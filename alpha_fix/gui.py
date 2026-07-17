from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk

from .config import AlphaFixConfig
from .error_report import report_gui_exception
from .sample_editor import SampleEditorDialog
from .samples import SampleRegion, draw_sample_overlays, load_sample_regions, save_sample_regions
from .service import AlphaFixService, ExportSummary, PreviewResult


class AlphaFixGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Alpha Fix")
        self.geometry("1460x900")
        self.minsize(1200, 760)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "exports"))
        self.mode_var = tk.StringVar(value="overlay")
        self.overlay_method_var = tk.StringVar(value="auto_hole")
        self.export_format_var = tk.StringVar(value="prores_4444")
        self.status_var = tk.StringVar(value="Ready.")

        self.border_width_var = tk.IntVar(value=12)
        self.border_clusters_var = tk.IntVar(value=3)
        self.subject_low_var = tk.DoubleVar(value=1.4)
        self.subject_high_var = tk.DoubleVar(value=4.5)
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
        self.sample_summary_var = tk.StringVar(value="Samples: 0 | Background: 0 | Keep: 0")
        self.sample_regions: list[SampleRegion] = []

        self._preview_refs: dict[str, ImageTk.PhotoImage] = {}

        self._build_layout()

    def report_callback_exception(self, exc: type[BaseException], val: BaseException, tb: object) -> None:
        report_gui_exception("Alpha Fix", val, tb)

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        controls = ttk.Frame(self, padding=16)
        controls.grid(row=0, column=0, sticky="nsw")
        controls.columnconfigure(0, weight=1)

        preview = ttk.Frame(self, padding=16)
        preview.grid(row=0, column=1, sticky="nsew")
        preview.columnconfigure(0, weight=1)
        preview.columnconfigure(1, weight=1)
        preview.columnconfigure(2, weight=1)
        preview.columnconfigure(3, weight=1)
        preview.rowconfigure(1, weight=1)

        files_frame = ttk.LabelFrame(controls, text="Files", padding=12)
        files_frame.grid(row=0, column=0, sticky="ew")
        files_frame.columnconfigure(0, weight=1)

        ttk.Label(files_frame, text="Input").grid(row=0, column=0, sticky="w")
        ttk.Entry(files_frame, width=42, textvariable=self.input_var).grid(row=1, column=0, sticky="ew")
        ttk.Button(files_frame, text="Browse", command=self._browse_input).grid(row=1, column=1, padx=(8, 0))

        ttk.Label(files_frame, text="Output").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(files_frame, width=42, textvariable=self.output_var).grid(row=3, column=0, sticky="ew")
        ttk.Button(files_frame, text="Browse", command=self._browse_output).grid(row=3, column=1, padx=(8, 0))

        ttk.Label(files_frame, text="Mode").grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Combobox(
            files_frame,
            textvariable=self.mode_var,
            values=("subject", "overlay"),
            state="readonly",
            width=18,
        ).grid(row=5, column=0, sticky="w")
        ttk.Label(files_frame, text="Overlay Engine").grid(row=6, column=0, sticky="w", pady=(12, 0))
        ttk.Combobox(
            files_frame,
            textvariable=self.overlay_method_var,
            values=("auto_hole", "chhc"),
            state="readonly",
            width=18,
        ).grid(row=7, column=0, sticky="w")

        workflow_frame = ttk.LabelFrame(controls, text="Process", padding=12)
        workflow_frame.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        workflow_frame.columnconfigure(0, weight=1)
        workflow_frame.columnconfigure(1, weight=1)

        ttk.Label(workflow_frame, text="Export Format").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            workflow_frame,
            textvariable=self.export_format_var,
            values=("prores_4444", "webm_alpha", "chroma_mp4", "png_sequence"),
            state="readonly",
            width=18,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 10))

        ttk.Button(workflow_frame, text="Preview Current File", command=self._preview).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(workflow_frame, text="Process To Output Folder", command=self._export).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(workflow_frame, text="Open Output Folder", command=self._open_output_folder).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
        )
        ttk.Label(
            workflow_frame,
            text="Workflow: choose an input file, choose an output folder, select a media format, then press Process To Output Folder. PNG frames are always written into rgba and alpha subfolders. Alpha video formats may look dark in normal players because they are shown over black.",
            wraplength=310,
            justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

        samples_frame = ttk.LabelFrame(controls, text="Guided Samples", padding=12)
        samples_frame.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        samples_frame.columnconfigure(0, weight=1)
        samples_frame.columnconfigure(1, weight=1)

        ttk.Button(samples_frame, text="Edit Samples", command=self._edit_samples).grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 6),
        )
        ttk.Button(samples_frame, text="Load Preset", command=self._load_sample_preset).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 0),
            pady=(0, 6),
        )
        ttk.Button(samples_frame, text="Save Preset", command=self._save_sample_preset).grid(
            row=1,
            column=0,
            sticky="ew",
        )
        ttk.Button(samples_frame, text="Clear Samples", command=self._clear_samples).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(8, 0),
        )
        ttk.Label(samples_frame, textvariable=self.sample_summary_var, wraplength=310).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

        tuning_frame = ttk.LabelFrame(controls, text="Advanced Tuning", padding=12)
        tuning_frame.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        tuning_frame.columnconfigure(0, weight=1)
        tuning_frame.columnconfigure(1, weight=0)

        numeric_fields = [
            ("Border Width", self.border_width_var),
            ("Border Clusters", self.border_clusters_var),
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
            ("SDR K", self.sdr_k_var),
            ("SDR Sigma", self.sdr_sigma_var),
        ]

        row = 0
        for label, variable in numeric_fields:
            ttk.Label(tuning_frame, text=label).grid(row=row, column=0, sticky="w", pady=(0, 2))
            ttk.Entry(tuning_frame, width=12, textvariable=variable).grid(row=row, column=1, sticky="w", padx=(8, 0))
            row += 1

        ttk.Checkbutton(tuning_frame, text="Enable SDR-Pow", variable=self.sdr_enabled_var).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

        ttk.Label(controls, textvariable=self.status_var, wraplength=310).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(14, 0),
        )

        self.original_label = ttk.Label(preview, text="Source", anchor="center")
        self.original_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.result_label = ttk.Label(preview, text="Composite", anchor="center")
        self.result_label.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        self.alpha_label = ttk.Label(preview, text="Alpha", anchor="center")
        self.alpha_label.grid(row=0, column=2, sticky="ew", pady=(0, 8))
        self.confidence_label = ttk.Label(preview, text="Confidence Map", anchor="center")
        self.confidence_label.grid(row=0, column=3, sticky="ew", pady=(0, 8))

        self.original_image = ttk.Label(preview)
        self.original_image.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self.result_image = ttk.Label(preview)
        self.result_image.grid(row=1, column=1, sticky="nsew", padx=8)
        self.alpha_image = ttk.Label(preview)
        self.alpha_image.grid(row=1, column=2, sticky="nsew", padx=8)
        self.confidence_image = ttk.Label(preview)
        self.confidence_image.grid(row=1, column=3, sticky="nsew", padx=(8, 0))

        self.diagnostics_text = ttk.Label(preview, text="Diagnostics: Run preview to compute.", justify="left", font=("Consolas", 10))
        self.diagnostics_text.grid(row=2, column=0, columnspan=4, sticky="w", pady=(16, 0))

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

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Choose export folder")
        if path:
            self.output_var.set(path)

    def _open_output_folder(self) -> None:
        output_path = self.output_var.get().strip()
        if not output_path:
            messagebox.showerror("No output folder", "Choose an output folder first.")
            return
        target = Path(output_path)
        target.mkdir(parents=True, exist_ok=True)
        os.startfile(str(target))

    def _edit_samples(self) -> None:
        input_path = self.input_var.get().strip()
        if not input_path:
            messagebox.showerror("No input", "Choose an input file before editing samples.")
            return

        try:
            frame = AlphaFixService(AlphaFixConfig()).load_input_frame(input_path)
        except Exception as exc:
            messagebox.showerror("Unable to load frame", str(exc))
            self.status_var.set(f"Sample editor failed: {exc}")
            return

        dialog = SampleEditorDialog(self, frame, self.sample_regions)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        self.sample_regions = dialog.result
        self._update_sample_summary()
        self.status_var.set(f"Updated guided samples: {len(self.sample_regions)} region(s).")

    def _load_sample_preset(self) -> None:
        path = filedialog.askopenfilename(
            title="Load sample preset",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.sample_regions = load_sample_regions(path)
        except Exception as exc:
            messagebox.showerror("Load failed", str(exc))
            self.status_var.set(f"Sample preset load failed: {exc}")
            return
        self._update_sample_summary()
        self.status_var.set(f"Loaded sample preset: {Path(path).name}")

    def _save_sample_preset(self) -> None:
        if not self.sample_regions:
            messagebox.showerror("No samples", "Create at least one sample before saving a preset.")
            return
        path = filedialog.asksaveasfilename(
            title="Save sample preset",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            save_sample_regions(path, self.sample_regions)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            self.status_var.set(f"Sample preset save failed: {exc}")
            return
        self.status_var.set(f"Saved sample preset: {Path(path).name}")

    def _clear_samples(self) -> None:
        self.sample_regions = []
        self._update_sample_summary()
        self.status_var.set("Cleared guided samples.")

    def _update_sample_summary(self) -> None:
        bg_count = sum(1 for region in self.sample_regions if region.kind == "background")
        keep_count = len(self.sample_regions) - bg_count
        self.sample_summary_var.set(
            f"Samples: {len(self.sample_regions)} | Background: {bg_count} | Keep: {keep_count}"
        )

    def _preview(self) -> None:
        try:
            config = self._build_config()
            service = AlphaFixService(config)
            preview = service.preview(self.input_var.get())
        except Exception as exc:
            messagebox.showerror("Preview failed", str(exc))
            self.status_var.set(f"Preview failed: {exc}")
            return

        self._show_preview(preview)
        self.status_var.set(f"Preview ready in {config.mode} mode.")

    def _show_preview(self, preview: PreviewResult) -> None:
        source_rgb = draw_sample_overlays(
            preview.frame_result.rgba[:, :, :3].copy(),
            tuple(self.sample_regions),
        )
        composite_rgb = self._checkerboard_composite(preview.frame_result.rgba)
        alpha_image = np.clip(preview.frame_result.alpha * 255.0, 0.0, 255.0).astype(np.uint8)
        
        conf_map = preview.frame_result.confidence
        conf_image = np.clip(conf_map * 255.0, 0.0, 255.0).astype(np.uint8)

        self._set_image(self.original_image, source_rgb, "source")
        self._set_image(self.result_image, composite_rgb, "result")
        self._set_image(self.alpha_image, alpha_image, "alpha", grayscale=True)
        self._set_image(self.confidence_image, conf_image, "confidence", grayscale=True)

        # Compute Diagnostics
        alpha = preview.frame_result.alpha
        alpha0 = preview.frame_result.alpha0
        mean_alpha = float(np.mean(alpha))
        mean_conf = float(np.mean(conf_map))
        ambiguity_frac = float(np.mean(conf_map < 0.5))
        correction_impact = float(np.mean(np.abs(alpha - alpha0)))
        bg_count = sum(1 for region in self.sample_regions if region.kind == "background")
        keep_count = len(self.sample_regions) - bg_count

        diag_str = (
            f"Diagnostics | "
            f"Mean Alpha: {mean_alpha:.4f} | "
            f"Mean Confidence: {mean_conf:.4f} | "
            f"Ambiguity Fraction (<0.5): {ambiguity_frac*100:.2f}% | "
            f"Correction Impact: {correction_impact:.4f} | "
            f"Samples: {len(self.sample_regions)} ({bg_count} bg / {keep_count} keep)"
        )
        self.diagnostics_text.config(text=diag_str)

    def _set_image(
        self,
        widget: ttk.Label,
        array: np.ndarray,
        key: str,
        grayscale: bool = False,
    ) -> None:
        image = Image.fromarray(array if not grayscale else array, mode=None)
        image.thumbnail((320, 320), Image.Resampling.LANCZOS)
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
            config = self._build_config()
            input_path = self.input_var.get().strip()
            output_path = self.output_var.get().strip()
            if not input_path:
                raise ValueError("Choose an input file before exporting.")
            if not output_path:
                raise ValueError("Choose an output folder before exporting.")
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        self.status_var.set("Export started...")
        thread = threading.Thread(
            target=self._run_export,
            args=(config, input_path, output_path),
            daemon=True,
        )
        thread.start()

    def _run_export(self, config: AlphaFixConfig, input_path: str, output_path: str) -> None:
        service = AlphaFixService(config)

        def on_progress(done: int, total: int) -> None:
            self.after(0, lambda: self.status_var.set(f"Exporting frame {done}/{total}..."))

        try:
            summary = service.export_sequence(input_path, output_path, progress_callback=on_progress)
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: messagebox.showerror("Export failed", msg))
            self.after(0, lambda: self.status_var.set(f"Export failed: {msg}"))
            return

        self.after(0, lambda: self._finish_export(summary))

    def _finish_export(self, summary: ExportSummary) -> None:
        video_line = ""
        if summary.video_artifact is not None:
            video_line = f"\n\nMedia file:\n- {summary.video_artifact.output_path.name}"
        self.status_var.set(
            f"Export complete: {summary.frame_count} frame(s) to {summary.output_dir} in {summary.mode} mode."
        )
        messagebox.showinfo(
            "Export complete",
            f"Saved {summary.frame_count} frame(s) to:\n{summary.output_dir}\n\nFiles are written into:\n- rgba\n- alpha{video_line}",
        )

    def _build_config(self) -> AlphaFixConfig:
        return AlphaFixConfig(
            mode=self.mode_var.get(),
            overlay_method=self.overlay_method_var.get(),
            border_width=int(self.border_width_var.get()),
            border_clusters=int(self.border_clusters_var.get()),
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
            export_format=self.export_format_var.get(),
            sample_regions=tuple(self.sample_regions),
            sdr_enabled=bool(self.sdr_enabled_var.get()),
            sdr_k=float(self.sdr_k_var.get()),
            sdr_sigma=float(self.sdr_sigma_var.get()),
        )


def launch_gui() -> None:
    try:
        app = AlphaFixGUI()
        app.mainloop()
    except Exception as exc:
        report_gui_exception("Alpha Fix", exc)
