from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from alpha_fix.pipeline import AlphaFixProcessor as BaseProcessor
from alpha_fix.pipeline import BorderPalette

from .config import AlphaFix2Config
from .radfield import init_radiation_state, update_radiation_state, RadiationState


@dataclass(slots=True)
class FrameResult:
    alpha0: np.ndarray
    alpha: np.ndarray
    alpha_ema: np.ndarray
    confidence: np.ndarray
    signed_distance: np.ndarray
    rgba: np.ndarray
    border_palette: BorderPalette
    debug_views: dict[str, np.ndarray]
    debug_stats: dict[str, float | int | str]


class AlphaFix2Processor(BaseProcessor):
    def __init__(self, config: AlphaFix2Config) -> None:
        super().__init__(config)
        self.lipc_state: dict[str, object] | None = None
        self._rad_state: RadiationState | None = None
        self.frame1_lab: np.ndarray | None = None
        self.prev_lab: np.ndarray | None = None
        self.frame1_b_field: np.ndarray | None = None
        self.frame1_k_field: np.ndarray | None = None
        self._last_change_mask_blend: np.ndarray | None = None
        self._frame1_background_mask: np.ndarray | None = None
        self._checkerboard_params: dict[str, object] | None = None

    def reset(self) -> None:
        super().reset()
        self.lipc_state = None
        self._rad_state = None
        self.frame1_lab = None
        self.prev_lab = None
        self.frame1_b_field = None
        self.frame1_k_field = None
        self._last_change_mask_blend = None
        self._frame1_background_mask = None
        self._checkerboard_params = None

    def fit_border_palette(self, frame_bgr: np.ndarray) -> BorderPalette:
        if self.config.mode == "subject":
            frame_lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
            border_pixels = self._sample_border_pixels(frame_lab)
            
            if len(border_pixels) == 0:
                center = frame_lab.reshape(-1, 3).mean(axis=0, keepdims=True)
                variance = np.full((1, 3), 64.0, dtype=np.float32)
                return BorderPalette(center.astype(np.float32), variance)

            sample_limit = min(self.config.border_sample_limit, len(border_pixels))
            if sample_limit < len(border_pixels):
                positions = np.linspace(0, len(border_pixels) - 1, sample_limit, dtype=np.int32)
                border_pixels = border_pixels[positions]

            cluster_count = max(1, min(self.config.border_clusters, len(border_pixels)))
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 0.2)
            _compactness, labels, centers = cv2.kmeans(
                border_pixels,
                cluster_count,
                None,
                criteria,
                4,
                cv2.KMEANS_PP_CENTERS,
            )

            label_values = labels.ravel()
            counts = np.bincount(label_values, minlength=cluster_count)
            fractions = counts / len(border_pixels)

            # Keep dominant backdrop clusters (fraction > 15%)
            dominant_idx = np.argmax(fractions)
            keep_indices = np.where(fractions > 0.15)[0]
            if len(keep_indices) == 0:
                keep_indices = [dominant_idx]

            centers = centers[keep_indices]
            
            variances: list[np.ndarray] = []
            for idx in keep_indices:
                members = border_pixels[label_values == idx]
                if len(members) == 0:
                    variances.append(np.full(3, 64.0, dtype=np.float32))
                else:
                    var = np.var(members, axis=0)
                    variances.append(np.maximum(var, 16.0).astype(np.float32))

            return BorderPalette(centers.astype(np.float32), np.array(variances))
        else:
            return super().fit_border_palette(frame_bgr)

    def process_frame(
        self,
        frame_bgr: np.ndarray,
        prev_alpha: np.ndarray | None = None,
    ) -> FrameResult:
        if self._border_palette is None:
            self._border_palette = self.fit_border_palette(frame_bgr)

        alpha0, confidence = self._build_anchor(frame_bgr)
        debug_views: dict[str, np.ndarray] = {"anchor": alpha0}
        debug_stats: dict[str, float | int | str] = {
            "overlay_method": self.config.overlay_method,
        }

        if self.config.mode == "overlay":
            if self.config.overlay_method == "auto_hole":
                alpha, extra_views, extra_stats = self._apply_auto_hole(alpha0, frame_bgr, self.config)
                debug_views.update(extra_views)
                debug_stats.update(extra_stats)
            elif self.config.overlay_method == "radfield":
                alpha = alpha0.copy()
                debug_views["frame_mask"] = (alpha >= 0.5).astype(np.float32)
            elif self.config.overlay_method == "chroma":
                alpha, extra_views, extra_stats = self._apply_chroma_key(frame_bgr, self.config)
                debug_views.update(extra_views)
                debug_stats.update(extra_stats)
            elif self.config.overlay_method == "checkerboard":
                alpha, extra_views, extra_stats = self._apply_checkerboard_key(frame_bgr, self.config)
                debug_views.update(extra_views)
                debug_stats.update(extra_stats)
            else:
                alpha = self._apply_chhc(alpha0, frame_bgr, self.config)
                debug_views["frame_mask"] = (alpha >= 0.5).astype(np.float32)
                debug_stats["hole_seed_count"] = 0
                debug_stats["hole_pixel_frac"] = 0.0

            # Force outer 8 pixels to be transparent to clean up edge vignette/compression artifacts
            margin = 8
            alpha[:margin, :] = 0.0
            alpha[-margin:, :] = 0.0
            alpha[:, :margin] = 0.0
            alpha[:, -margin:] = 0.0

            alpha_ema = alpha0.copy()
            signed_distance = self._signed_distance(alpha >= 0.5)
        else:
            if prev_alpha is None or self.frame1_lab is None:
                alpha = alpha0.copy()
            else:
                change_mask = self._last_change_mask_blend if self._last_change_mask_blend is not None else np.zeros(alpha0.shape, dtype=np.float32)
                alpha_blend = (
                    self.config.ema_decay * prev_alpha
                    + (1.0 - self.config.ema_decay) * alpha0
                ).astype(np.float32)
                # Bypassing EMA lag on moving pixels
                alpha = np.where(change_mask > 0.5, alpha0, alpha_blend)

            alpha_ema = alpha.copy()

            if self.config.osa_enabled:
                alpha = self._apply_osa_v2(alpha, alpha0, self.config)
            elif self.config.sdr_enabled:
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

        if self.config.anchor_blend > 0.0:
            alpha = (1.0 - self.config.anchor_blend) * alpha + self.config.anchor_blend * alpha0
            alpha = np.clip(alpha, 0.0, 1.0).astype(np.float32)

        self.prev_lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

        return FrameResult(
            alpha0=alpha0,
            alpha=alpha,
            alpha_ema=alpha_ema,
            confidence=confidence,
            signed_distance=signed_distance,
            rgba=self._rgba_from_alpha(frame_bgr, alpha),
            border_palette=self._border_palette,
            debug_views=debug_views,
            debug_stats=debug_stats,
        )

    def _fit_backdrop_palette(self, frame_bgr: np.ndarray, background_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        background_pixels_bgr = frame_bgr[background_mask > 0.0]
        if len(background_pixels_bgr) == 0:
            return None
            
        background_pixels_lab = cv2.cvtColor(
            background_pixels_bgr[:, None, :], 
            cv2.COLOR_BGR2LAB
        ).astype(np.float32)[:, 0, :]
        
        mins = np.percentile(background_pixels_lab, 1, axis=0)
        maxs = np.percentile(background_pixels_lab, 99, axis=0)
        stds = np.std(background_pixels_lab, axis=0)
        
        # Minimum tolerances to handle uniform colors and allow smooth feathering
        stds = np.maximum(stds, np.array([10.0, 6.0, 6.0], dtype=np.float32))
        
        return mins, maxs, stds

    def _palette_distance(self, frame_bgr: np.ndarray, mins: np.ndarray, maxs: np.ndarray, stds: np.ndarray) -> np.ndarray:
        frame_lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        dist = np.maximum(0.0, np.maximum(mins[None, None, :] - frame_lab, frame_lab - maxs[None, None, :]))
        scaled = dist / stds[None, None, :]
        distance = np.sqrt(np.sum(scaled * scaled, axis=-1))
        return distance.astype(np.float32)

    def _build_anchor(self, frame_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self.config.overlay_method in ("chroma", "checkerboard"):
            h, w = frame_bgr.shape[:2]
            alpha0 = np.ones((h, w), dtype=np.float32)
            confidence = np.ones((h, w), dtype=np.float32)
            return alpha0, confidence

        distance = self._border_distance(frame_bgr)
        edge_strength = self._edge_strength(frame_bgr)
        
        from alpha_fix.samples import build_sample_mask
        background_mask = build_sample_mask(frame_bgr.shape[:2], self.config.sample_regions, "background")
        has_manual = np.any(background_mask > 0.0)

        backdrop_bounds = None
        raw_alpha = None
        
        if self.config.mode == "overlay" and self.config.overlay_method == "radfield" and has_manual:
            backdrop_bounds = self._fit_backdrop_palette(frame_bgr, background_mask)
            if backdrop_bounds is not None:
                mins, maxs, stds = backdrop_bounds
                dist_backdrop = self._palette_distance(frame_bgr, mins, maxs, stds)
                raw_alpha = self._smoothstep(dist_backdrop, self.config.overlay_low, self.config.overlay_high)

        if self.config.mode == "overlay":
            if self.config.overlay_method == "radfield":
                alpha0 = np.ones(frame_bgr.shape[:2], dtype=np.float32)
            else:
                alpha0 = 1.0 - self._smoothstep(
                    distance,
                    self.config.overlay_low,
                    self.config.overlay_high,
                )
        else:
            raw_alpha_subj = self._smoothstep(
                distance,
                self.config.subject_low,
                self.config.subject_high,
            )
            raw_alpha_subj = np.clip(
                raw_alpha_subj + edge_strength * self.config.edge_boost * (1.0 - raw_alpha_subj),
                0.0,
                1.0,
            )
            
            # Topological Inward Radiation: Only erase continuous background touching the borders,
            # BUT do not protect disconnected holes if their colors are extremely close to the backdrop
            # (e.g. background showing through thin gaps in the hair).
            bg_mask = (raw_alpha_subj < 0.5).astype(np.uint8)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bg_mask, connectivity=4)
            
            h, w = bg_mask.shape
            border_labels = set()
            border_labels.update(labels[0, :])
            border_labels.update(labels[h-1, :])
            border_labels.update(labels[:, 0])
            border_labels.update(labels[:, w-1])
            if 0 in border_labels:
                border_labels.remove(0)
                
            protected_labels = set()
            for label_idx in range(1, num_labels):
                if label_idx in border_labels:
                    continue
                
                component_mask = (labels == label_idx)
                mean_dist = np.mean(distance[component_mask])
                
                # If the disconnected component has colors significantly different from the backdrop,
                # we assume it's part of the subject (e.g. dark clothes, shadows) and protect it.
                # If it's extremely close to the backdrop (mean_dist < 0.8), we let it remain transparent.
                if mean_dist >= 0.8:
                    protected_labels.add(label_idx)
                    
            bg_labels = border_labels.copy()
            for label_idx in range(1, num_labels):
                if label_idx not in protected_labels:
                    bg_labels.add(label_idx)
                    
            true_bg_mask = np.isin(labels, list(bg_labels))
            
            alpha0 = np.ones((h, w), dtype=np.float32)
            alpha0[true_bg_mask] = raw_alpha_subj[true_bg_mask]

        if self.config.anchor_blur_sigma > 0:
            alpha0 = cv2.GaussianBlur(alpha0, (0, 0), self.config.anchor_blur_sigma)

        confidence = np.clip(np.abs(alpha0 - 0.5) * 2.0, self.config.confidence_floor, 1.0)
        
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        if self.frame1_lab is None:
            # FRAME 1
            if len(self.config.sample_regions) > 0:
                from .radfield import compute_sample_radiation
                # Limit spatial bleed in overlay mode by decreasing srf_sigma_d dynamically
                effective_config = self.config
                if self.config.mode == "overlay":
                    h, w = frame_bgr.shape[:2]
                    effective_sigma_d = min(h, w) * 0.65
                    effective_config = self.config.updated(srf_sigma_d=effective_sigma_d)
                
                b_field, k_field = compute_sample_radiation(frame_bgr, effective_config)
            else:
                b_field = np.zeros(alpha0.shape, dtype=np.float32)
                k_field = np.zeros(alpha0.shape, dtype=np.float32)
                
            self.frame1_lab = lab.copy()
            self.frame1_b_field = b_field.copy()
            self.frame1_k_field = k_field.copy()
            self._last_change_mask_blend = np.zeros(alpha0.shape, dtype=np.float32)
            
            from alpha_fix.samples import build_sample_mask
            keep_mask = build_sample_mask(alpha0.shape, self.config.sample_regions, "keep")
            background_mask = build_sample_mask(alpha0.shape, self.config.sample_regions, "background")
            
            b_field_clean = self._smoothstep(b_field, 0.1, 0.6)
            k_field_clean = self._smoothstep(k_field, 0.1, 0.6)
            
            if raw_alpha is not None:
                alpha0 = np.clip(raw_alpha + (1.0 - b_field_clean), 0.0, 1.0)
            else:
                alpha0 = alpha0 * (1.0 - b_field_clean)
                
            alpha0 = np.maximum(alpha0, k_field_clean)
            
            # Apply hard background/keep masks on Frame 1 only
            alpha0 = alpha0 * (1.0 - background_mask)
            alpha0 = np.maximum(alpha0, keep_mask)
            
            confidence = np.maximum(confidence, b_field_clean)
            confidence = np.maximum(confidence, k_field_clean)
            confidence = np.maximum(confidence, keep_mask)
            confidence = np.maximum(confidence, background_mask)
            
        else:
            # FRAME 2+
            diff_f1 = np.linalg.norm(lab - self.frame1_lab, axis=-1)
            diff_prev = np.linalg.norm(lab - self.prev_lab, axis=-1) if self.prev_lab is not None else diff_f1
            
            change_mask_f1 = (diff_f1 > self.config.srf_tau_delta).astype(np.float32)
            change_mask_blend = ((diff_f1 > self.config.srf_tau_delta) | (diff_prev > self.config.srf_tau_delta)).astype(np.float32)
            self._last_change_mask_blend = change_mask_blend
            
            # Disable background/keep erasure where pixels changed
            effective_b_field = self.frame1_b_field * (1.0 - change_mask_f1)
            effective_k_field = self.frame1_k_field * (1.0 - change_mask_f1)
            
            b_field_clean = self._smoothstep(effective_b_field, 0.1, 0.6)
            k_field_clean = self._smoothstep(effective_k_field, 0.1, 0.6)
            
            if raw_alpha is not None:
                alpha0 = np.clip(raw_alpha + (1.0 - b_field_clean), 0.0, 1.0)
            else:
                alpha0 = alpha0 * (1.0 - b_field_clean)
                
            alpha0 = np.maximum(alpha0, k_field_clean)
            
            confidence = np.maximum(confidence, b_field_clean)
            confidence = np.maximum(confidence, k_field_clean)

        return alpha0.astype(np.float32), confidence.astype(np.float32)

    def _apply_chroma_key(
        self,
        frame_bgr: np.ndarray,
        cfg: AlphaFix2Config,
    ) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, float | int | str]]:
        height, width = frame_bgr.shape[:2]
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        diff_a = lab[:, :, 1] - cfg.chroma_target_a
        diff_b = lab[:, :, 2] - cfg.chroma_target_b
        chroma_dist = np.sqrt(diff_a**2 + diff_b**2)
        
        t = np.clip((chroma_dist - cfg.chroma_low) / (cfg.chroma_high - cfg.chroma_low + 1e-6), 0.0, 1.0)
        alpha = t * t * (3.0 - 2.0 * t)
        
        x_min_px = int(cfg.chroma_portal_x_min * width)
        x_max_px = int(cfg.chroma_portal_x_max * width)
        y_min_px = int(cfg.chroma_portal_y_min * height)
        y_max_px = int(cfg.chroma_portal_y_max * height)
        
        portal_mask = np.zeros((height, width), dtype=np.float32)
        portal_mask[y_min_px:y_max_px, x_min_px:x_max_px] = 1.0
        
        alpha_final = 1.0 - (1.0 - alpha) * portal_mask
        
        void_mask_view = np.clip(chroma_dist / 100.0, 0.0, 1.0)
        
        debug_views = {
            "void_mask": void_mask_view.astype(np.float32),
            "seed_map": portal_mask,
            "hole_mask": (1.0 - alpha_final).astype(np.float32),
            "frame_mask": (alpha_final >= 0.5).astype(np.float32),
        }
        
        hole_pixel_frac = float(np.mean(alpha_final < 0.5))
        
        debug_stats = {
            "hole_seed_count": 0,
            "hole_pixel_frac": hole_pixel_frac,
        }
        
        return alpha_final, debug_views, debug_stats

    def _apply_auto_hole(
        self,
        alpha0: np.ndarray,
        frame_bgr: np.ndarray,
        cfg: AlphaFix2Config,
    ) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, float | int | str]]:
        frame_fill, closed_mask = self._extract_outer_frame_mask(alpha0, cfg)
        debug_views: dict[str, np.ndarray] = {
            "closed_mask": closed_mask.astype(np.float32),
            "frame_fill": frame_fill.astype(np.float32),
        }
        debug_stats: dict[str, float | int | str] = {
            "hole_seed_count": 0,
            "hole_pixel_frac": 0.0,
        }

        if not np.any(frame_fill):
            fallback = self._apply_chhc(alpha0, frame_bgr, cfg)
            return fallback, debug_views, debug_stats

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
        debug_views["void_mask"] = void_mask.astype(np.float32)

        seeds, seed_map = self._select_hole_seeds(void_mask, frame_fill, cfg)
        debug_views["seed_map"] = seed_map.astype(np.float32)
        debug_stats["hole_seed_count"] = len(seeds)

        if not seeds:
            fallback = self._apply_chhc(alpha0, frame_bgr, cfg)
            return fallback, debug_views, debug_stats

        hole_mask = self._grow_holes(gray, void_mask, seeds, cfg)
        debug_views["hole_mask"] = hole_mask.astype(np.float32)
        debug_stats["hole_pixel_frac"] = float(np.mean(hole_mask))

        if not np.any(hole_mask):
            fallback = self._apply_chhc(alpha0, frame_bgr, cfg)
            return fallback, debug_views, debug_stats

        solid_mask = frame_fill & ~hole_mask
        keep_mask = self._overlay_keep_mask(alpha0.shape)
        if np.any(keep_mask):
            debug_views["keep_mask"] = keep_mask.astype(np.float32)
            solid_mask = solid_mask | (keep_mask & frame_fill)
        debug_views["frame_mask"] = solid_mask.astype(np.float32)
        alpha = self._feather_binary_mask(solid_mask, cfg.chhc_feather_r)
        return alpha, debug_views, debug_stats



    def _extract_outer_frame_mask(
        self,
        alpha0: np.ndarray,
        cfg: AlphaFix2Config,
    ) -> tuple[np.ndarray, np.ndarray]:
        height, width = alpha0.shape
        raw = (alpha0 > cfg.chhc_t_alpha).astype(np.uint8) * 255
        kernel_size = max(3, int(cfg.chhc_close_kernel) | 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        closed = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, kernel)

        contours, hierarchy = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None or len(contours) == 0:
            return np.zeros((height, width), dtype=bool), (closed > 0)

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
            return np.zeros((height, width), dtype=bool), (closed > 0)

        frame_fill = np.zeros((height, width), dtype=np.uint8)
        cv2.drawContours(frame_fill, contours, frame_idx, 255, cv2.FILLED)
        return frame_fill > 0, closed > 0

    def _select_hole_seeds(
        self,
        void_mask: np.ndarray,
        frame_fill: np.ndarray,
        cfg: AlphaFix2Config,
    ) -> tuple[list[tuple[int, int]], np.ndarray]:
        height, width = void_mask.shape
        seed_map = np.zeros((height, width), dtype=np.uint8)
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

        candidates = []
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
            dist_to_center = np.sqrt((centroid_x - cx)**2 + (centroid_y - cy)**2)
            centrality = max(0.0, 1.0 - (dist_to_center / max_dist))

            score = rect_score * (centrality ** 0.5)

            if score < 0.2:
                continue

            candidates.append((score, int(x), int(y)))

        candidates.sort(key=lambda c: c[0], reverse=True)
        top_candidates = candidates[:2]  # Allow up to 2 high-quality seeds

        seeds: list[tuple[int, int]] = []
        for _score, x, y in top_candidates:
            seed_map[y, x] = 255
            seeds.append((x, y))

        return seeds, seed_map

    @staticmethod
    def _grow_holes(
        gray: np.ndarray,
        void_mask: np.ndarray,
        seeds: list[tuple[int, int]],
        cfg: AlphaFix2Config,
    ) -> np.ndarray:
        height, width = gray.shape
        gray_u8 = np.clip(gray * 255.0, 0.0, 255.0).astype(np.uint8)
        mask = np.ones((height + 2, width + 2), dtype=np.uint8)
        mask[1 : height + 1, 1 : width + 1] = (~void_mask).astype(np.uint8)
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

    def _apply_osa_v2(self, alpha_ema: np.ndarray, alpha_0: np.ndarray, cfg: AlphaFix2Config) -> np.ndarray:
        m_fg = (alpha_ema >= cfg.osa_pivot).astype(np.uint8)
        d_in = cv2.distanceTransform(m_fg, cv2.DIST_L2, 3)
        d_out = cv2.distanceTransform(1 - m_fg, cv2.DIST_L2, 3)
        S = d_out - d_in

        S_smooth = cv2.GaussianBlur(S, (5, 5), 0)
        gx = cv2.Sobel(S_smooth, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(S_smooth, cv2.CV_32F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2) + 1e-6
        nx, ny = gx / mag, gy / mag

        if cfg.osa_mode == 'HTP':
            S_abs = np.abs(S)
            dist_beyond = np.maximum(0, S_abs - cfg.osa_R)
            envelope = np.exp(-(dist_beyond**2) / (2.0 * max(cfg.osa_sigma, 1e-6)**2))
            delta_t = np.abs(alpha_ema - alpha_0)
            w_lag = np.exp(-cfg.osa_lam * delta_t)
            v_raw = cfg.osa_kappa * np.tanh(cfg.osa_omega * (cfg.osa_pivot - alpha_ema)) * w_lag * envelope
        else:
            envelope = np.exp(-(S**2) / (2.0 * max(cfg.osa_sigma, 1e-6)**2))
            v_raw = cfg.osa_kappa * 16.0 * np.maximum(0, cfg.osa_pivot - alpha_ema) * alpha_ema * envelope

        v_mag = np.clip(v_raw, -3.0, 3.0)
        h, w = alpha_ema.shape
        y_idx, x_idx = np.indices((h, w), dtype=np.float32)

        alpha_shocked = cv2.remap(
            alpha_ema,
            x_idx + v_mag * nx,
            y_idx + v_mag * ny,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )

        return np.clip(alpha_shocked, 0.0, 1.0).astype(np.float32)

    def _rgba_from_alpha(self, frame_bgr: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        cfg = self.config
        
        if cfg.despill_enabled and cfg.despill_target != "none":
            # Convert BGR to RGB (float32)
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
            
            # Determine target color (green or blue)
            target = "green"
            if cfg.despill_target in ("green", "blue"):
                target = cfg.despill_target
            elif cfg.despill_target == "auto":
                pixel_bgr = None
                if cfg.overlay_method == "chroma":
                    pixel_lab = np.array([[[128, cfg.chroma_target_a, cfg.chroma_target_b]]], dtype=np.uint8)
                    pixel_bgr = cv2.cvtColor(pixel_lab, cv2.COLOR_LAB2BGR)[0, 0]
                elif self._border_palette is not None and len(self._border_palette.centers) > 0:
                    center_lab = np.clip(self._border_palette.centers[0], 0.0, 255.0).astype(np.uint8)
                    pixel_lab = np.array([[center_lab]], dtype=np.uint8)
                    pixel_bgr = cv2.cvtColor(pixel_lab, cv2.COLOR_LAB2BGR)[0, 0]
                    
                if pixel_bgr is not None:
                    # pixel_bgr is [B, G, R]
                    b, g, r = pixel_bgr
                    if g > b:
                        target = "green"
                    else:
                        target = "blue"
                else:
                    # Fallback to checking median border RGB
                    med_rgb = self._median_border_rgb(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
                    if med_rgb[1] > med_rgb[2]:
                        target = "green"
                    else:
                        target = "blue"
            
            # Transition edge pixels where alpha < 0.95
            mask = alpha < 0.95
            if np.any(mask):
                R = rgb[:, :, 0]
                G = rgb[:, :, 1]
                B = rgb[:, :, 2]
                
                strength = cfg.despill_strength
                threshold = cfg.despill_threshold
                
                if target == "green":
                    max_rb = np.maximum(R, B)
                    excess = np.maximum(0.0, G - max_rb * threshold)
                    G[mask] = G[mask] - strength * excess[mask]
                elif target == "blue":
                    max_rg = np.maximum(R, G)
                    excess = np.maximum(0.0, B - max_rg * threshold)
                    B[mask] = B[mask] - strength * excess[mask]
                    
                rgb[:, :, 0] = R
                rgb[:, :, 1] = G
                rgb[:, :, 2] = B
                
            rgb = np.clip(rgb, 0.0, 255.0).astype(np.uint8)
        else:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
        # Standard subject color bleeding if applicable
        solid_fg_mask = (alpha > 0.90).astype(np.float32)
        edge_mask = (alpha > 0.0) & (alpha <= 0.90)
        
        if cfg.mode == "subject" and np.any(edge_mask) and np.any(solid_fg_mask):
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

    def _apply_checkerboard_key(
        self,
        frame_bgr: np.ndarray,
        cfg: AlphaFix2Config,
    ) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, float | int | str]]:
        h, w = frame_bgr.shape[:2]
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        if self._checkerboard_params is None:
            # We construct a top corners mask to sample clean background checkerboard
            margin = 4
            corner_w = min(48, max(16, min(h, w) // 4))
            top_mask = np.zeros((h, w), dtype=bool)
            top_mask[margin:corner_w, margin:corner_w] = True
            top_mask[margin:corner_w, -corner_w:-margin] = True
            
            size = cfg.checkerboard_size
            off_x = cfg.checkerboard_offset_x
            off_y = cfg.checkerboard_offset_y
            
            if size <= 0 or off_x < 0 or off_y < 0:
                top_pixels = gray[top_mask]
                y_top, x_top = np.where(top_mask)
                pixel_data = top_pixels.astype(np.float32).reshape(-1, 1)
                
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
                _, _, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
                c1, c2 = float(centers[0][0]), float(centers[1][0])
                color_min = min(c1, c2)
                color_max = max(c1, c2)
                
                top_vals = top_pixels.astype(np.float32)
                
                # 1. Coarse search on top corners
                best_score = -1.0
                best_size = 16.0
                best_off_x = 0.0
                best_off_y = 0.0
                
                for s in range(4, 65):
                    step = max(1, s // 8)
                    for ox in range(0, s, step):
                        for oy in range(0, s, step):
                            phase = (np.floor((x_top - ox) / s) + np.floor((y_top - oy) / s)) % 2
                            expected = np.where(phase == 0, color_min, color_max)
                            mae = np.mean(np.abs(top_vals - expected))
                            score = 1.0 / (mae + 1e-5)
                            if score > best_score:
                                best_score = score
                                best_size = float(s)
                                best_off_x = float(ox)
                                best_off_y = float(oy)
                
                # 2. Stage 1: Coarse float search
                stage1_best_score = best_score
                stage1_size = best_size
                stage1_off_x = best_off_x
                stage1_off_y = best_off_y
                
                for size_f in np.arange(best_size - 1.5, best_size + 1.6, 0.1):
                    if size_f < 4:
                        continue
                    for off_x_f in np.arange(best_off_x - 4.0, best_off_x + 4.1, 1.0):
                        for off_y_f in np.arange(best_off_y - 4.0, best_off_y + 4.1, 1.0):
                            phase = (np.floor((x_top - off_x_f) / size_f) + np.floor((y_top - off_y_f) / size_f)) % 2
                            expected = np.where(phase == 0, color_min, color_max)
                            mae = np.mean(np.abs(top_vals - expected))
                            score = 1.0 / (mae + 1e-5)
                            if score > stage1_best_score:
                                stage1_best_score = score
                                stage1_size = size_f
                                stage1_off_x = off_x_f
                                stage1_off_y = off_y_f
                
                # 3. Stage 2: Fine float search
                fine_best_score = stage1_best_score
                fine_size = stage1_size
                fine_off_x = stage1_off_x
                fine_off_y = stage1_off_y
                
                for size_f in np.arange(stage1_size - 0.15, stage1_size + 0.16, 0.01):
                    if size_f < 4:
                        continue
                    for off_x_f in np.arange(stage1_off_x - 1.0, stage1_off_x + 1.1, 0.2):
                        for off_y_f in np.arange(stage1_off_y - 1.0, stage1_off_y + 1.1, 0.2):
                            phase = (np.floor((x_top - off_x_f) / size_f) + np.floor((y_top - off_y_f) / size_f)) % 2
                            expected = np.where(phase == 0, color_min, color_max)
                            mae = np.mean(np.abs(top_vals - expected))
                            score = 1.0 / (mae + 1e-5)
                            if score > fine_best_score:
                                fine_best_score = score
                                fine_size = size_f
                                fine_off_x = off_x_f
                                fine_off_y = off_y_f
                
                size = fine_size
                off_x = fine_off_x
                off_y = fine_off_y
            
            # Recalculate colors based on BOTH top corners, using a clean 48x48 region and median
            sample_mask = np.zeros((h, w), dtype=bool)
            sample_mask[margin:corner_w, margin:corner_w] = True
            sample_mask[margin:corner_w, -corner_w:-margin] = True
            
            y_all, x_all = np.indices((h, w))
            phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2
            
            corner_bgr_pixels = frame_bgr[sample_mask]
            corner_phases = phase_all[sample_mask]
            
            p0_pixels = corner_bgr_pixels[corner_phases == 0]
            p1_pixels = corner_bgr_pixels[corner_phases == 1]
            
            # Robust median colors
            color1_bgr = np.median(p0_pixels, axis=0) if len(p0_pixels) > 0 else np.array([102.0, 102.0, 102.0])
            color2_bgr = np.median(p1_pixels, axis=0) if len(p1_pixels) > 0 else np.array([153.0, 153.0, 153.0])
            
            self._checkerboard_params = {
                "size": size,
                "offset_x": off_x,
                "offset_y": off_y,
                "color1_bgr": color1_bgr,
                "color2_bgr": color2_bgr,
            }
            print(f"[Checkerboard] Detected size={size:.4f}, offset=({off_x:.2f}, {off_y:.2f}), colors: {color1_bgr} / {color2_bgr}", flush=True)
            
        params = self._checkerboard_params
        size = params["size"]
        off_x = params["offset_x"]
        off_y = params["offset_y"]
        color1_bgr = params["color1_bgr"]
        color2_bgr = params["color2_bgr"]
        
        y_all, x_all = np.indices((h, w))
        phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2
        
        diff1 = frame_bgr.astype(np.float32) - color1_bgr
        dist1 = np.sqrt(np.sum(diff1 * diff1, axis=-1))
        
        diff2 = frame_bgr.astype(np.float32) - color2_bgr
        dist2 = np.sqrt(np.sum(diff2 * diff2, axis=-1))
        
        dist = np.minimum(dist1, dist2)
        dist = cv2.GaussianBlur(dist, (5, 5), 0)
        
        # Pixel-level alpha
        t = np.clip((dist - cfg.checkerboard_low) / (cfg.checkerboard_high - cfg.checkerboard_low + 1e-6), 0.0, 1.0)
        alpha_pixel = t * t * (3.0 - 2.0 * t)
        
        # Cell-guided classification to fill checkerboard holes in solid subject regions
        cell_x = np.floor((x_all - off_x) / size)
        cell_y = np.floor((y_all - off_y) / size)
        
        min_cx = np.min(cell_x)
        min_cy = np.min(cell_y)
        cell_x_idx = (cell_x - min_cx).astype(np.int32)
        cell_y_idx = (cell_y - min_cy).astype(np.int32)
        
        num_cx = np.max(cell_x_idx) + 1
        num_cy = np.max(cell_y_idx) + 1
        
        cell_sum = np.zeros((num_cy, num_cx), dtype=np.float32)
        cell_count = np.zeros((num_cy, num_cx), dtype=np.float32)
        
        np.add.at(cell_sum, (cell_y_idx, cell_x_idx), dist)
        np.add.at(cell_count, (cell_y_idx, cell_x_idx), 1.0)
        
        grid_mean = cell_sum / np.maximum(cell_count, 1.0)
        
        # Max filter over 3x3 neighbor cells (dilation)
        kernel = np.ones((3, 3), dtype=np.uint8)
        grid_max_neighbor = cv2.dilate(grid_mean, kernel)
        
        # Cells where all neighbors are background (mean distance < high threshold)
        is_bg_cell = (grid_max_neighbor < cfg.checkerboard_high).astype(np.uint8)
        
        # Topological connectivity check: keep only background cells connected to the borders
        n_y, n_x = is_bg_cell.shape
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(is_bg_cell, connectivity=4)
        
        border_labels = set()
        for x in range(n_x):
            border_labels.add(labels[0, x])
            border_labels.add(labels[n_y - 1, x])
        for y in range(n_y):
            border_labels.add(labels[y, 0])
            border_labels.add(labels[y, n_x - 1])
            
        if 0 in border_labels:
            border_labels.remove(0)
            
        is_bg_cell_connected = np.isin(labels, list(border_labels)).astype(np.uint8)
        
        # Dilate to cover boundary cells
        near_bg_cell = cv2.dilate(is_bg_cell_connected, kernel)
        
        # Bilinear upscale of near_bg_cell to full frame size for a smooth weight map
        near_bg_smooth = cv2.resize(near_bg_cell.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        
        # Force near_bg_smooth to 1 near the edges of the image (within 48 pixels)
        # to ensure the background is completely keyed out and not blocked by subject dilation.
        edge_margin = 48
        if h > 2 * edge_margin and w > 2 * edge_margin:
            border_mask = np.ones((h, w), dtype=np.float32)
            border_mask[edge_margin:-edge_margin, edge_margin:-edge_margin] = 0.0
            border_mask = cv2.GaussianBlur(border_mask, (15, 15), 0)
            near_bg_smooth = np.maximum(near_bg_smooth, border_mask)
        
        # Smoothly blend pixel-level alpha with solid foreground (1.0)
        alpha = near_bg_smooth * alpha_pixel + (1.0 - near_bg_smooth) * 1.0
        
        debug_views = {
            "void_mask": np.clip(dist / 100.0, 0.0, 1.0).astype(np.float32),
            "seed_map": (phase_all == 0).astype(np.float32),
            "hole_mask": (1.0 - alpha).astype(np.float32),
            "frame_mask": (alpha >= 0.5).astype(np.float32),
        }
        
        hole_pixel_frac = float(np.mean(alpha < 0.5))
        debug_stats = {
            "hole_seed_count": 0,
            "hole_pixel_frac": hole_pixel_frac,
            "checkerboard_size": size,
            "checkerboard_offset_x": off_x,
            "checkerboard_offset_y": off_y,
        }
        
        return alpha, debug_views, debug_stats
