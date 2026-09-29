from __future__ import annotations
from dataclasses import dataclass
import cv2
import numpy as np
from .research_config import ResearchConfig
from alpha_fix.samples import build_sample_mask, collect_sample_pixels

from .primitives import MattePrimitives, FrameResult
from .constellation import constellation_overlay_alpha

class ResearchProcessor(MattePrimitives):
    def process_frame(
        self,
        frame_bgr: np.ndarray,
        prev_alpha: np.ndarray | None = None,
    ) -> FrameResult:
        if self._border_palette is None:
            self._border_palette = self.fit_border_palette(frame_bgr)

        alpha0, confidence = self._build_anchor(frame_bgr)

        if self.config.mode == "overlay":
            if self.config.overlay_method in ("constellation", "bounded_geodesic"):
                alpha = self._apply_constellation(alpha0, frame_bgr, self.config)
            elif self.config.overlay_method == "auto_hole":
                alpha = self._apply_auto_hole(alpha0, frame_bgr, self.config)
            else:
                alpha = (
                    self._apply_chhc(alpha0, frame_bgr, self.config)
                    if self.config.chhc_enabled
                    else alpha0
                )
            if self.config.overlay_method != "bounded_geodesic":
                # Global overlay methods clean edge vignette/compression artifacts.
                # Bounded mode must leave every pixel outside jurisdiction untouched.
                margin = 8
                alpha[:margin, :] = 0.0
                alpha[-margin:, :] = 0.0
                alpha[:, :margin] = 0.0
                alpha[:, -margin:] = 0.0

            alpha_ema = alpha0.copy()
            signed_distance = self._signed_distance(alpha >= 0.5)
        else:
            if prev_alpha is None:
                alpha = alpha0.copy()
            else:
                alpha = (
                    self.config.ema_decay * prev_alpha
                    + (1.0 - self.config.ema_decay) * alpha0
                ).astype(np.float32)

            alpha_ema = alpha.copy()

            if getattr(self.config, 'sdr_enabled', False):
                alpha = self._apply_sdr_pow(alpha, self.config)

            if self.config.anchor_blur_sigma > 0:
                alpha = cv2.GaussianBlur(alpha, (0, 0), self.config.anchor_blur_sigma)

            signed_distance = self._signed_distance(alpha >= 0.5)
            if self.config.lipc_enabled:
                alpha = self._apply_lipc(
                    alpha,
                    alpha0,
                    frame_bgr,
                    signed_distance,
                    confidence,
                    self.config,
                )
            signed_distance = self._signed_distance(alpha >= 0.5)

        return FrameResult(
            alpha0=alpha0,
            alpha=alpha,
            alpha_ema=alpha_ema,
            confidence=confidence,
            signed_distance=signed_distance,
            rgba=self._rgba_from_alpha(frame_bgr, alpha),
            border_palette=self._border_palette,
        )


    def _apply_constellation(
        self,
        alpha0: np.ndarray,
        frame_bgr: np.ndarray,
        cfg: ResearchConfig,
    ) -> np.ndarray:
        bounded = cfg.overlay_method == "bounded_geodesic"
        if bounded:
            basin_mask = build_sample_mask(alpha0.shape, cfg.sample_regions, "basin")
            background_mask = build_sample_mask(alpha0.shape, cfg.sample_regions, "background")
            if not np.any(basin_mask > 0.5) or not np.any(background_mask > 0.5):
                return np.ones_like(alpha0, dtype=np.float32)

        result = constellation_overlay_alpha(frame_bgr, cfg.sample_regions, cfg)
        if result is None:
            if bounded:
                return np.ones_like(alpha0, dtype=np.float32)
            # Global constellation retains the historical hole-carver fallback.
            return self._apply_chhc(alpha0, frame_bgr, cfg)
        alpha = result if isinstance(result, np.ndarray) else result[0]
        keep_mask = self._overlay_keep_mask(alpha0.shape)
        if np.any(keep_mask > 0.0):
            alpha = np.maximum(alpha, keep_mask)
        return np.clip(alpha, 0.0, 1.0).astype(np.float32)
