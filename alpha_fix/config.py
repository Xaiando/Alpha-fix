from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from .samples import SampleRegion

Mode = Literal["subject", "overlay"]
OverlayMethod = Literal["auto_hole", "chhc"]
ExportFormat = Literal["png_sequence", "chroma_mp4", "webm_alpha", "prores_4444"]


@dataclass(slots=True)
class AlphaFixConfig:
    mode: Mode = "overlay"
    overlay_method: OverlayMethod = "auto_hole"

    border_width: int = 12
    border_clusters: int = 3
    border_sample_limit: int = 12000

    subject_low: float = 1.4
    subject_high: float = 4.5
    overlay_low: float = 0.3
    overlay_high: float = 2.3

    edge_boost: float = 0.18
    anchor_blur_sigma: float = 1.0
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
    chhc_feather_r: float = 2.5

    export_alpha_matte: bool = True
    export_format: ExportFormat = "prores_4444"
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

    def updated(self, **overrides: object) -> "AlphaFixConfig":
        return replace(self, **overrides)
