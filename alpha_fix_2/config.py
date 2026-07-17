from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from alpha_fix.samples import SampleRegion

Mode = Literal["subject", "overlay"]
OverlayMethod = Literal["chhc", "auto_hole", "radfield", "chroma", "checkerboard"]


@dataclass(slots=True)
class AlphaFix2Config:
    mode: Mode = "overlay"
    overlay_method: OverlayMethod = "auto_hole"

    chroma_target_a: float = 69.0
    chroma_target_b: float = 185.0
    chroma_low: float = 55.0
    chroma_high: float = 82.0
    chroma_portal_x_min: float = 0.22
    chroma_portal_x_max: float = 0.78
    chroma_portal_y_min: float = 0.15
    chroma_portal_y_max: float = 0.88

    checkerboard_low: float = 15.0
    checkerboard_high: float = 25.0
    checkerboard_size: int = 0
    checkerboard_offset_x: int = -1
    checkerboard_offset_y: int = -1

    border_width: int = 12
    border_clusters: int = 3
    border_sample_limit: int = 12000

    subject_low: float = 0.8
    subject_high: float = 2.5
    overlay_low: float = 0.3
    overlay_high: float = 2.3

    edge_boost: float = 0.12
    anchor_blur_sigma: float = 1.0
    anchor_blend: float = 0.0
    ema_decay: float = 0.65
    confidence_floor: float = 0.15
    alpha_floor: float = 0.35

    lipc_enabled: bool = True
    lipc_alpha_min: float = 0.02
    lipc_t_delta: float = 0.35
    lipc_t_luma: float = 0.80
    lipc_sigma_d: float = 2.5
    lipc_lambda: float = 0.65
    lipc_band_radius: int = 6

    chhc_enabled: bool = True
    chhc_t_alpha: float = 0.12
    chhc_close_kernel: int = 5
    chhc_min_hole_frac: float = 0.03
    chhc_valid_margin: float = 0.05
    chhc_feather_r: float = 4.0

    export_alpha_matte: bool = True
    sample_regions: tuple[SampleRegion, ...] = ()

    sdr_enabled: bool = False
    sdr_pivot: float = 0.50
    sdr_k: float = 0.6
    sdr_sigma: float = 1.5

    hole_dark_max: float = 0.18
    hole_flat_max: float = 0.035
    hole_min_area_frac: float = 0.01
    hole_seed_min_dist: float = 8.0
    hole_flood_tol: int = 18
    hole_margin_frac: float = 0.05

    srf_sigma_d: float = 2000.0
    srf_sigma_c: float = 18.0
    srf_gamma: float = 2.2
    srf_tau_delta: float = 12.0
    srf_lambda_t: float = 0.30
    srf_edge_boost: float = 0.15

    osa_enabled: bool = False
    osa_mode: Literal["HTP", "lite"] = "HTP"
    osa_pivot: float = 0.50
    osa_kappa: float = 2.5
    osa_R: float = 2.5
    osa_sigma: float = 2.0
    osa_omega: float = 4.0
    osa_lam: float = 5.0

    despill_enabled: bool = True
    despill_target: Literal["auto", "green", "blue", "none"] = "auto"
    despill_strength: float = 1.0
    despill_threshold: float = 1.0

    def updated(self, **overrides: object) -> "AlphaFix2Config":
        return replace(self, **overrides)
