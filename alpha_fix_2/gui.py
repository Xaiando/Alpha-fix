from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk

from alpha_fix.error_report import report_gui_exception
from alpha_fix.sample_editor import SampleEditorDialog
from alpha_fix.samples import SampleRegion, draw_sample_overlays, load_sample_regions, save_sample_regions

from .config import AlphaFix2Config
from .service import AlphaFix2Service, BatchExportSummary, ExportSummary, PreviewResult


class AlphaFix2GUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Alpha Fix Sandbox")
        self.geometry("1720x1020")
        self.minsize(1380, 860)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "sandbox_exports"))
        self.mode_var = tk.StringVar(value="overlay")
        self.overlay_method_var = tk.StringVar(value="auto_hole")
        self.status_var = tk.StringVar(value="Sandbox ready.")
        self.frame_index_var = tk.IntVar(value=0)
        self.total_frames_var = tk.IntVar(value=0)
        self.export_format_var = tk.StringVar(value="webm_alpha")
        self.sample_summary_var = tk.StringVar(value="Samples: 0 | Background: 0 | Keep: 0")
        self.advanced_view_var = tk.BooleanVar(value=False)
        self.review_status_var = tk.StringVar(value="Review: no folder loaded.")
        self.sample_regions: list[SampleRegion] = []
        self._review_paths: tuple[Path, ...] = ()
        self._review_index = 0
        self._review_sample_regions: dict[Path, list[SampleRegion]] = {}
        self._review_approved: set[Path] = set()

        self.border_width_var = tk.IntVar(value=12)
        self.border_clusters_var = tk.IntVar(value=3)
        self.anchor_blend_var = tk.DoubleVar(value=0.0)
        self.subject_low_var = tk.DoubleVar(value=0.8)
        self.subject_high_var = tk.DoubleVar(value=2.5)
        self.overlay_low_var = tk.DoubleVar(value=0.3)
        self.overlay_high_var = tk.DoubleVar(value=2.3)
        self.lipc_lambda_var = tk.DoubleVar(value=0.65)
        self.lipc_delta_var = tk.DoubleVar(value=0.35)
        self.lipc_luma_var = tk.DoubleVar(value=0.80)
        self.chhc_alpha_var = tk.DoubleVar(value=0.12)
        self.chhc_close_var = tk.IntVar(value=5)
        self.chhc_min_hole_var = tk.DoubleVar(value=0.03)
        self.chhc_margin_var = tk.DoubleVar(value=0.05)
        self.sdr_enabled_var = tk.BooleanVar(value=False)
        self.sdr_k_var = tk.DoubleVar(value=0.6)
        self.sdr_sigma_var = tk.DoubleVar(value=1.5)
        self.osa_enabled_var = tk.BooleanVar(value=False)
        self.osa_mode_var = tk.StringVar(value="HTP")
        self.osa_pivot_var = tk.DoubleVar(value=0.50)
        self.osa_kappa_var = tk.DoubleVar(value=2.5)
        self.osa_R_var = tk.DoubleVar(value=2.5)
        self.osa_sigma_var = tk.DoubleVar(value=2.0)
        self.osa_omega_var = tk.DoubleVar(value=4.0)
        self.osa_lam_var = tk.DoubleVar(value=5.0)
        self.hole_dark_max_var = tk.DoubleVar(value=0.80)
        self.hole_flat_max_var = tk.DoubleVar(value=0.035)
        self.hole_min_area_var = tk.DoubleVar(value=0.01)
        self.hole_seed_dist_var = tk.DoubleVar(value=8.0)
        self.hole_flood_tol_var = tk.IntVar(value=18)
        self.hole_margin_var = tk.DoubleVar(value=0.05)
        self.srf_sigma_d_var = tk.DoubleVar(value=80.0)
        self.srf_sigma_c_var = tk.DoubleVar(value=18.0)
        self.srf_gamma_var = tk.DoubleVar(value=2.2)
        self.srf_tau_delta_var = tk.DoubleVar(value=12.0)
        self.srf_lambda_t_var = tk.DoubleVar(value=0.30)
        self.srf_edge_boost_var = tk.DoubleVar(value=0.25)
        self.chroma_target_a_var = tk.DoubleVar(value=69.0)
        self.chroma_target_b_var = tk.DoubleVar(value=185.0)
        self.chroma_low_var = tk.DoubleVar(value=55.0)
        self.chroma_high_var = tk.DoubleVar(value=82.0)
        self.chroma_portal_x_min_var = tk.DoubleVar(value=0.22)
        self.chroma_portal_x_max_var = tk.DoubleVar(value=0.78)
        self.chroma_portal_y_min_var = tk.DoubleVar(value=0.15)
        self.chroma_portal_y_max_var = tk.DoubleVar(value=0.88)
        self.checkerboard_low_var = tk.DoubleVar(value=15.0)
        self.checkerboard_high_var = tk.DoubleVar(value=25.0)
        self.checkerboard_size_var = tk.IntVar(value=0)
        self.checkerboard_offset_x_var = tk.IntVar(value=-1)
        self.checkerboard_offset_y_var = tk.IntVar(value=-1)

        self.despill_enabled_var = tk.BooleanVar(value=True)
        self.despill_target_var = tk.StringVar(value="auto")
        self.despill_strength_var = tk.DoubleVar(value=1.0)
        self.despill_threshold_var = tk.DoubleVar(value=1.0)

        self._preview_refs: dict[str, ImageTk.PhotoImage] = {}
        self._panel_widgets: dict[str, ttk.Label] = {}
        self._advanced_widgets: list[tk.Widget] = []

        self._build_layout()
        self._toggle_advanced_view()

    def report_callback_exception(self, exc: type[BaseException], val: BaseException, tb: object) -> None:
        report_gui_exception("Alpha Fix Sandbox", val, tb)

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        controls = ttk.Frame(self, padding=16)
        controls.grid(row=0, column=0, sticky="nsw")

        preview = ttk.Frame(self, padding=16)
        preview.grid(row=0, column=1, sticky="nsew")
        for col in range(4):
            preview.columnconfigure(col, weight=1)
        preview.rowconfigure(1, weight=1)
        preview.rowconfigure(3, weight=1)

        ttk.Label(controls, text="Input").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, width=42, textvariable=self.input_var).grid(row=1, column=0, sticky="ew")
        ttk.Button(controls, text="Browse", command=self._browse_input).grid(row=1, column=1, padx=(8, 0))
        ttk.Button(controls, text="Folder", command=self._browse_input_folder).grid(row=2, column=1, padx=(8, 0), pady=(6, 0))

        ttk.Label(controls, text="Output").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(controls, width=42, textvariable=self.output_var).grid(row=3, column=0, sticky="ew")
        ttk.Button(controls, text="Browse", command=self._browse_output).grid(row=3, column=1, padx=(8, 0))

        ttk.Label(controls, text="Mode").grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            values=("subject", "overlay"),
            state="readonly",
            width=18,
        ).grid(row=5, column=0, sticky="w")

        ttk.Label(controls, text="Overlay Method").grid(row=6, column=0, sticky="w", pady=(12, 0))
        ttk.Combobox(
            controls,
            textvariable=self.overlay_method_var,
            values=("auto_hole", "chhc", "radfield", "chroma", "checkerboard"),
            state="readonly",
            width=18,
        ).grid(row=7, column=0, sticky="w")

        samples_frame = ttk.LabelFrame(controls, text="Guided Samples", padding=12)
        samples_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        samples_frame.columnconfigure(0, weight=1)
        samples_frame.columnconfigure(1, weight=1)

        ttk.Button(samples_frame, text="Edit Samples", command=self._edit_samples).grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 6),
        )
        ttk.Button(samples_frame, text="Clear Samples", command=self._clear_samples).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 0),
            pady=(0, 6),
        )
        ttk.Label(samples_frame, textvariable=self.sample_summary_var, wraplength=310).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

        ttk.Separator(controls).grid(row=9, column=0, columnspan=2, sticky="ew", pady=14)
        advanced_toggle = ttk.Checkbutton(
            controls,
            text="Advanced View",
            variable=self.advanced_view_var,
            command=self._toggle_advanced_view,
        )
        advanced_toggle.grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, 8))

        numeric_fields = [
            ("Border Width", self.border_width_var),
            ("Border Clusters", self.border_clusters_var),
            ("Anchor Blend", self.anchor_blend_var),
            ("Subject Low", self.subject_low_var),
            ("Subject High", self.subject_high_var),
            ("Overlay Low", self.overlay_low_var),
            ("Overlay High", self.overlay_high_var),
            ("LIPC Lambda", self.lipc_lambda_var),
            ("LIPC Delta", self.lipc_delta_var),
            ("LIPC Luma", self.lipc_luma_var),
            ("CHHC Alpha", self.chhc_alpha_var),
            ("CHHC Close", self.chhc_close_var),
            ("CHHC Min Hole", self.chhc_min_hole_var),
            ("CHHC Margin", self.chhc_margin_var),
            ("Hole Dark Max", self.hole_dark_max_var),
            ("Hole Flat Max", self.hole_flat_max_var),
            ("Hole Min Area", self.hole_min_area_var),
            ("Hole Seed Dist", self.hole_seed_dist_var),
            ("Hole Flood Tol", self.hole_flood_tol_var),
            ("Hole Margin", self.hole_margin_var),
            ("SRF Sigma D", self.srf_sigma_d_var),
            ("SRF Sigma C", self.srf_sigma_c_var),
            ("SRF Gamma", self.srf_gamma_var),
            ("SRF Tau Delta", self.srf_tau_delta_var),
            ("SRF Lambda T", self.srf_lambda_t_var),
            ("SRF Edge Boost", self.srf_edge_boost_var),
            ("SDR K", self.sdr_k_var),
            ("SDR Sigma", self.sdr_sigma_var),
            ("OSA Pivot", self.osa_pivot_var),
            ("OSA Kappa", self.osa_kappa_var),
            ("OSA R", self.osa_R_var),
            ("OSA Sigma", self.osa_sigma_var),
            ("OSA Omega", self.osa_omega_var),
            ("OSA Lam", self.osa_lam_var),
            ("Chroma Target A", self.chroma_target_a_var),
            ("Chroma Target B", self.chroma_target_b_var),
            ("Chroma Low", self.chroma_low_var),
            ("Chroma High", self.chroma_high_var),
            ("Chroma Portal X Min", self.chroma_portal_x_min_var),
            ("Chroma Portal X Max", self.chroma_portal_x_max_var),
            ("Chroma Portal Y Min", self.chroma_portal_y_min_var),
            ("Chroma Portal Y Max", self.chroma_portal_y_max_var),
            ("Checkerboard Low", self.checkerboard_low_var),
            ("Checkerboard High", self.checkerboard_high_var),
            ("Checkerboard Size", self.checkerboard_size_var),
            ("Checkerboard Offset X", self.checkerboard_offset_x_var),
            ("Checkerboard Offset Y", self.checkerboard_offset_y_var),
            ("Despill Strength", self.despill_strength_var),
            ("Despill Threshold", self.despill_threshold_var),
        ]

        row = 11
        for label, variable in numeric_fields:
            label_widget = ttk.Label(controls, text=label)
            label_widget.grid(row=row, column=0, sticky="w", pady=(0, 2))
            entry_widget = ttk.Entry(controls, width=12, textvariable=variable)
            entry_widget.grid(row=row, column=1, sticky="w", padx=(8, 0))
            self._advanced_widgets.extend([label_widget, entry_widget])
            row += 1

        sdr_check = ttk.Checkbutton(controls, text="Enable SDR-Pow", variable=self.sdr_enabled_var)
        sdr_check.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 2),
        )
        self._advanced_widgets.append(sdr_check)
        row += 1

        osa_check = ttk.Checkbutton(controls, text="Enable OSA-v2", variable=self.osa_enabled_var)
        osa_check.grid(
            row=row,
            column=0,
            sticky="w",
            pady=(2, 8),
        )
        osa_combo = ttk.Combobox(
            controls,
            textvariable=self.osa_mode_var,
            values=("HTP", "lite"),
            state="readonly",
            width=8,
        )
        osa_combo.grid(row=row, column=1, sticky="w", pady=(2, 8))
        self._advanced_widgets.extend([osa_check, osa_combo])
        row += 1

        despill_check = ttk.Checkbutton(controls, text="Enable Despill", variable=self.despill_enabled_var)
        despill_check.grid(
            row=row,
            column=0,
            sticky="w",
            pady=(2, 8),
        )
        despill_combo = ttk.Combobox(
            controls,
            textvariable=self.despill_target_var,
            values=("auto", "green", "blue", "none"),
            state="readonly",
            width=8,
        )
        despill_combo.grid(row=row, column=1, sticky="w", pady=(2, 8))
        self._advanced_widgets.extend([despill_check, despill_combo])
        row += 1

        sandbox_note = ttk.Label(
            controls,
            text="Sandbox branch: experimental controls and debug views may change between passes.",
            wraplength=320,
        )
        sandbox_note.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self._advanced_widgets.append(sandbox_note)
        row += 1

        ttk.Label(controls, text="Timeline").grid(row=row, column=0, sticky="w", pady=(8, 2))
        self.timeline_slider = ttk.Scale(
            controls, 
            from_=0, 
            to=0, 
            variable=self.frame_index_var, 
            command=self._on_scrub
        )
        self.timeline_slider.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 2))
        row += 1
        
        self.frame_label = ttk.Label(controls, text="Frame: 0 / 0")
        self.frame_label.grid(row=row, column=1, sticky="e", pady=(0, 8))
        row += 1

        ttk.Button(controls, text="Preview Selected Frame", command=self._preview).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 8),
        )
        row += 1

        review_frame = ttk.LabelFrame(controls, text="Review", padding=10)
        review_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        review_frame.columnconfigure(0, weight=1)
        review_frame.columnconfigure(1, weight=1)
        ttk.Button(review_frame, text="X Draw", command=self._draw_current_review_item).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )
        ttk.Button(review_frame, text="✓ Keep / Next", command=self._keep_current_review_item).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )
        ttk.Label(review_frame, textvariable=self.review_status_var, wraplength=300).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )
        row += 1
        
        ttk.Label(controls, text="Export Format").grid(row=row, column=0, sticky="w", pady=(8, 2))
        ttk.Combobox(
            controls,
            textvariable=self.export_format_var,
            values=("chroma_mp4", "prores_4444", "webm_alpha", "png_sequence"),
            state="readonly",
            width=18,
        ).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 2))
        row += 1

        ttk.Button(controls, text="Start Processing", command=self._export).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )
        row += 1

        ttk.Label(controls, textvariable=self.status_var, wraplength=320).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(14, 0),
        )

        panels = [
            ("Source", "source", 0, 0),
            ("Composite", "result", 0, 1),
            ("Alpha", "alpha", 0, 2),
            ("Anchor", "anchor", 0, 3),
            ("Void Candidates", "void", 2, 0),
            ("Seed Map", "seed", 2, 1),
            ("Hole Mask", "hole", 2, 2),
            ("Frame Mask", "frame", 2, 3),
            ("Field Map", "field_map", 4, 0),
        ]
        for title, key, row_idx, col_idx in panels:
            ttk.Label(preview, text=title, anchor="center").grid(row=row_idx, column=col_idx, sticky="ew", pady=(0, 8))
            image_label = ttk.Label(preview)
            image_label.grid(row=row_idx + 1, column=col_idx, sticky="nsew", padx=8, pady=(0, 12))
            self._panel_widgets[key] = image_label

        self.diagnostics_text = ttk.Label(
            preview,
            text="Diagnostics: Run preview to inspect sandbox outputs.",
            justify="left",
            font=("Consolas", 10),
        )
        self.diagnostics_text.grid(row=6, column=0, columnspan=4, sticky="w", pady=(8, 0))

    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose input image or video",
            filetypes=[
                ("Media", "*.mp4 *.mov *.avi *.mkv *.webm *.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.input_var.set(path)
            self._clear_review_state()
            self._update_timeline_limits(path)
            self.after(50, self._preview)

    def _browse_input_folder(self) -> None:
        path = filedialog.askdirectory(title="Choose folder of images or videos")
        if path:
            self.input_var.set(path)
            self._load_review_folder(Path(path))
            self.total_frames_var.set(0)
            self.frame_index_var.set(0)
            self._on_scrub(0)
            self.timeline_slider.configure(to=0)
            self.after(50, self._preview)

    def _update_timeline_limits(self, path: str) -> None:
        if Path(path).is_dir():
            self.total_frames_var.set(0)
            self.frame_index_var.set(0)
            self._on_scrub(0)
            self.timeline_slider.configure(to=0)
            return

        import cv2
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            total = max(1, total) - 1
            self.total_frames_var.set(total)
            self.frame_index_var.set(0)
            self._on_scrub(0)
            self.timeline_slider.configure(to=total)
        cap.release()

    def _on_scrub(self, val: str | float) -> None:
        idx = int(float(val))
        self.frame_index_var.set(idx)
        self.frame_label.config(text=f"Frame: {idx} / {self.total_frames_var.get()}")

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Choose export folder")
        if path:
            self.output_var.set(path)

    def _toggle_advanced_view(self) -> None:
        for widget in self._advanced_widgets:
            if self.advanced_view_var.get():
                widget.grid()
            else:
                widget.grid_remove()

    def _clear_review_state(self) -> None:
        self._review_paths = ()
        self._review_index = 0
        self._review_sample_regions.clear()
        self._review_approved.clear()
        self.review_status_var.set("Review: single file.")
        self._update_sample_summary()

    def _load_review_folder(self, folder: Path) -> None:
        media_paths = AlphaFix2Service(self._build_config(sample_regions=())).discover_media(folder)
        self._review_paths = media_paths
        self._review_index = 0
        self._review_sample_regions.clear()
        self._review_approved.clear()
        self._update_review_status()

    def _current_review_path(self) -> Path | None:
        input_path = Path(self.input_var.get())
        if input_path.is_dir():
            if not self._review_paths:
                self._load_review_folder(input_path)
            if not self._review_paths:
                return None
            self._review_index = min(self._review_index, len(self._review_paths) - 1)
            return self._review_paths[self._review_index]
        return input_path if str(input_path) else None

    def _active_sample_regions(self) -> list[SampleRegion]:
        path = self._current_review_path()
        if path is not None and Path(self.input_var.get()).is_dir():
            return self._review_sample_regions.setdefault(path.resolve(), [])
        return self.sample_regions

    def _review_sample_overrides(self) -> dict[Path, tuple[SampleRegion, ...]]:
        return {
            path: tuple(regions)
            for path, regions in self._review_sample_regions.items()
            if len(regions) > 0
        }

    def _update_review_status(self) -> None:
        if not self._review_paths:
            if self.input_var.get().strip() and not Path(self.input_var.get()).is_dir():
                self.review_status_var.set("Review: single file.")
            else:
                self.review_status_var.set("Review: no folder loaded.")
            return

        current = self._review_paths[self._review_index]
        approved = len(self._review_approved)
        corrected = len(self._review_sample_regions)
        self.review_status_var.set(
            f"Review {self._review_index + 1}/{len(self._review_paths)}: {current.name} | "
            f"Kept: {approved} | Drawn: {corrected}"
        )

    def _keep_current_review_item(self) -> None:
        path = self._current_review_path()
        if path is None:
            messagebox.showerror("No review item", "Choose a file or folder first.")
            return

        if self._review_paths:
            self._review_approved.add(path.resolve())
            if self._review_index < len(self._review_paths) - 1:
                self._review_index += 1
                self._update_review_status()
                self._preview()
                return

            self._update_review_status()
            self.status_var.set("Review complete. Ready to export all.")
            return

        self.status_var.set("Kept current file. Ready to export.")

    def _draw_current_review_item(self) -> None:
        self._edit_samples()

    def _preview(self) -> None:
        try:
            config = self._build_config(sample_regions=tuple(self._active_sample_regions()))
            service = AlphaFix2Service(config)
            preview_path = self._current_review_path()
            if preview_path is None:
                raise ValueError("Choose a supported input file or folder.")
            preview = service.preview(preview_path, frame_index=self.frame_index_var.get())
        except Exception as exc:
            messagebox.showerror("Preview failed", str(exc))
            self.status_var.set(f"Preview failed: {exc}")
            return

        self._show_preview(preview)
        self.status_var.set(
            f"Preview ready in {config.mode} mode using {config.overlay_method}."
            if config.mode == "overlay"
            else f"Preview ready in {config.mode} mode."
        )

    def _show_preview(self, preview: PreviewResult) -> None:
        result = preview.frame_result
        source_rgb = draw_sample_overlays(
            result.rgba[:, :, :3].copy(),
            tuple(self._active_sample_regions()),
        )
        composite_rgb = self._checkerboard_composite(result.rgba)
        alpha_image = np.clip(result.alpha * 255.0, 0.0, 255.0).astype(np.uint8)
        anchor_image = np.clip(result.alpha0 * 255.0, 0.0, 255.0).astype(np.uint8)
        void_image = self._debug_image(result.debug_views.get("void_mask"), alpha_image.shape)
        seed_image = self._debug_image(result.debug_views.get("seed_map"), alpha_image.shape)
        hole_image = self._debug_image(result.debug_views.get("hole_mask"), alpha_image.shape)
        frame_image = self._debug_image(result.debug_views.get("frame_mask"), alpha_image.shape)
        field_map_image = self._debug_image(result.debug_views.get("field_map"), (*alpha_image.shape, 3))

        self._set_image(self._panel_widgets["source"], source_rgb, "source")
        self._set_image(self._panel_widgets["result"], composite_rgb, "result")
        self._set_image(self._panel_widgets["alpha"], alpha_image, "alpha", grayscale=True)
        self._set_image(self._panel_widgets["anchor"], anchor_image, "anchor", grayscale=True)
        self._set_image(self._panel_widgets["void"], void_image, "void", grayscale=True)
        self._set_image(self._panel_widgets["seed"], seed_image, "seed", grayscale=True)
        self._set_image(self._panel_widgets["hole"], hole_image, "hole", grayscale=True)
        self._set_image(self._panel_widgets["frame"], frame_image, "frame", grayscale=True)
        self._set_image(self._panel_widgets["field_map"], field_map_image, "field_map")

        mean_alpha = float(np.mean(result.alpha))
        mean_conf = float(np.mean(result.confidence))
        ambiguity_frac = float(np.mean(result.confidence < 0.5))
        correction_impact = float(np.mean(np.abs(result.alpha - result.alpha0)))
        seed_count = int(result.debug_stats.get("hole_seed_count", 0))
        hole_frac = float(result.debug_stats.get("hole_pixel_frac", 0.0))
        method = str(result.debug_stats.get("overlay_method", "n/a"))

        diag_str = (
            f"Diagnostics | Mode: {self.mode_var.get()} | Method: {method} | "
            f"Mean Alpha: {mean_alpha:.4f} | Mean Confidence: {mean_conf:.4f} | "
            f"Ambiguity Fraction (<0.5): {ambiguity_frac*100:.2f}% | "
            f"Correction Impact: {correction_impact:.4f} | "
            f"Seeds: {seed_count} | Hole Fraction: {hole_frac:.4f}"
        )
        self.diagnostics_text.config(text=diag_str)
        self._update_review_status()

    @staticmethod
    def _debug_image(view: np.ndarray | None, shape: tuple[int, int]) -> np.ndarray:
        if view is None:
            return np.zeros(shape, dtype=np.uint8)
        return np.clip(view * 255.0, 0.0, 255.0).astype(np.uint8)

    def _set_image(
        self,
        widget: ttk.Label,
        array: np.ndarray,
        key: str,
        grayscale: bool = False,
    ) -> None:
        image = Image.fromarray(array if not grayscale else array, mode=None)
        image.thumbnail((360, 320), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        widget.configure(image=photo)
        self._preview_refs[key] = photo

    @staticmethod
    def _checkerboard_composite(rgba: np.ndarray) -> np.ndarray:
        rgb = rgba[:, :, :3].astype(np.float32)
        alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
        height, width = alpha.shape[:2]
        tile = 24
        yy, xx = np.indices((height, width))
        board = ((xx // tile + yy // tile) % 2).astype(np.float32)
        checker = np.where(board[:, :, None] > 0.0, 216.0, 176.0)
        composite = rgb * alpha + checker * (1.0 - alpha)
        return np.clip(composite, 0.0, 255.0).astype(np.uint8)

    def _export(self) -> None:
        try:
            input_path = self.input_var.get().strip()
            output_path = self.output_var.get().strip()
            if not input_path:
                raise ValueError("Choose an input file before exporting.")
            if not output_path:
                raise ValueError("Choose an output folder before exporting.")
            path = Path(input_path)
            config = self._build_config(
                sample_regions=() if path.is_dir() else tuple(self._active_sample_regions())
            )
            sample_overrides = self._review_sample_overrides()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        self.status_var.set("Sandbox export started...")
        thread = threading.Thread(
            target=self._run_export,
            args=(config, input_path, output_path, self.export_format_var.get(), sample_overrides),
            daemon=True,
        )
        thread.start()

    def _run_export(
        self,
        config: AlphaFix2Config,
        input_path: str,
        output_path: str,
        format: str,
        sample_overrides: dict[Path, tuple[SampleRegion, ...]],
    ) -> None:
        service = AlphaFix2Service(config)

        def on_progress(done: int, total: int) -> None:
            self.after(0, lambda: self.status_var.set(f"Sandbox exporting frame {done}/{total}..."))

        try:
            if Path(input_path).is_dir():
                def on_batch_progress(done: int, total: int, current_path: Path) -> None:
                    self.after(
                        0,
                        lambda: self.status_var.set(
                            f"Sandbox batch {done}/{total}: {current_path.name}"
                        ),
                    )

                summary = service.export_batch(
                    input_path,
                    output_path,
                    format,
                    sample_regions_by_path=sample_overrides,
                    progress_callback=on_batch_progress,
                )
            else:
                summary = service.export_sequence(input_path, output_path, format, progress_callback=on_progress)
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: messagebox.showerror("Export failed", msg))
            self.after(0, lambda: self.status_var.set(f"Export failed: {msg}"))
            return

        self.after(0, lambda: self._finish_export(summary))

    def _finish_export(self, summary: ExportSummary | BatchExportSummary) -> None:
        if isinstance(summary, BatchExportSummary):
            self.status_var.set(
                f"Sandbox batch complete: {summary.succeeded}/{summary.item_count} file(s) exported to {summary.output_dir}."
            )
            messagebox.showinfo(
                "Batch export complete",
                f"Processed {summary.item_count} file(s).\n\n"
                f"Done: {summary.succeeded}\n"
                f"Failed: {summary.failed}\n\n"
                f"Output:\n{summary.output_dir}",
            )
            return

        self.status_var.set(
            f"Sandbox export complete: {summary.frame_count} frame(s) to {summary.output_dir} in {summary.mode} mode."
        )
        messagebox.showinfo(
            "Export complete",
            f"Saved {summary.frame_count} frame(s) to:\n{summary.output_dir}",
        )

    def _edit_samples(self) -> None:
        input_path = self.input_var.get().strip()
        if not input_path:
            messagebox.showerror("No input", "Choose an input file before editing samples.")
            return

        try:
            # We just need the frame to draw on. We can use the service's read logic.
            config = self._build_config(sample_regions=tuple(self._active_sample_regions()))
            service = AlphaFix2Service(config)
            path = self._current_review_path()
            if path is None:
                raise ValueError("Choose a supported input file or folder.")
            frame = service.preview(path, frame_index=self.frame_index_var.get()).frame_bgr
        except Exception as exc:
            messagebox.showerror("Unable to load frame", str(exc))
            self.status_var.set(f"Sample editor failed: {exc}")
            return

        dialog = SampleEditorDialog(self, frame, self._active_sample_regions())
        self.wait_window(dialog)
        if dialog.result is None:
            return
        if Path(input_path).is_dir():
            assert path is not None
            self._review_sample_regions[path.resolve()] = dialog.result
        else:
            self.sample_regions = dialog.result
        self._update_sample_summary()
        self._update_review_status()
        self.status_var.set(f"Updated guided samples: {len(dialog.result)} region(s).")
        self._preview()

    def _clear_samples(self) -> None:
        path = self._current_review_path()
        if path is not None and Path(self.input_var.get()).is_dir():
            self._review_sample_regions.pop(path.resolve(), None)
        else:
            self.sample_regions = []
        self._update_sample_summary()
        self._update_review_status()
        self.status_var.set("Cleared guided samples.")

    def _update_sample_summary(self) -> None:
        regions = self._active_sample_regions()
        bg_count = sum(1 for region in regions if region.kind == "background")
        keep_count = len(regions) - bg_count
        self.sample_summary_var.set(
            f"Samples: {len(regions)} | Background: {bg_count} | Keep: {keep_count}"
        )

    def _build_config(
        self,
        sample_regions: tuple[SampleRegion, ...] | None = None,
    ) -> AlphaFix2Config:
        if sample_regions is None:
            sample_regions = tuple(self._active_sample_regions())
        return AlphaFix2Config(
            mode=self.mode_var.get(),
            overlay_method=self.overlay_method_var.get(),
            sample_regions=sample_regions,
            border_width=int(self.border_width_var.get()),
            border_clusters=int(self.border_clusters_var.get()),
            anchor_blend=float(self.anchor_blend_var.get()),
            subject_low=float(self.subject_low_var.get()),
            subject_high=float(self.subject_high_var.get()),
            overlay_low=float(self.overlay_low_var.get()),
            overlay_high=float(self.overlay_high_var.get()),
            lipc_lambda=float(self.lipc_lambda_var.get()),
            lipc_t_delta=float(self.lipc_delta_var.get()),
            lipc_t_luma=float(self.lipc_luma_var.get()),
            chhc_t_alpha=float(self.chhc_alpha_var.get()),
            chhc_close_kernel=int(self.chhc_close_var.get()),
            chhc_min_hole_frac=float(self.chhc_min_hole_var.get()),
            chhc_valid_margin=float(self.chhc_margin_var.get()),
            sdr_enabled=bool(self.sdr_enabled_var.get()),
            sdr_k=float(self.sdr_k_var.get()),
            sdr_sigma=float(self.sdr_sigma_var.get()),
            osa_enabled=bool(self.osa_enabled_var.get()),
            osa_mode=self.osa_mode_var.get(),
            osa_pivot=float(self.osa_pivot_var.get()),
            osa_kappa=float(self.osa_kappa_var.get()),
            osa_R=float(self.osa_R_var.get()),
            osa_sigma=float(self.osa_sigma_var.get()),
            osa_omega=float(self.osa_omega_var.get()),
            osa_lam=float(self.osa_lam_var.get()),
            hole_dark_max=float(self.hole_dark_max_var.get()),
            hole_flat_max=float(self.hole_flat_max_var.get()),
            hole_min_area_frac=float(self.hole_min_area_var.get()),
            hole_seed_min_dist=float(self.hole_seed_dist_var.get()),
            hole_flood_tol=int(self.hole_flood_tol_var.get()),
            hole_margin_frac=float(self.hole_margin_var.get()),
            srf_sigma_d=float(self.srf_sigma_d_var.get()),
            srf_sigma_c=float(self.srf_sigma_c_var.get()),
            srf_gamma=float(self.srf_gamma_var.get()),
            srf_tau_delta=float(self.srf_tau_delta_var.get()),
            srf_lambda_t=float(self.srf_lambda_t_var.get()),
            srf_edge_boost=float(self.srf_edge_boost_var.get()),
            chroma_target_a=float(self.chroma_target_a_var.get()),
            chroma_target_b=float(self.chroma_target_b_var.get()),
            chroma_low=float(self.chroma_low_var.get()),
            chroma_high=float(self.chroma_high_var.get()),
            chroma_portal_x_min=float(self.chroma_portal_x_min_var.get()),
            chroma_portal_x_max=float(self.chroma_portal_x_max_var.get()),
            chroma_portal_y_min=float(self.chroma_portal_y_min_var.get()),
            chroma_portal_y_max=float(self.chroma_portal_y_max_var.get()),
            checkerboard_low=float(self.checkerboard_low_var.get()),
            checkerboard_high=float(self.checkerboard_high_var.get()),
            checkerboard_size=int(self.checkerboard_size_var.get()),
            checkerboard_offset_x=int(self.checkerboard_offset_x_var.get()),
            checkerboard_offset_y=int(self.checkerboard_offset_y_var.get()),
            despill_enabled=bool(self.despill_enabled_var.get()),
            despill_target=self.despill_target_var.get(),
            despill_strength=float(self.despill_strength_var.get()),
            despill_threshold=float(self.despill_threshold_var.get()),
        )


def launch_gui() -> None:
    try:
        app = AlphaFix2GUI()
        app.mainloop()
    except Exception as exc:
        report_gui_exception("Alpha Fix Sandbox", exc)
