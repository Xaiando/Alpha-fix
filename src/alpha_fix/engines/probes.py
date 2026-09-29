from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(slots=True, frozen=True)
class BoundedProbeAlpha:
    """One fail-closed alpha proposal and the operator authority that bounds it."""

    alpha: np.ndarray
    jurisdiction: np.ndarray
    keep: np.ndarray


def compose_bounded_probes(
    base_alpha: np.ndarray,
    probes: Iterable[BoundedProbeAlpha],
) -> np.ndarray:
    """Compose independent removal probes without expanding their authority.

    The composition is a meet (pixelwise minimum) inside the union of probe
    jurisdictions. The union of every authored keep mask is a veto that restores
    the incoming baseline. Consequently, probes are monotone-removing, commute,
    are idempotent, and cannot change pixels outside their jurisdictions.
    """

    base = np.asarray(base_alpha, dtype=np.float32)
    if base.ndim != 2:
        raise ValueError("base_alpha must be a 2D array")

    layers = tuple(probes)
    for layer in layers:
        if layer.alpha.shape != base.shape:
            raise ValueError("probe alpha shape must match base_alpha")
        if layer.jurisdiction.shape != base.shape:
            raise ValueError("probe jurisdiction shape must match base_alpha")
        if layer.keep.shape != base.shape:
            raise ValueError("probe keep shape must match base_alpha")

    output = np.clip(base, 0.0, 1.0).copy()
    keep_union = np.zeros(base.shape, dtype=bool)
    for layer in layers:
        keep_union |= np.asarray(layer.keep, dtype=bool)

    for layer in layers:
        active = np.asarray(layer.jurisdiction, dtype=bool) & ~keep_union
        proposal = np.clip(np.asarray(layer.alpha, dtype=np.float32), 0.0, 1.0)
        output[active] = np.minimum(output[active], proposal[active])

    output[keep_union] = np.clip(base[keep_union], 0.0, 1.0)
    return output.astype(np.float32)
