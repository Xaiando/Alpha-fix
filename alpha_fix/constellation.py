"""Constellation Seeding + barrier-aware geodesic flood (sandbox / experimental).

This is the experimental overlay method that pairs two ideas:

* a *scout* that may teleport globally to drop background seed dots wherever the
  sampled background family reappears (solves the "more than two disconnected
  background basins" problem), and
* a *flood* that may not teleport at all: each seed radiates outward along a
  geodesic cost field and stops when it hits a structural wall.

"The scout may teleport. The colonies must walk."

Signals used in this first pass:

* diagonal Mahalanobis colour distance to the operator-sampled background family
  (mean + per-channel variance in a rescaled, perceptual-ish Lab space). Colour
  acts as a *gate*, not a travel cost: pixels far from the family become walls
  the flood cannot enter. Making colour a per-step cost (an earlier mistake)
  penalizes travel through perfectly good background in proportion to distance.
* an L-channel gradient barrier that makes real edges expensive to cross, so the
  flood slows at silhouettes even between same-colour regions.

Thresholds are expressed *relative to the sampled family's own spread* (the 90th
percentile Mahalanobis sigma over the operator pixels), so they transfer across
images/noise levels instead of depending on an absolute sigma guess.

Entropy / superpixel / temporal passes are deliberately left out of this MVP;
entropy slots in as an extra gate/barrier term, temporal as a seed filter, and
neither changes the flood.

Dependency-free by design: the geodesic flood is an exact multi-source Dijkstra
over a downscaled frame (``const_work_res``). scikit-image's ``MCP_Geometric``
is the drop-in production upgrade once we outgrow the pure-Python flood.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2
import numpy as np

from .samples import SampleRegion, build_sample_mask, collect_sample_pixels

if TYPE_CHECKING:  # avoid a runtime import cycle with config.py
    from .config import AlphaFixConfig

_VAR_FLOOR = 4.0  # min per-channel Lab variance (rescaled units) to keep Mahalanobis stable
_MIN_BG_PIXELS = 24


@dataclass(slots=True)
class ConstellationDebug:
    """Inspectable intermediate fields (work resolution unless noted)."""

    operator_seeds: np.ndarray  # bool: seeds from operator background circles
    scout_seeds: np.ndarray     # bool: seeds the scout teleported in
    color_rel: np.ndarray       # float: Mahalanobis sigma / family spread (1.0 == typical bg)
    barrier: np.ndarray         # float: normalized L-gradient barrier
    off_family: np.ndarray      # bool: colour-gated walls
    geodesic: np.ndarray        # float: arrival cost D from the seed set (inf = unreachable)
    membership: np.ndarray      # float (full res): background membership in [0, 1]


def _to_lab(frame_bgr: np.ndarray) -> np.ndarray:
    """OpenCV 8-bit Lab -> rescaled, roughly perceptual Lab.

    OpenCV packs 8-bit Lab as L in [0, 255] and a/b in [0, 255] centred on 128.
    Left raw, the L channel would dominate every distance. Rescale to
    L* in [0, 100] and a*/b* in [-128, 127] so the Mahalanobis metric is honest.
    """
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= 100.0 / 255.0
    lab[..., 1] -= 128.0
    lab[..., 2] -= 128.0
    return lab


def _smoothstep(lo: float, hi: float, x: np.ndarray) -> np.ndarray:
    if hi <= lo:
        return (x >= hi).astype(np.float32)
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


def _geodesic_distance(cost: np.ndarray, seeds: np.ndarray) -> np.ndarray:
    """Exact multi-source geodesic distance via Dijkstra (4-connectivity).

    ``cost[q]`` is the cost of *entering* pixel ``q`` (np.inf = impassable).
    Seeds start at distance 0. Returns an ``(h, w)`` float64 arrival-cost map;
    unreachable pixels stay ``inf``.
    """
    h, w = cost.shape
    cost_flat = cost.reshape(-1)
    dist = np.full(h * w, np.inf, dtype=np.float64)

    heap: list[tuple[float, int]] = []
    for idx in np.flatnonzero(seeds.reshape(-1)):
        i = int(idx)
        dist[i] = 0.0
        heap.append((0.0, i))
    heapq.heapify(heap)

    while heap:
        d, i = heapq.heappop(heap)
        if d > dist[i]:
            continue
        r, c = divmod(i, w)
        if r > 0:
            j = i - w
            nd = d + cost_flat[j]
            if nd < dist[j]:
                dist[j] = nd
                heapq.heappush(heap, (nd, j))
        if r < h - 1:
            j = i + w
            nd = d + cost_flat[j]
            if nd < dist[j]:
                dist[j] = nd
                heapq.heappush(heap, (nd, j))
        if c > 0:
            j = i - 1
            nd = d + cost_flat[j]
            if nd < dist[j]:
                dist[j] = nd
                heapq.heappush(heap, (nd, j))
        if c < w - 1:
            j = i + 1
            nd = d + cost_flat[j]
            if nd < dist[j]:
                dist[j] = nd
                heapq.heappush(heap, (nd, j))

    return dist.reshape(h, w)


def _scout_seeds(
    color_rel: np.ndarray,
    barrier: np.ndarray,
    forbidden: np.ndarray,
    cfg: "AlphaFixConfig",
) -> np.ndarray:
    """Teleport a sparse background seed dot into every disconnected basin
    whose colour matches the sampled family and whose interior is smooth.

    One representative dot per qualifying connected component, so the flood
    (not the scout) decides how far each colony's jurisdiction extends.
    """
    h, w = color_rel.shape
    seeds = np.zeros((h, w), dtype=bool)
    if not getattr(cfg, "const_scout_enabled", True):
        return seeds

    candidate = (
        (color_rel < cfg.const_seed_color_tol)
        & (barrier < cfg.const_seed_grad_max)
        & (~forbidden)
    ).astype(np.uint8)
    # Erode away thin bridges so unrelated basins don't merge into one component.
    candidate = cv2.erode(candidate, np.ones((3, 3), np.uint8))
    if not candidate.any():
        return seeds

    count, labels = cv2.connectedComponents(candidate)
    min_area = max(1.0, cfg.const_seed_min_area_frac * h * w)
    for lbl in range(1, count):
        comp = labels == lbl
        if int(comp.sum()) < min_area:
            continue
        # Representative dot = most background-like pixel in the component.
        masked = np.where(comp, color_rel, np.inf)
        ry, rx = np.unravel_index(int(np.argmin(masked)), masked.shape)
        y0, y1 = max(0, ry - 1), min(h, ry + 2)
        x0, x1 = max(0, rx - 1), min(w, rx + 2)
        seeds[y0:y1, x0:x1] = True
    return seeds


def constellation_overlay_alpha(
    frame_bgr: np.ndarray,
    sample_regions: tuple[SampleRegion, ...],
    cfg: "AlphaFixConfig",
    *,
    return_debug: bool = False,
) -> np.ndarray | tuple[np.ndarray, ConstellationDebug] | None:
    """Return an overlay alpha (background -> 0, foreground -> 1), or ``None``
    when there is no usable background model (caller should fall back).
    """
    regions = tuple(sample_regions)
    height, width = frame_bgr.shape[:2]

    scale = min(1.0, cfg.const_work_res / float(max(height, width)))
    if scale < 1.0:
        work = cv2.resize(
            frame_bgr,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    else:
        work = frame_bgr
    h, w = work.shape[:2]

    lab = _to_lab(work)

    # --- Background colour family (diagonal Mahalanobis) -----------------
    bg_pixels = collect_sample_pixels(lab, regions, "background")
    if len(bg_pixels) < _MIN_BG_PIXELS:
        return None
    mean = bg_pixels.mean(axis=0)
    var = np.maximum(bg_pixels.var(axis=0), _VAR_FLOOR)
    d2 = (((lab - mean) ** 2) / var).sum(axis=-1)
    color_sigma = np.sqrt(np.maximum(d2, 0.0)).astype(np.float32)

    # Calibrate to the sampled family's own spread so thresholds transfer.
    operator_bg = build_sample_mask((h, w), regions, "background") > 0.5
    ref = color_sigma[operator_bg]
    spread = float(np.percentile(ref, 90)) if ref.size else 1.0
    color_rel = color_sigma / max(spread, 1e-3)

    # --- Barrier (L-gradient), normalized by its own 95th percentile -----
    # Denoise first and subtract a floor so *flat* regions read ~0: any nonzero
    # per-step cost would otherwise accumulate over distance and strand the far
    # side of a large basin as "foreground".
    lightness = cv2.GaussianBlur(lab[..., 0], (0, 0), 1.0)
    gx = cv2.Scharr(lightness, cv2.CV_32F, 1, 0)
    gy = cv2.Scharr(lightness, cv2.CV_32F, 0, 1)
    grad = np.sqrt(gx * gx + gy * gy)
    p95 = float(np.percentile(grad, 95)) + 1e-6
    barrier = np.clip(grad / p95 - cfg.const_barrier_floor, 0.0, 4.0).astype(np.float32)

    keep = build_sample_mask((h, w), regions, "keep") > 0.5
    off_family = color_rel >= cfg.const_color_gate  # rejected family -> walls
    forbidden = keep | off_family

    # --- Seeds: operator circles + scouted constellation dots ------------
    # The scout only founds colonies in *trusted* basins (const_seed_color_tol
    # sits at the trust ceiling), so fog/smudge is reached by walking, not seeded.
    operator_seeds = operator_bg & ~forbidden
    scout_seeds = _scout_seeds(color_rel, barrier, forbidden, cfg)
    seeds = operator_seeds | scout_seeds
    if not seeds.any():
        return None

    # --- Flood: colonies walk the geodesic cost field --------------------
    # Travel cost has three parts, all zero inside uniform terrain so distance
    # is never charged on its own (the bug the synthetic caught):
    #   * structural edge barrier (L gradient)  -> silhouettes / rails
    #   * colour *transition* barrier            -> charged where family
    #     membership CHANGES, so a large uniform fog basin is paid for once at
    #     its edge, not by its depth ("count transitions, not pixels")
    #   * optional per-step uncertain-terrain toll (Sol's swamp; off by default)
    # The rejected band (colour_rel >= gate) is an absolute wall regardless.
    cr = cv2.GaussianBlur(np.minimum(color_rel, cfg.const_color_gate), (0, 0), 1.0)
    cgx = cv2.Scharr(cr, cv2.CV_32F, 1, 0)
    cgy = cv2.Scharr(cr, cv2.CV_32F, 0, 1)
    cgrad = np.sqrt(cgx * cgx + cgy * cgy)
    cg95 = float(np.percentile(cgrad, 95)) + 1e-6
    color_transition = np.clip(cgrad / cg95 - cfg.const_barrier_floor, 0.0, 4.0).astype(np.float32)

    band = max(cfg.const_color_gate - cfg.const_color_trust, 1e-6)
    swamp = np.clip((color_rel - cfg.const_color_trust) / band, 0.0, 1.0).astype(np.float32)

    cost = (
        float(cfg.const_base_cost)
        + float(cfg.const_grad_weight) * barrier
        + float(cfg.const_color_weight) * color_transition
        + float(cfg.const_uncertainty_weight) * swamp
    ).astype(np.float64)
    cost[forbidden] = np.inf
    geodesic = _geodesic_distance(cost, seeds)

    membership = 1.0 - _smoothstep(cfg.const_tau_lo, cfg.const_tau_hi, geodesic)
    membership[np.isinf(geodesic)] = 0.0
    membership[keep] = 0.0

    membership_full = cv2.resize(
        membership.astype(np.float32), (width, height), interpolation=cv2.INTER_LINEAR
    )

    if cfg.const_edge_snap and scale < 1.0:
        # The flood decides connectivity at low resolution; snap the *boundary* to
        # the full-res colour gate. A pixel is background only if the flood reached
        # its neighbourhood AND it is on-family at full resolution. This re-sharpens
        # colour edges and re-protects thin off-family structures (icicles, chains)
        # that vanished under the downscale and got eroded by the flood.
        lab_full = _to_lab(frame_bgr)
        d2_full = (((lab_full - mean) ** 2) / var).sum(axis=-1)
        color_rel_full = np.sqrt(np.maximum(d2_full, 0.0)) / max(spread, 1e-3)
        on_family_full = (color_rel_full < cfg.const_color_gate).astype(np.float32)
        membership_full *= on_family_full
        keep_full = build_sample_mask((height, width), regions, "keep") > 0.5
        membership_full[keep_full] = 0.0

    if cfg.const_feather_px > 0:
        membership_full = cv2.GaussianBlur(membership_full, (0, 0), cfg.const_feather_px)
    membership_full = np.clip(membership_full, 0.0, 1.0)

    alpha = (1.0 - membership_full).astype(np.float32)  # background transparent

    if return_debug:
        debug = ConstellationDebug(
            operator_seeds=operator_seeds,
            scout_seeds=scout_seeds,
            color_rel=color_rel,
            barrier=barrier,
            off_family=off_family,
            geodesic=geodesic,
            membership=membership_full,
        )
        return alpha, debug
    return alpha
