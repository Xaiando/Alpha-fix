from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .config import AlphaFixConfig
from .constellation import constellation_overlay_alpha
from .samples import build_sample_mask, collect_sample_pixels


@dataclass(slots=True)
class BorderPalette:
    centers: np.ndarray
    variances: np.ndarray


@dataclass(slots=True)
class FrameResult:
    alpha0: np.ndarray
    alpha: np.ndarray
    alpha_ema: np.ndarray
    confidence: np.ndarray
    signed_distance: np.ndarray
    rgba: np.ndarray
    border_palette: BorderPalette


class AlphaFixProcessor:
    def __init__(self, config: AlphaFixConfig) -> None:
        self.config = config
        self._border_palette: BorderPalette | None = None

    def reset(self) -> None:
        self._border_palette = None

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
            # Force outer 8 pixels to be transparent to clean up edge vignette/compression artifacts
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

    def fit_border_palette(self, frame_bgr: np.ndarray) -> BorderPalette:
        frame_lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        border_pixels = self._sample_border_pixels(frame_lab)
        guided_pixels = collect_sample_pixels(
            frame_lab,
            self.config.sample_regions,
            "background",
        )
        if len(guided_pixels) > 0:
            border_pixels = np.concatenate(
                [
                    border_pixels,
                    guided_pixels,
                    guided_pixels,
                ],
                axis=0,
            ).astype(np.float32)

        if len(border_pixels) == 0:
            center = frame_lab.reshape(-1, 3).mean(axis=0, keepdims=True)
            variance = np.full((1, 3), 64.0, dtype=np.float32)
            return BorderPalette(center.astype(np.float32), variance)

        sample_limit = min(self.config.border_sample_limit, len(border_pixels))
        if sample_limit < len(border_pixels):
            positions = np.linspace(0, len(border_pixels) - 1, sample_limit, dtype=np.int32)
            border_pixels = border_pixels[positions]

        cluster_count = max(1, min(self.config.border_clusters, len(border_pixels)))
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            25,
            0.2,
        )
        _compactness, labels, centers = cv2.kmeans(
            border_pixels,
            cluster_count,
            None,
            criteria,
            4,
            cv2.KMEANS_PP_CENTERS,
        )

        variances: list[np.ndarray] = []
        label_values = labels.ravel()
        for idx in range(cluster_count):
            members = border_pixels[label_values == idx]
            if len(members) == 0:
                variances.append(np.full(3, 64.0, dtype=np.float32))
                continue
            variances.append(np.var(members, axis=0).astype(np.float32) + 25.0)

        return BorderPalette(
            centers=centers.astype(np.float32),
            variances=np.stack(variances).astype(np.float32),
        )

    def _build_anchor(self, frame_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        distance = self._border_distance(frame_bgr)
        edge_strength = self._edge_strength(frame_bgr)

        if self.config.mode == "overlay":
            alpha0 = 1.0 - self._smoothstep(
                distance,
                self.config.overlay_low,
                self.config.overlay_high,
            )
        else:
            alpha0 = self._smoothstep(
                distance,
                self.config.subject_low,
                self.config.subject_high,
            )
            alpha0 = np.clip(
                alpha0 + edge_strength * self.config.edge_boost * (1.0 - alpha0),
                0.0,
                1.0,
            )

        if self.config.anchor_blur_sigma > 0:
            alpha0 = cv2.GaussianBlur(alpha0, (0, 0), self.config.anchor_blur_sigma)

        background_mask = build_sample_mask(
            alpha0.shape,
            self.config.sample_regions,
            "background",
        )
        keep_mask = build_sample_mask(
            alpha0.shape,
            self.config.sample_regions,
            "keep",
        )
        if np.any(background_mask > 0.0):
            alpha0 = alpha0 * (1.0 - background_mask)
        if np.any(keep_mask > 0.0):
            alpha0 = np.maximum(alpha0, keep_mask)

        confidence = np.clip(np.abs(alpha0 - 0.5) * 2.0, self.config.confidence_floor, 1.0)
        if np.any(background_mask > 0.0):
            confidence = np.maximum(confidence, background_mask)
        if np.any(keep_mask > 0.0):
            confidence = np.maximum(confidence, keep_mask)
        return alpha0.astype(np.float32), confidence.astype(np.float32)

    def _overlay_keep_mask(self, image_shape: tuple[int, int]) -> np.ndarray:
        keep_mask = build_sample_mask(
            image_shape,
            self.config.sample_regions,
            "keep",
        )
        return keep_mask > 0.15

    def _border_distance(self, frame_bgr: np.ndarray) -> np.ndarray:
        if self._border_palette is None:
            raise RuntimeError("Border palette must be fitted before computing distance.")

        frame_lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        diff = frame_lab[:, :, None, :] - self._border_palette.centers[None, None, :, :]
        scaled = (diff * diff) / self._border_palette.variances[None, None, :, :]
        distance = np.sqrt(np.min(np.sum(scaled, axis=-1), axis=-1))
        return distance.astype(np.float32)

    def _sample_border_pixels(self, image_lab: np.ndarray) -> np.ndarray:
        width = max(1, min(self.config.border_width, min(image_lab.shape[0], image_lab.shape[1]) // 3))
        top = image_lab[:width, :, :]
        bottom = image_lab[-width:, :, :]
        left = image_lab[:, :width, :]
        right = image_lab[:, -width:, :]
        return np.concatenate(
            [
                top.reshape(-1, 3),
                bottom.reshape(-1, 3),
                left.reshape(-1, 3),
                right.reshape(-1, 3),
            ],
            axis=0,
        ).astype(np.float32)

    def _edge_strength(self, frame_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        lap = np.abs(cv2.Laplacian(gray, cv2.CV_32F))
        lap = cv2.GaussianBlur(lap, (0, 0), 1.0)
        scale = float(np.percentile(lap, 95)) + 1e-6
        return np.clip(lap / scale, 0.0, 1.0).astype(np.float32)

    @staticmethod
    def _smoothstep(values: np.ndarray, low: float, high: float) -> np.ndarray:
        if high <= low:
            return (values >= high).astype(np.float32)
        t = np.clip((values - low) / (high - low), 0.0, 1.0)
        return (t * t * (3.0 - 2.0 * t)).astype(np.float32)

    @staticmethod
    def _signed_distance(mask: np.ndarray) -> np.ndarray:
        mask_u8 = mask.astype(np.uint8)
        inside = cv2.distanceTransform(mask_u8, cv2.DIST_L2, 3)
        outside = cv2.distanceTransform(1 - mask_u8, cv2.DIST_L2, 3)
        return (outside - inside).astype(np.float32)

    def _median_border_rgb(self, frame_rgb: np.ndarray) -> np.ndarray:
        width = max(1, min(self.config.border_width, min(frame_rgb.shape[0], frame_rgb.shape[1]) // 3))
        top = frame_rgb[:width, :, :]
        bottom = frame_rgb[-width:, :, :]
        left = frame_rgb[:, :width, :]
        right = frame_rgb[:, -width:, :]
        border = np.concatenate(
            [
                top.reshape(-1, 3),
                bottom.reshape(-1, 3),
                left.reshape(-1, 3),
                right.reshape(-1, 3),
            ],
            axis=0,
        )
        return np.median(border, axis=0).astype(np.float32)

    def _apply_lipc(
        self,
        alpha: np.ndarray,
        alpha0: np.ndarray,
        frame_bgr: np.ndarray,
        phi: np.ndarray,
        conf: np.ndarray,
        cfg: AlphaFixConfig,
    ) -> np.ndarray:
        frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        bg_mask = alpha0 < 0.05

        if int(np.count_nonzero(bg_mask)) > 100:
            bg = np.median(frame[bg_mask], axis=0).astype(np.float32)
        else:
            bg = self._median_border_rgb(frame)

        ext = (phi > 0.0) & (phi <= float(cfg.lipc_band_radius))
        active = ext & (alpha > cfg.lipc_alpha_min)
        if not np.any(active):
            return np.clip(alpha, 0.0, 1.0)

        a_safe = np.maximum(alpha, cfg.lipc_alpha_min)
        f_hat = (frame - (1.0 - a_safe)[..., None] * bg[None, None, :]) / a_safe[..., None]
        f_hat = np.clip(f_hat, 0.0, 2.0)

        y_f = 0.2126 * f_hat[..., 0] + 0.7152 * f_hat[..., 1] + 0.0722 * f_hat[..., 2]
        delta_f = np.linalg.norm(f_hat - bg[None, None, :], axis=-1)

        h_color = np.clip((cfg.lipc_t_delta - delta_f) / max(cfg.lipc_t_delta, 1e-6), 0.0, 1.0)
        h_luma = np.clip((y_f - cfg.lipc_t_luma) / max(1.0 - cfg.lipc_t_luma, 1e-6), 0.0, 1.0)
        halo = h_color * h_luma

        weight = np.exp(-0.5 * (phi / max(cfg.lipc_sigma_d, 1e-6)) ** 2)
        reduction = cfg.lipc_lambda * halo * weight * conf

        alpha_new = alpha.copy()
        alpha_new[active] *= 1.0 - np.clip(reduction[active], 0.0, 1.0)
        alpha_new = np.maximum(alpha_new, cfg.alpha_floor * alpha0)
        return np.clip(alpha_new, 0.0, 1.0).astype(np.float32)

    def _apply_chhc(
        self,
        alpha0: np.ndarray,
        frame_bgr: np.ndarray,
        cfg: AlphaFixConfig,
    ) -> np.ndarray:
        del frame_bgr
        height, width = alpha0.shape

        raw = (alpha0 > cfg.chhc_t_alpha).astype(np.uint8) * 255
        kernel_size = max(3, int(cfg.chhc_close_kernel) | 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        closed = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, kernel)

        contours, hierarchy = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None or len(contours) == 0:
            return alpha0.astype(np.float32)

        hierarchy = hierarchy[0]
        frame_area = float(height * width)
        frame_idx = -1
        max_area = 0.0
        for idx, rel in enumerate(hierarchy):
            if rel[3] == -1:
                area = float(cv2.contourArea(contours[idx]))
                if area > max_area:
                    max_area = area
                    frame_idx = idx

        if frame_idx == -1:
            return alpha0.astype(np.float32)

        frame_fill = np.zeros((height, width), dtype=np.uint8)
        cv2.drawContours(frame_fill, contours, frame_idx, 255, cv2.FILLED)

        holes: list[int] = []
        min_area = cfg.chhc_min_hole_frac * frame_area
        margin_x = cfg.chhc_valid_margin * width
        margin_y = cfg.chhc_valid_margin * height

        for idx, rel in enumerate(hierarchy):
            if rel[3] != frame_idx:
                continue
            area = float(cv2.contourArea(contours[idx]))
            if area < min_area:
                continue
            moments = cv2.moments(contours[idx])
            if moments["m00"] < 1.0:
                continue
            cx = moments["m10"] / moments["m00"]
            cy = moments["m01"] / moments["m00"]
            if margin_x < cx < (width - margin_x) and margin_y < cy < (height - margin_y):
                holes.append(idx)

        hole_mask = np.zeros((height, width), dtype=np.uint8)
        for idx in holes:
            cv2.drawContours(hole_mask, contours, idx, 255, cv2.FILLED)

        frame_mask = (frame_fill > 0) & (hole_mask == 0)
        keep_mask = self._overlay_keep_mask(alpha0.shape)
        if np.any(keep_mask):
            frame_mask = frame_mask | (keep_mask & (frame_fill > 0))
        dist_inside = cv2.distanceTransform(frame_mask.astype(np.uint8) * 255, cv2.DIST_L2, 3)

        alpha_overlay = np.zeros((height, width), dtype=np.float32)
        alpha_overlay[dist_inside > cfg.chhc_feather_r] = 1.0
        feather_zone = (dist_inside > 0) & (dist_inside <= cfg.chhc_feather_r)
        alpha_overlay[feather_zone] = dist_inside[feather_zone] / max(cfg.chhc_feather_r, 1e-6)
        return np.clip(alpha_overlay, 0.0, 1.0).astype(np.float32)

    def _apply_constellation(
        self,
        alpha0: np.ndarray,
        frame_bgr: np.ndarray,
        cfg: AlphaFixConfig,
    ) -> np.ndarray:
        result = constellation_overlay_alpha(frame_bgr, cfg.sample_regions, cfg)
        if result is None:
            # No usable background family sampled -> fall back to the hole carver.
            return self._apply_chhc(alpha0, frame_bgr, cfg)
        alpha = result if isinstance(result, np.ndarray) else result[0]
        keep_mask = self._overlay_keep_mask(alpha0.shape)
        if np.any(keep_mask > 0.0):
            alpha = np.maximum(alpha, keep_mask)
        return np.clip(alpha, 0.0, 1.0).astype(np.float32)

    def _apply_auto_hole(
        self,
        alpha0: np.ndarray,
        frame_bgr: np.ndarray,
        cfg: AlphaFixConfig,
    ) -> np.ndarray:
        frame_fill = self._extract_outer_frame_mask(alpha0, cfg)
        if not np.any(frame_fill):
            return self._apply_chhc(alpha0, frame_bgr, cfg)

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        lap = np.abs(cv2.Laplacian(gray, cv2.CV_32F))
        lap = cv2.GaussianBlur(lap, (0, 0), 1.0)
        scale = float(np.percentile(lap, 95)) + 1e-6
        texture = np.clip(lap / scale, 0.0, 1.0)

        void_mask = (
            frame_fill
            & (gray <= cfg.hole_dark_max)
            & (texture <= cfg.hole_flat_max)
        )
        seeds = self._select_hole_seeds(void_mask, frame_fill, cfg)
        if not seeds:
            return self._apply_chhc(alpha0, frame_bgr, cfg)

        hole_mask = self._grow_holes(gray, void_mask, seeds, cfg)
        if not np.any(hole_mask):
            return self._apply_chhc(alpha0, frame_bgr, cfg)

        solid_mask = frame_fill & ~hole_mask
        keep_mask = self._overlay_keep_mask(alpha0.shape)
        if np.any(keep_mask):
            solid_mask = solid_mask | (keep_mask & frame_fill)
        return self._feather_binary_mask(solid_mask, cfg.chhc_feather_r)

    def _extract_outer_frame_mask(
        self,
        alpha0: np.ndarray,
        cfg: AlphaFixConfig,
    ) -> np.ndarray:
        height, width = alpha0.shape
        raw = (alpha0 > cfg.chhc_t_alpha).astype(np.uint8) * 255
        kernel_size = max(3, int(cfg.chhc_close_kernel) | 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        closed = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, kernel)

        contours, hierarchy = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None or len(contours) == 0:
            return np.zeros((height, width), dtype=bool)

        hierarchy = hierarchy[0]
        frame_idx = -1
        max_area = 0.0
        for idx, rel in enumerate(hierarchy):
            if rel[3] != -1:
                continue
            area = float(cv2.contourArea(contours[idx]))
            if area > max_area:
                max_area = area
                frame_idx = idx

        if frame_idx == -1:
            return np.zeros((height, width), dtype=bool)

        frame_fill = np.zeros((height, width), dtype=np.uint8)
        cv2.drawContours(frame_fill, contours, frame_idx, 255, cv2.FILLED)
        return frame_fill > 0

    def _select_hole_seeds(
        self,
        void_mask: np.ndarray,
        frame_fill: np.ndarray,
        cfg: AlphaFixConfig,
    ) -> list[tuple[int, int]]:
        height, width = void_mask.shape
        void_u8 = void_mask.astype(np.uint8)
        component_count, labels, stats, centroids = cv2.connectedComponentsWithStats(void_u8, 8)
        min_area = cfg.hole_min_area_frac * float(height * width)
        margin_x = cfg.hole_margin_frac * width
        margin_y = cfg.hole_margin_frac * height
        safe_mask = np.zeros((height, width), dtype=bool)
        y0 = int(max(0, margin_y))
        y1 = int(min(height, height - margin_y))
        x0 = int(max(0, margin_x))
        x1 = int(min(width, width - margin_x))
        safe_mask[y0:y1, x0:x1] = True

        cx, cy = width / 2.0, height / 2.0
        max_dist = max(np.sqrt(cx**2 + cy**2), 1e-6)

        candidates: list[tuple[float, int, int]] = []
        for idx in range(1, component_count):
            area = float(stats[idx, cv2.CC_STAT_AREA])
            if area < min_area:
                continue

            component_mask = labels == idx
            candidate_mask = component_mask & safe_mask
            if not np.any(candidate_mask):
                continue
            distance = cv2.distanceTransform(candidate_mask.astype(np.uint8), cv2.DIST_L2, 5)
            y, x = np.unravel_index(int(np.argmax(distance)), distance.shape)
            if float(distance[y, x]) < cfg.hole_seed_min_dist:
                continue
            if not frame_fill[y, x]:
                continue

            w_bbox = float(stats[idx, cv2.CC_STAT_WIDTH])
            h_bbox = float(stats[idx, cv2.CC_STAT_HEIGHT])
            rect_score = area / max(w_bbox * h_bbox, 1.0)

            centroid_x, centroid_y = centroids[idx]
            dist_to_center = np.sqrt((centroid_x - cx) ** 2 + (centroid_y - cy) ** 2)
            centrality = max(0.0, 1.0 - (dist_to_center / max_dist))
            score = rect_score * (centrality ** 0.5)
            if score < 0.2:
                continue

            candidates.append((score, int(x), int(y)))

        candidates.sort(key=lambda item: item[0], reverse=True)
        return [(x, y) for _score, x, y in candidates[:2]]

    @staticmethod
    def _grow_holes(
        gray: np.ndarray,
        frame_fill: np.ndarray,
        seeds: list[tuple[int, int]],
        cfg: AlphaFixConfig,
    ) -> np.ndarray:
        height, width = gray.shape
        gray_u8 = np.clip(gray * 255.0, 0.0, 255.0).astype(np.uint8)
        mask = np.ones((height + 2, width + 2), dtype=np.uint8)
        mask[1 : height + 1, 1 : width + 1] = (~frame_fill).astype(np.uint8)
        fill_value = 255

        for seed in seeds:
            cv2.floodFill(
                gray_u8,
                mask,
                seed,
                0,
                loDiff=int(cfg.hole_flood_tol),
                upDiff=int(cfg.hole_flood_tol),
                flags=cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (fill_value << 8),
            )

        return mask[1:-1, 1:-1] == fill_value

    @staticmethod
    def _feather_binary_mask(mask: np.ndarray, feather_radius: float) -> np.ndarray:
        dist_inside = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 3)
        alpha = np.zeros(mask.shape, dtype=np.float32)
        alpha[dist_inside > feather_radius] = 1.0
        feather_zone = (dist_inside > 0) & (dist_inside <= feather_radius)
        alpha[feather_zone] = dist_inside[feather_zone] / max(feather_radius, 1e-6)
        return np.clip(alpha, 0.0, 1.0).astype(np.float32)

    def _rgba_from_alpha(self, frame_bgr: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        solid_fg_mask = (alpha > 0.90).astype(np.float32)
        edge_mask = (alpha > 0.0) & (alpha <= 0.90)
        
        if self.config.mode == "subject" and np.any(edge_mask) and np.any(solid_fg_mask):
            fg_rgb = rgb.astype(np.float32) * solid_fg_mask[:, :, None]
            
            blur_size = (31, 31)
            blurred_rgb = cv2.GaussianBlur(fg_rgb, blur_size, 0)
            blurred_mask = cv2.GaussianBlur(solid_fg_mask, blur_size, 0)
            
            bled_rgb = blurred_rgb / np.maximum(blurred_mask[:, :, None], 1e-6)
            bled_rgb = np.clip(bled_rgb, 0.0, 255.0).astype(np.uint8)
            
            valid_bleed = blurred_mask > 0.01
            replace_mask = edge_mask & valid_bleed
            
            rgb[replace_mask] = bled_rgb[replace_mask]

        alpha_u8 = np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8)
        return np.dstack([rgb, alpha_u8])

    def _apply_sdr_pow(self, alpha_ema: np.ndarray, cfg: AlphaFixConfig) -> np.ndarray:
        m_fg = (alpha_ema >= cfg.sdr_pivot).astype(np.uint8)
        d_in = cv2.distanceTransform(m_fg, cv2.DIST_L2, 3)
        d_out = cv2.distanceTransform(1 - m_fg, cv2.DIST_L2, 3)
        S = d_out - d_in  # Repo convention: S > 0 is OUTSIDE
        
        power_mod = cfg.sdr_k * S * np.exp(-(S**2) / (2.0 * max(cfg.sdr_sigma, 1e-6)**2))
        gamma = np.exp(power_mod)
        
        alpha_safe = np.clip(alpha_ema, 1e-6, 1.0)
        alpha_new = np.power(alpha_safe, gamma)
        
        return np.clip(alpha_new, 0.0, 1.0).astype(np.float32)
