# Alpha Fix Source Bundle

Generated for sharing with Perplexity.

Included files:
- `pyproject.toml`
- `README.md`
- `Alpha Fix.bat`
- `Alpha Fix Sandbox.bat`
- `Alpha Fix.vbs`
- `Alpha Fix Sandbox.vbs`
- `Install Shortcuts.ps1`
- `alpha_fix\__init__.py`
- `alpha_fix\__main__.py`
- `alpha_fix\cli.py`
- `alpha_fix\config.py`
- `alpha_fix\error_report.py`
- `alpha_fix\gui.py`
- `alpha_fix\pipeline.py`
- `alpha_fix\samples.py`
- `alpha_fix\sample_editor.py`
- `alpha_fix\service.py`
- `alpha_fix_2\__init__.py`
- `alpha_fix_2\__main__.py`
- `alpha_fix_2\cli.py`
- `alpha_fix_2\config.py`
- `alpha_fix_2\gui.py`
- `alpha_fix_2\pipeline.py`
- `alpha_fix_2\service.py`
- `tests\test_pipeline.py`
- `tests\test_sandbox_pipeline.py`

## pyproject.toml

````toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "alpha-fix"
version = "0.1.0"
description = "Production and sandbox desktop apps for extracting OBS-ready subject and overlay mattes from video."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "numpy>=2.1,<3",
  "opencv-python>=4.10,<5",
  "Pillow>=11,<12",
]

[project.scripts]
alpha-fix = "alpha_fix.cli:main"
alpha-fix-2 = "alpha_fix_2.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["alpha_fix", "alpha_fix_2"]

````

## README.md

````markdown
# Alpha Fix

Alpha Fix now has two parallel desktop apps inside this folder:

- `alpha_fix`: stable operator-facing branch.
- `alpha_fix_2`: sandbox branch for aggressive experimentation and debug-heavy previews.

Both apps are Python/OpenCV desktop tools for extracting OBS-ready overlays from stills or video.

## Branch Roles

`alpha_fix` keeps the conservative live workflow:

- `subject` mode uses a border-palette anchor matte plus EMA and LIPC.
- `overlay` mode uses the existing CHHC hole-carving path.
- guided samples can now be drawn on the first frame and saved as JSON presets.

`alpha_fix_2` is the experimental branch:

- keeps the same subject baseline
- adds sandbox-only overlay method switching
- includes an `auto_hole` overlay experiment with hole-discovery debug views

## Run

```powershell
uv sync
uv run alpha-fix --gui
uv run alpha-fix-2 --gui
```

## Open Like An App

After `uv sync`, you can launch either app by double-clicking:

- `Alpha Fix.vbs` or `Alpha Fix.lnk`
- `Alpha Fix Sandbox.vbs` or `Alpha Fix Sandbox.lnk`

If the `.lnk` shortcuts are missing, run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\Install Shortcuts.ps1"
```

CLI export examples:

```powershell
uv run alpha-fix --input "input.mp4" --output ".\\exports" --mode subject
uv run alpha-fix --input "input.png" --output ".\\exports" --mode overlay --sample-preset ".\\samples.json"
uv run alpha-fix-2 --input "input.mp4" --output ".\\sandbox_exports" --mode overlay --overlay-method auto_hole
```

## Notes

- This is still a reconstructed codebase built from the research and history files, not the original recovered repo.
- Production and sandbox are intentionally split so experiments can move fast without destabilizing the operator path.

````

## Alpha Fix.bat

````bat
@echo off
cd /d "%~dp0"
echo Starting Alpha Fix Production...
uv run python -m alpha_fix --gui

````

## Alpha Fix Sandbox.bat

````bat
@echo off
cd /d "%~dp0"
echo Starting Alpha Fix Sandbox...
uv run python -m alpha_fix_2 --gui

````

## Alpha Fix.vbs

````vb
Option Explicit

Dim shell
Dim fso
Dim root
Dim pythonw
Dim command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    MsgBox "Alpha Fix is not installed in the local .venv yet." & vbCrLf & _
        "Run 'uv sync' in this folder first.", vbExclamation, "Alpha Fix"
    WScript.Quit 1
End If

shell.CurrentDirectory = root
command = """" & pythonw & """ -m alpha_fix.cli --gui"
shell.Run command, 1, False

````

## Alpha Fix Sandbox.vbs

````vb
Option Explicit

Dim shell
Dim fso
Dim root
Dim pythonw
Dim command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    MsgBox "Alpha Fix Sandbox is not installed in the local .venv yet." & vbCrLf & _
        "Run 'uv sync' in this folder first.", vbExclamation, "Alpha Fix Sandbox"
    WScript.Quit 1
End If

shell.CurrentDirectory = root
command = """" & pythonw & """ -m alpha_fix_2.cli --gui"
shell.Run command, 1, False

````

## Install Shortcuts.ps1

````powershell
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $root ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $pythonw)) {
    throw "Missing $pythonw. Run 'uv sync' in this folder first."
}

$shell = New-Object -ComObject WScript.Shell

$definitions = @(
    @{
        Shortcut = Join-Path $root "Alpha Fix.lnk"
        Target = $pythonw
        Arguments = "-m alpha_fix.cli --gui"
        Description = "Launch Alpha Fix production app"
    },
    @{
        Shortcut = Join-Path $root "Alpha Fix Sandbox.lnk"
        Target = $pythonw
        Arguments = "-m alpha_fix_2.cli --gui"
        Description = "Launch Alpha Fix sandbox app"
    }
)

foreach ($item in $definitions) {
    if (Test-Path $item.Shortcut) {
        Remove-Item $item.Shortcut -Force
    }
    $shortcut = $shell.CreateShortcut($item.Shortcut)
    $shortcut.TargetPath = $item.Target
    $shortcut.Arguments = $item.Arguments
    $shortcut.WorkingDirectory = $root
    $shortcut.IconLocation = "$pythonw,0"
    $shortcut.Description = $item.Description
    $shortcut.Save()
}

Write-Host "Created shortcuts in $root"

````

## alpha_fix\__init__.py

````python
from .config import AlphaFixConfig
from .pipeline import AlphaFixProcessor, FrameResult
from .samples import SampleRegion
from .service import AlphaFixService, ExportSummary, PreviewResult

__all__ = [
    "AlphaFixConfig",
    "AlphaFixProcessor",
    "AlphaFixService",
    "ExportSummary",
    "FrameResult",
    "PreviewResult",
    "SampleRegion",
]

````

## alpha_fix\__main__.py

````python
from .cli import main


if __name__ == "__main__":
    main()

````

## alpha_fix\cli.py

````python
from __future__ import annotations

import argparse
from pathlib import Path

from .config import AlphaFixConfig
from .samples import load_sample_regions
from .service import AlphaFixService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alpha Fix desktop MVP.")
    parser.add_argument("--gui", action="store_true", help="Launch the desktop GUI.")
    parser.add_argument("--input", help="Input image or video path.")
    parser.add_argument("--output", help="Output directory for exported PNG frames.")
    parser.add_argument("--mode", choices=("subject", "overlay"), default="overlay")
    parser.add_argument("--overlay-method", choices=("auto_hole", "chhc"), default="auto_hole")
    parser.add_argument("--border-width", type=int, default=12)
    parser.add_argument("--border-clusters", type=int, default=3)
    parser.add_argument("--subject-low", type=float, default=1.4)
    parser.add_argument("--subject-high", type=float, default=4.5)
    parser.add_argument("--overlay-low", type=float, default=0.3)
    parser.add_argument("--overlay-high", type=float, default=2.3)
    parser.add_argument("--lipc-lambda", type=float, default=0.65)
    parser.add_argument("--lipc-delta", type=float, default=0.35)
    parser.add_argument("--lipc-luma", type=float, default=0.80)
    parser.add_argument("--chhc-alpha", type=float, default=0.12)
    parser.add_argument("--chhc-close", type=int, default=5)
    parser.add_argument("--chhc-min-hole", type=float, default=0.03)
    parser.add_argument("--chhc-margin", type=float, default=0.05)
    parser.add_argument("--sample-preset", help="JSON file with guided sample regions.")
    parser.add_argument("--sdr-enabled", action="store_true", help="Enable SDR-Pow method.")
    parser.add_argument("--sdr-k", type=float, default=0.6)
    parser.add_argument("--sdr-sigma", type=float, default=1.5)
    parser.add_argument(
        "--no-alpha-matte",
        action="store_true",
        help="Skip grayscale alpha matte exports.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui or not args.input:
        from .gui import launch_gui

        launch_gui()
        return

    if not args.output:
        parser.error("--output is required when --input is provided without --gui.")

    sample_regions = ()
    if args.sample_preset:
        sample_regions = tuple(load_sample_regions(args.sample_preset))

    config = AlphaFixConfig(
        mode=args.mode,
        overlay_method=args.overlay_method,
        border_width=args.border_width,
        border_clusters=args.border_clusters,
        subject_low=args.subject_low,
        subject_high=args.subject_high,
        overlay_low=args.overlay_low,
        overlay_high=args.overlay_high,
        lipc_lambda=args.lipc_lambda,
        lipc_t_delta=args.lipc_delta,
        lipc_t_luma=args.lipc_luma,
        chhc_t_alpha=args.chhc_alpha,
        chhc_close_kernel=args.chhc_close,
        chhc_min_hole_frac=args.chhc_min_hole,
        chhc_valid_margin=float(args.chhc_margin),
        sample_regions=sample_regions,
        sdr_enabled=args.sdr_enabled,
        sdr_k=args.sdr_k,
        sdr_sigma=args.sdr_sigma,
        export_alpha_matte=not args.no_alpha_matte,
    )

    service = AlphaFixService(config)

    def progress(done: int, total: int) -> None:
        print(f"[{done}/{total}] processing", flush=True)

    summary = service.export_sequence(
        Path(args.input),
        Path(args.output),
        progress_callback=progress,
    )
    print(
        f"Exported {summary.frame_count} frame(s) to {summary.output_dir} in {summary.mode} mode.",
        flush=True,
    )

````

## alpha_fix\config.py

````python
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from .samples import SampleRegion

Mode = Literal["subject", "overlay"]
OverlayMethod = Literal["auto_hole", "chhc"]


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

````

## alpha_fix\error_report.py

````python
from __future__ import annotations

import ctypes
import traceback
from pathlib import Path


def report_gui_exception(app_name: str, exc: BaseException, tb: object | None = None) -> None:
    trace = "".join(traceback.format_exception(type(exc), exc, tb or exc.__traceback__))
    log_name = app_name.lower().replace(" ", "_") + "_startup.log"
    log_path = Path.cwd() / log_name
    log_path.write_text(trace, encoding="utf-8")
    ctypes.windll.user32.MessageBoxW(
        0,
        f"{app_name} failed to start.\n\nDetails were written to:\n{log_path}",
        app_name,
        0x10,
    )

````

## alpha_fix\gui.py

````python
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

        ttk.Button(workflow_frame, text="Preview Current File", command=self._preview).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(workflow_frame, text="Process To Output Folder", command=self._export).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(workflow_frame, text="Open Output Folder", command=self._open_output_folder).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
        )
        ttk.Label(
            workflow_frame,
            text="Workflow: choose an input file, choose an output folder, then press Process To Output Folder. Exports are written into rgba and alpha subfolders.",
            wraplength=310,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

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
            self.after(0, lambda: messagebox.showerror("Export failed", str(exc)))
            self.after(0, lambda: self.status_var.set(f"Export failed: {exc}"))
            return

        self.after(0, lambda: self._finish_export(summary))

    def _finish_export(self, summary: ExportSummary) -> None:
        self.status_var.set(
            f"Export complete: {summary.frame_count} frame(s) to {summary.output_dir} in {summary.mode} mode."
        )
        messagebox.showinfo(
            "Export complete",
            f"Saved {summary.frame_count} frame(s) to:\n{summary.output_dir}\n\nFiles are written into:\n- rgba\n- alpha",
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

````

## alpha_fix\pipeline.py

````python
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .config import AlphaFixConfig
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
            if self.config.overlay_method == "auto_hole":
                alpha = self._apply_auto_hole(alpha0, frame_bgr, self.config)
            else:
                alpha = (
                    self._apply_chhc(alpha0, frame_bgr, self.config)
                    if self.config.chhc_enabled
                    else alpha0
                )
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

        frame_mask = (closed > 0) & (hole_mask == 0)
        dist_inside = cv2.distanceTransform(frame_mask.astype(np.uint8) * 255, cv2.DIST_L2, 3)

        alpha_overlay = np.zeros((height, width), dtype=np.float32)
        alpha_overlay[dist_inside > cfg.chhc_feather_r] = 1.0
        feather_zone = (dist_inside > 0) & (dist_inside <= cfg.chhc_feather_r)
        alpha_overlay[feather_zone] = dist_inside[feather_zone] / max(cfg.chhc_feather_r, 1e-6)
        return np.clip(alpha_overlay, 0.0, 1.0).astype(np.float32)

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

        hole_mask = self._grow_holes(gray, frame_fill, seeds, cfg)
        if not np.any(hole_mask):
            return self._apply_chhc(alpha0, frame_bgr, cfg)

        solid_mask = frame_fill & ~hole_mask
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

    @staticmethod
    def _rgba_from_alpha(frame_bgr: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
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

````

## alpha_fix\samples.py

````python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

SampleKind = Literal["background", "keep"]
SampleShape = Literal["rectangle", "ellipse"]


@dataclass(slots=True, frozen=True)
class SampleRegion:
    kind: SampleKind
    shape: SampleShape
    x0: float
    y0: float
    x1: float
    y1: float

    def normalized(self) -> "SampleRegion":
        x0 = float(np.clip(min(self.x0, self.x1), 0.0, 1.0))
        y0 = float(np.clip(min(self.y0, self.y1), 0.0, 1.0))
        x1 = float(np.clip(max(self.x0, self.x1), 0.0, 1.0))
        y1 = float(np.clip(max(self.y0, self.y1), 0.0, 1.0))
        return SampleRegion(self.kind, self.shape, x0, y0, x1, y1)

    def to_dict(self) -> dict[str, float | str]:
        region = self.normalized()
        return {
            "kind": region.kind,
            "shape": region.shape,
            "x0": region.x0,
            "y0": region.y0,
            "x1": region.x1,
            "y1": region.y1,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SampleRegion":
        kind = str(data["kind"])
        shape = str(data["shape"])
        if kind not in {"background", "keep"}:
            raise ValueError(f"Unsupported sample kind: {kind}")
        if shape not in {"rectangle", "ellipse"}:
            raise ValueError(f"Unsupported sample shape: {shape}")
        return cls(
            kind=kind,
            shape=shape,
            x0=float(data["x0"]),
            y0=float(data["y0"]),
            x1=float(data["x1"]),
            y1=float(data["y1"]),
        ).normalized()


def save_sample_regions(path: str | Path, sample_regions: list[SampleRegion] | tuple[SampleRegion, ...]) -> None:
    payload = {
        "version": 1,
        "sample_regions": [region.to_dict() for region in sample_regions],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_sample_regions(path: str | Path) -> list[SampleRegion]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    regions = payload.get("sample_regions", [])
    return [SampleRegion.from_dict(item) for item in regions]


def collect_sample_pixels(image: np.ndarray, sample_regions: tuple[SampleRegion, ...], kind: SampleKind) -> np.ndarray:
    mask = build_sample_mask(image.shape[:2], sample_regions, kind)
    if not np.any(mask > 0.0):
        return np.empty((0, image.shape[-1]), dtype=np.float32)
    return image[mask > 0.5].reshape(-1, image.shape[-1]).astype(np.float32)


def build_sample_mask(
    image_shape: tuple[int, int],
    sample_regions: tuple[SampleRegion, ...],
    kind: SampleKind,
) -> np.ndarray:
    height, width = image_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    for region in sample_regions:
        region = region.normalized()
        if region.kind != kind:
            continue
        x0, y0, x1, y1 = region_bounds(region, width, height)
        if x1 <= x0 or y1 <= y0:
            continue
        if region.shape == "ellipse":
            center = ((x0 + x1) // 2, (y0 + y1) // 2)
            axes = (max(1, (x1 - x0) // 2), max(1, (y1 - y0) // 2))
            cv2.ellipse(mask, center, axes, 0.0, 0.0, 360.0, 255, cv2.FILLED)
        else:
            cv2.rectangle(mask, (x0, y0), (x1, y1), 255, cv2.FILLED)
    if int(mask.max()) == 0:
        return np.zeros((height, width), dtype=np.float32)
    smooth = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (0, 0), 1.2)
    return np.clip(smooth, 0.0, 1.0).astype(np.float32)


def draw_sample_overlays(image_rgb: np.ndarray, sample_regions: tuple[SampleRegion, ...]) -> np.ndarray:
    if len(sample_regions) == 0:
        return image_rgb
    overlay = image_rgb.copy()
    height, width = overlay.shape[:2]
    for region in sample_regions:
        region = region.normalized()
        x0, y0, x1, y1 = region_bounds(region, width, height)
        color = (235, 76, 64) if region.kind == "background" else (56, 196, 110)
        if region.shape == "ellipse":
            center = ((x0 + x1) // 2, (y0 + y1) // 2)
            axes = (max(1, (x1 - x0) // 2), max(1, (y1 - y0) // 2))
            cv2.ellipse(overlay, center, axes, 0.0, 0.0, 360.0, color, 2)
        else:
            cv2.rectangle(overlay, (x0, y0), (x1, y1), color, 2)
    return overlay


def region_bounds(region: SampleRegion, width: int, height: int) -> tuple[int, int, int, int]:
    normalized = region.normalized()
    x0 = int(round(normalized.x0 * (width - 1)))
    y0 = int(round(normalized.y0 * (height - 1)))
    x1 = int(round(normalized.x1 * (width - 1)))
    y1 = int(round(normalized.y1 * (height - 1)))
    return x0, y0, x1, y1

````

## alpha_fix\sample_editor.py

````python
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from .samples import SampleRegion, SampleShape, draw_sample_overlays


class SampleEditorDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        frame_bgr: np.ndarray,
        sample_regions: list[SampleRegion],
    ) -> None:
        super().__init__(parent)
        self.title("Guided Samples")
        self.transient(parent)
        self.grab_set()
        self.geometry("1280x860")
        self.minsize(980, 720)

        self.result: list[SampleRegion] | None = None
        self._frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._sample_regions = [region.normalized() for region in sample_regions]
        self._display_width, self._display_height = self._fit_display_size(self._frame_rgb.shape[1], self._frame_rgb.shape[0])
        self._photo: ImageTk.PhotoImage | None = None
        self._drag_start: tuple[int, int] | None = None
        self._preview_item: int | None = None
        self._image_item: int | None = None

        self.kind_var = tk.StringVar(value="background")
        self.shape_var = tk.StringVar(value="rectangle")
        self.summary_var = tk.StringVar()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)
        container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            container,
            width=self._display_width,
            height=self._display_height,
            background="#1f1f1f",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        side = ttk.Frame(container)
        side.grid(row=0, column=1, sticky="ns")
        side.columnconfigure(0, weight=1)

        ttk.Label(side, text="Sample Kind").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            side,
            textvariable=self.kind_var,
            values=("background", "keep"),
            state="readonly",
            width=18,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(side, text="Shape").grid(row=2, column=0, sticky="w")
        ttk.Combobox(
            side,
            textvariable=self.shape_var,
            values=("rectangle", "ellipse"),
            state="readonly",
            width=18,
        ).grid(row=3, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(
            side,
            text="Drag on the frame to create a region. Background regions are red, keep regions are green.",
            wraplength=240,
        ).grid(row=4, column=0, sticky="w", pady=(0, 12))

        self.region_list = tk.Listbox(side, width=36, height=18)
        self.region_list.grid(row=5, column=0, sticky="ew")

        ttk.Label(side, textvariable=self.summary_var, wraplength=240).grid(
            row=6,
            column=0,
            sticky="w",
            pady=(8, 12),
        )

        ttk.Button(side, text="Delete Selected", command=self._delete_selected).grid(
            row=7,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(side, text="Clear All", command=self._clear_all).grid(
            row=8,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(side, text="Done", command=self._finish).grid(
            row=9,
            column=0,
            sticky="ew",
            pady=(16, 8),
        )
        ttk.Button(side, text="Cancel", command=self._cancel).grid(
            row=10,
            column=0,
            sticky="ew",
        )

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._refresh()

    @staticmethod
    def _fit_display_size(width: int, height: int) -> tuple[int, int]:
        max_width = 900
        max_height = 720
        scale = min(max_width / max(width, 1), max_height / max(height, 1), 1.0)
        return max(1, int(round(width * scale))), max(1, int(round(height * scale)))

    def _refresh(self) -> None:
        image = draw_sample_overlays(self._frame_rgb.copy(), tuple(self._sample_regions))
        pil_image = Image.fromarray(image)
        pil_image = pil_image.resize((self._display_width, self._display_height), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(pil_image)

        self.canvas.delete("all")
        self._image_item = self.canvas.create_image(0, 0, anchor="nw", image=self._photo)
        self._sync_region_list()

    def _sync_region_list(self) -> None:
        self.region_list.delete(0, tk.END)
        bg_count = 0
        keep_count = 0
        for idx, region in enumerate(self._sample_regions, start=1):
            if region.kind == "background":
                bg_count += 1
            else:
                keep_count += 1
            label = f"{idx:02d}. {region.kind} {region.shape} ({region.x0:.2f},{region.y0:.2f})-({region.x1:.2f},{region.y1:.2f})"
            self.region_list.insert(tk.END, label)
        self.summary_var.set(f"Total: {len(self._sample_regions)} | Background: {bg_count} | Keep: {keep_count}")

    def _image_to_normalized(self, x: int, y: int) -> tuple[float, float]:
        nx = float(np.clip(x / max(self._display_width - 1, 1), 0.0, 1.0))
        ny = float(np.clip(y / max(self._display_height - 1, 1), 0.0, 1.0))
        return nx, ny

    def _on_press(self, event: tk.Event[tk.Misc]) -> None:
        self._drag_start = (
            int(np.clip(event.x, 0, self._display_width - 1)),
            int(np.clip(event.y, 0, self._display_height - 1)),
        )
        if self._preview_item is not None:
            self.canvas.delete(self._preview_item)
            self._preview_item = None

    def _on_drag(self, event: tk.Event[tk.Misc]) -> None:
        if self._drag_start is None:
            return
        x0, y0 = self._drag_start
        x1 = int(np.clip(event.x, 0, self._display_width - 1))
        y1 = int(np.clip(event.y, 0, self._display_height - 1))
        if self._preview_item is not None:
            self.canvas.delete(self._preview_item)
        color = "#eb4c40" if self.kind_var.get() == "background" else "#38c46e"
        if self.shape_var.get() == "ellipse":
            self._preview_item = self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=2, dash=(4, 2))
        else:
            self._preview_item = self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, dash=(4, 2))

    def _on_release(self, event: tk.Event[tk.Misc]) -> None:
        if self._drag_start is None:
            return
        x0, y0 = self._drag_start
        x1 = int(np.clip(event.x, 0, self._display_width - 1))
        y1 = int(np.clip(event.y, 0, self._display_height - 1))
        self._drag_start = None
        if self._preview_item is not None:
            self.canvas.delete(self._preview_item)
            self._preview_item = None
        if abs(x1 - x0) < 6 or abs(y1 - y0) < 6:
            return

        nx0, ny0 = self._image_to_normalized(x0, y0)
        nx1, ny1 = self._image_to_normalized(x1, y1)
        region = SampleRegion(
            kind=self.kind_var.get(),
            shape=self.shape_var.get(),
            x0=nx0,
            y0=ny0,
            x1=nx1,
            y1=ny1,
        ).normalized()
        self._sample_regions.append(region)
        self._refresh()

    def _delete_selected(self) -> None:
        selection = self.region_list.curselection()
        if not selection:
            return
        index = int(selection[0])
        del self._sample_regions[index]
        self._refresh()

    def _clear_all(self) -> None:
        self._sample_regions.clear()
        self._refresh()

    def _finish(self) -> None:
        self.result = list(self._sample_regions)
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()

````

## alpha_fix\service.py

````python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from .config import AlphaFixConfig
from .pipeline import AlphaFixProcessor, FrameResult

ProgressCallback = Callable[[int, int], None]


@dataclass(slots=True)
class PreviewResult:
    input_path: Path
    frame_bgr: np.ndarray
    frame_result: FrameResult


@dataclass(slots=True)
class ExportSummary:
    input_path: Path
    output_dir: Path
    frame_count: int
    fps: float
    mode: str


class AlphaFixService:
    def __init__(self, config: AlphaFixConfig) -> None:
        self.config = config

    def load_input_frame(self, input_path: str | Path) -> np.ndarray:
        return self._read_first_frame(Path(input_path))

    def preview(self, input_path: str | Path) -> PreviewResult:
        path = Path(input_path)
        frame = self.load_input_frame(path)
        processor = AlphaFixProcessor(self.config)
        result = processor.process_frame(frame)
        return PreviewResult(path, frame, result)

    def export_sequence(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        progress_callback: ProgressCallback | None = None,
    ) -> ExportSummary:
        source = Path(input_path)
        target = Path(output_dir)
        rgba_dir = target / "rgba"
        matte_dir = target / "alpha"
        rgba_dir.mkdir(parents=True, exist_ok=True)
        if self.config.export_alpha_matte:
            matte_dir.mkdir(parents=True, exist_ok=True)

        processor = AlphaFixProcessor(self.config)
        prev_alpha: np.ndarray | None = None

        if self._is_image(source):
            frame = self._read_image(source)
            result = processor.process_frame(frame)
            self._write_frame_outputs(result, rgba_dir, matte_dir, 0)
            if progress_callback is not None:
                progress_callback(1, 1)
            return ExportSummary(source, target, 1, 1.0, self.config.mode)

        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise FileNotFoundError(f"Unable to open input: {source}")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_count = 0

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                result = processor.process_frame(frame, prev_alpha=prev_alpha)
                self._write_frame_outputs(result, rgba_dir, matte_dir, frame_count)
                if self.config.mode == "subject":
                    prev_alpha = result.alpha_ema
                frame_count += 1

                if progress_callback is not None:
                    callback_total = total_frames if total_frames > 0 else frame_count
                    progress_callback(frame_count, callback_total)
        finally:
            capture.release()

        return ExportSummary(source, target, frame_count, fps, self.config.mode)

    @staticmethod
    def _is_image(path: Path) -> bool:
        return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    def _read_first_frame(self, path: Path) -> np.ndarray:
        if self._is_image(path):
            return self._read_image(path)

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise FileNotFoundError(f"Unable to open input: {path}")

        try:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Unable to read first frame from: {path}")
            return frame
        finally:
            capture.release()

    @staticmethod
    def _read_image(path: Path) -> np.ndarray:
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is None:
            raise FileNotFoundError(f"Unable to open image: {path}")
        return frame

    def _write_frame_outputs(
        self,
        result: FrameResult,
        rgba_dir: Path,
        matte_dir: Path,
        frame_index: int,
    ) -> None:
        rgba_path = rgba_dir / f"frame_{frame_index:05d}.png"
        rgba_bgra = cv2.cvtColor(result.rgba, cv2.COLOR_RGBA2BGRA)
        if not cv2.imwrite(str(rgba_path), rgba_bgra):
            raise IOError(f"Failed to write image to {rgba_path}")

        if self.config.export_alpha_matte:
            matte_path = matte_dir / f"alpha_{frame_index:05d}.png"
            alpha_u8 = np.clip(result.alpha * 255.0, 0.0, 255.0).astype(np.uint8)
            if not cv2.imwrite(str(matte_path), alpha_u8):
                raise IOError(f"Failed to write image to {matte_path}")

````

## alpha_fix_2\__init__.py

````python
from .config import AlphaFix2Config
from .pipeline import AlphaFix2Processor, FrameResult
from .service import AlphaFix2Service, ExportSummary, PreviewResult

__all__ = [
    "AlphaFix2Config",
    "AlphaFix2Processor",
    "AlphaFix2Service",
    "ExportSummary",
    "FrameResult",
    "PreviewResult",
]

````

## alpha_fix_2\__main__.py

````python
from .cli import main


if __name__ == "__main__":
    main()

````

## alpha_fix_2\cli.py

````python
from __future__ import annotations

import argparse
from pathlib import Path

from .config import AlphaFix2Config
from .service import AlphaFix2Service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alpha Fix sandbox desktop app.")
    parser.add_argument("--gui", action="store_true", help="Launch the sandbox GUI.")
    parser.add_argument("--input", help="Input image or video path.")
    parser.add_argument("--output", help="Output directory for exported PNG frames.")
    parser.add_argument("--mode", choices=("subject", "overlay"), default="overlay")
    parser.add_argument("--overlay-method", choices=("auto_hole", "chhc"), default="auto_hole")
    parser.add_argument("--border-width", type=int, default=12)
    parser.add_argument("--border-clusters", type=int, default=3)
    parser.add_argument("--anchor-blend", type=float, default=0.0)
    parser.add_argument("--subject-low", type=float, default=1.4)
    parser.add_argument("--subject-high", type=float, default=4.5)
    parser.add_argument("--overlay-low", type=float, default=0.3)
    parser.add_argument("--overlay-high", type=float, default=2.3)
    parser.add_argument("--lipc-lambda", type=float, default=0.65)
    parser.add_argument("--lipc-delta", type=float, default=0.35)
    parser.add_argument("--lipc-luma", type=float, default=0.80)
    parser.add_argument("--chhc-alpha", type=float, default=0.12)
    parser.add_argument("--chhc-close", type=int, default=5)
    parser.add_argument("--chhc-min-hole", type=float, default=0.03)
    parser.add_argument("--chhc-margin", type=float, default=0.05)
    parser.add_argument("--hole-dark-max", type=float, default=0.18)
    parser.add_argument("--hole-flat-max", type=float, default=0.035)
    parser.add_argument("--hole-min-area", type=float, default=0.01)
    parser.add_argument("--hole-seed-dist", type=float, default=8.0)
    parser.add_argument("--hole-flood-tol", type=int, default=18)
    parser.add_argument("--hole-margin", type=float, default=0.05)
    parser.add_argument("--sdr-enabled", action="store_true", help="Enable SDR-Pow method.")
    parser.add_argument("--sdr-k", type=float, default=0.6)
    parser.add_argument("--sdr-sigma", type=float, default=1.5)
    parser.add_argument("--osa-enabled", action="store_true", help="Enable OSA-v2 method.")
    parser.add_argument("--osa-mode", choices=("HTP", "lite"), default="HTP")
    parser.add_argument("--osa-pivot", type=float, default=0.50)
    parser.add_argument("--osa-kappa", type=float, default=2.5)
    parser.add_argument("--osa-r", type=float, default=2.5)
    parser.add_argument("--osa-sigma", type=float, default=2.0)
    parser.add_argument("--osa-omega", type=float, default=4.0)
    parser.add_argument("--osa-lam", type=float, default=5.0)
    parser.add_argument(
        "--no-alpha-matte",
        action="store_true",
        help="Skip grayscale alpha matte exports.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui or not args.input:
        from .gui import launch_gui

        launch_gui()
        return

    if not args.output:
        parser.error("--output is required when --input is provided without --gui.")

    config = AlphaFix2Config(
        mode=args.mode,
        overlay_method=args.overlay_method,
        border_width=args.border_width,
        border_clusters=args.border_clusters,
        anchor_blend=args.anchor_blend,
        subject_low=args.subject_low,
        subject_high=args.subject_high,
        overlay_low=args.overlay_low,
        overlay_high=args.overlay_high,
        lipc_lambda=args.lipc_lambda,
        lipc_t_delta=args.lipc_delta,
        lipc_t_luma=args.lipc_luma,
        chhc_t_alpha=args.chhc_alpha,
        chhc_close_kernel=args.chhc_close,
        chhc_min_hole_frac=args.chhc_min_hole,
        chhc_valid_margin=args.chhc_margin,
        hole_dark_max=args.hole_dark_max,
        hole_flat_max=args.hole_flat_max,
        hole_min_area_frac=args.hole_min_area,
        hole_seed_min_dist=args.hole_seed_dist,
        hole_flood_tol=args.hole_flood_tol,
        hole_margin_frac=args.hole_margin,
        sdr_enabled=args.sdr_enabled,
        sdr_k=args.sdr_k,
        sdr_sigma=args.sdr_sigma,
        osa_enabled=args.osa_enabled,
        osa_mode=args.osa_mode,
        osa_pivot=args.osa_pivot,
        osa_kappa=args.osa_kappa,
        osa_R=args.osa_r,
        osa_sigma=args.osa_sigma,
        osa_omega=args.osa_omega,
        osa_lam=args.osa_lam,
        export_alpha_matte=not args.no_alpha_matte,
    )

    service = AlphaFix2Service(config)

    def progress(done: int, total: int) -> None:
        print(f"[{done}/{total}] sandbox processing", flush=True)

    summary = service.export_sequence(
        Path(args.input),
        Path(args.output),
        progress_callback=progress,
    )
    print(
        f"Sandbox exported {summary.frame_count} frame(s) to {summary.output_dir} in {summary.mode} mode.",
        flush=True,
    )

````

## alpha_fix_2\config.py

````python
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from alpha_fix.samples import SampleRegion

Mode = Literal["subject", "overlay"]
OverlayMethod = Literal["chhc", "auto_hole"]


@dataclass(slots=True)
class AlphaFix2Config:
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
    chhc_feather_r: float = 2.5

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

    osa_enabled: bool = False
    osa_mode: Literal["HTP", "lite"] = "HTP"
    osa_pivot: float = 0.50
    osa_kappa: float = 2.5
    osa_R: float = 2.5
    osa_sigma: float = 2.0
    osa_omega: float = 4.0
    osa_lam: float = 5.0

    def updated(self, **overrides: object) -> "AlphaFix2Config":
        return replace(self, **overrides)

````

## alpha_fix_2\gui.py

````python
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk

from alpha_fix.error_report import report_gui_exception

from .config import AlphaFix2Config
from .service import AlphaFix2Service, ExportSummary, PreviewResult


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
        self.export_format_var = tk.StringVar(value="chroma_mp4")

        self.border_width_var = tk.IntVar(value=12)
        self.border_clusters_var = tk.IntVar(value=3)
        self.anchor_blend_var = tk.DoubleVar(value=0.0)
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

        self._preview_refs: dict[str, ImageTk.PhotoImage] = {}
        self._panel_widgets: dict[str, ttk.Label] = {}

        self._build_layout()

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
            values=("auto_hole", "chhc"),
            state="readonly",
            width=18,
        ).grid(row=7, column=0, sticky="w")

        ttk.Separator(controls).grid(row=8, column=0, columnspan=2, sticky="ew", pady=14)

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
            ("SDR K", self.sdr_k_var),
            ("SDR Sigma", self.sdr_sigma_var),
            ("OSA Pivot", self.osa_pivot_var),
            ("OSA Kappa", self.osa_kappa_var),
            ("OSA R", self.osa_R_var),
            ("OSA Sigma", self.osa_sigma_var),
            ("OSA Omega", self.osa_omega_var),
            ("OSA Lam", self.osa_lam_var),
        ]

        row = 9
        for label, variable in numeric_fields:
            ttk.Label(controls, text=label).grid(row=row, column=0, sticky="w", pady=(0, 2))
            ttk.Entry(controls, width=12, textvariable=variable).grid(row=row, column=1, sticky="w", padx=(8, 0))
            row += 1

        ttk.Checkbutton(controls, text="Enable SDR-Pow", variable=self.sdr_enabled_var).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 2),
        )
        row += 1

        ttk.Checkbutton(controls, text="Enable OSA-v2", variable=self.osa_enabled_var).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(2, 8),
        )
        ttk.Combobox(
            controls,
            textvariable=self.osa_mode_var,
            values=("HTP", "lite"),
            state="readonly",
            width=8,
        ).grid(row=row, column=1, sticky="w", pady=(2, 8))
        row += 1

        ttk.Label(
            controls,
            text="Sandbox branch: experimental controls and debug views may change between passes.",
            wraplength=320,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 12))
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
        self.diagnostics_text.grid(row=4, column=0, columnspan=4, sticky="w", pady=(8, 0))

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
            self._update_timeline_limits(path)

    def _update_timeline_limits(self, path: str) -> None:
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

    def _preview(self) -> None:
        try:
            config = self._build_config()
            service = AlphaFix2Service(config)
            preview = service.preview(self.input_var.get(), frame_index=self.frame_index_var.get())
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
        source_rgb = result.rgba[:, :, :3]
        composite_rgb = self._checkerboard_composite(result.rgba)
        alpha_image = np.clip(result.alpha * 255.0, 0.0, 255.0).astype(np.uint8)
        anchor_image = np.clip(result.alpha0 * 255.0, 0.0, 255.0).astype(np.uint8)
        void_image = self._debug_image(result.debug_views.get("void_mask"), alpha_image.shape)
        seed_image = self._debug_image(result.debug_views.get("seed_map"), alpha_image.shape)
        hole_image = self._debug_image(result.debug_views.get("hole_mask"), alpha_image.shape)
        frame_image = self._debug_image(result.debug_views.get("frame_mask"), alpha_image.shape)

        self._set_image(self._panel_widgets["source"], source_rgb, "source")
        self._set_image(self._panel_widgets["result"], composite_rgb, "result")
        self._set_image(self._panel_widgets["alpha"], alpha_image, "alpha", grayscale=True)
        self._set_image(self._panel_widgets["anchor"], anchor_image, "anchor", grayscale=True)
        self._set_image(self._panel_widgets["void"], void_image, "void", grayscale=True)
        self._set_image(self._panel_widgets["seed"], seed_image, "seed", grayscale=True)
        self._set_image(self._panel_widgets["hole"], hole_image, "hole", grayscale=True)
        self._set_image(self._panel_widgets["frame"], frame_image, "frame", grayscale=True)

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

        self.status_var.set("Sandbox export started...")
        thread = threading.Thread(
            target=self._run_export,
            args=(config, input_path, output_path, self.export_format_var.get()),
            daemon=True,
        )
        thread.start()

    def _run_export(self, config: AlphaFix2Config, input_path: str, output_path: str, format: str) -> None:
        service = AlphaFix2Service(config)

        def on_progress(done: int, total: int) -> None:
            self.after(0, lambda: self.status_var.set(f"Sandbox exporting frame {done}/{total}..."))

        try:
            summary = service.export_sequence(input_path, output_path, format, progress_callback=on_progress)
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Export failed", str(exc)))
            self.after(0, lambda: self.status_var.set(f"Export failed: {exc}"))
            return

        self.after(0, lambda: self._finish_export(summary))

    def _finish_export(self, summary: ExportSummary) -> None:
        self.status_var.set(
            f"Sandbox export complete: {summary.frame_count} frame(s) to {summary.output_dir} in {summary.mode} mode."
        )
        messagebox.showinfo(
            "Export complete",
            f"Saved {summary.frame_count} frame(s) to:\n{summary.output_dir}",
        )

    def _build_config(self) -> AlphaFix2Config:
        return AlphaFix2Config(
            mode=self.mode_var.get(),
            overlay_method=self.overlay_method_var.get(),
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
        )


def launch_gui() -> None:
    try:
        app = AlphaFix2GUI()
        app.mainloop()
    except Exception as exc:
        report_gui_exception("Alpha Fix Sandbox", exc)

````

## alpha_fix_2\pipeline.py

````python
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from alpha_fix.pipeline import AlphaFixProcessor as BaseProcessor
from alpha_fix.pipeline import BorderPalette

from .config import AlphaFix2Config


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
        self.config = config

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
            else:
                alpha = self._apply_chhc(alpha0, frame_bgr, self.config)
                debug_views["frame_mask"] = (alpha >= 0.5).astype(np.float32)
                debug_stats["hole_seed_count"] = 0
                debug_stats["hole_pixel_frac"] = 0.0
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

        hole_mask = self._grow_holes(gray, frame_fill, seeds, cfg)
        debug_views["hole_mask"] = hole_mask.astype(np.float32)
        debug_stats["hole_pixel_frac"] = float(np.mean(hole_mask))

        if not np.any(hole_mask):
            fallback = self._apply_chhc(alpha0, frame_bgr, cfg)
            return fallback, debug_views, debug_stats

        solid_mask = frame_fill & ~hole_mask
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
        frame_fill: np.ndarray,
        seeds: list[tuple[int, int]],
        cfg: AlphaFix2Config,
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

````

## alpha_fix_2\service.py

````python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from .config import AlphaFix2Config
from .pipeline import AlphaFix2Processor, FrameResult

ProgressCallback = Callable[[int, int], None]


@dataclass(slots=True)
class PreviewResult:
    input_path: Path
    frame_bgr: np.ndarray
    frame_result: FrameResult


@dataclass(slots=True)
class ExportSummary:
    input_path: Path
    output_dir: Path
    frame_count: int
    fps: float
    mode: str


class AlphaFix2Service:
    def __init__(self, config: AlphaFix2Config) -> None:
        self.config = config

    def preview(self, input_path: str | Path, frame_index: int = 0) -> PreviewResult:
        path = Path(input_path)
        frame = self._read_frame(path, frame_index)
        processor = AlphaFix2Processor(self.config)
        result = processor.process_frame(frame)
        return PreviewResult(path, frame, result)

    def export_sequence(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        format: str = "png_sequence",
        progress_callback: ProgressCallback | None = None,
    ) -> ExportSummary:
        source = Path(input_path)
        target = Path(output_dir)
        rgba_dir = target / "rgba"
        matte_dir = target / "alpha"
        rgba_dir.mkdir(parents=True, exist_ok=True)
        if self.config.export_alpha_matte:
            matte_dir.mkdir(parents=True, exist_ok=True)

        processor = AlphaFix2Processor(self.config)
        prev_alpha: np.ndarray | None = None

        if self._is_image(source):
            frame = self._read_image(source)
            result = processor.process_frame(frame)
            self._write_frame_outputs(result, rgba_dir, matte_dir, 0)
            if progress_callback is not None:
                progress_callback(1, 1)
            return ExportSummary(source, target, 1, 1.0, self.config.mode)

        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise FileNotFoundError(f"Unable to open input: {source}")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_count = 0

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                result = processor.process_frame(frame, prev_alpha=prev_alpha)
                self._write_frame_outputs(result, rgba_dir, matte_dir, frame_count)
                if self.config.mode == "subject":
                    prev_alpha = result.alpha_ema
                frame_count += 1

                if progress_callback is not None:
                    callback_total = total_frames if total_frames > 0 else frame_count
                    progress_callback(frame_count, callback_total)
        finally:
            capture.release()

        import subprocess
        
        if format != "png_sequence":
            output_name = source.stem + f"_{format}"
            
            if format == "chroma_mp4":
                output_file = target / f"{output_name}.mp4"
                cmd = [
                    "ffmpeg", "-y", "-framerate", str(fps),
                    "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
                    "-filter_complex", "[0:v]split[v1][v2];[v1]format=rgb24,drawbox=x=0:y=0:w=iw:h=ih:color=#00FF00:t=fill[bg];[bg][v2]overlay=format=rgb,format=yuv420p",
                    "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                    str(output_file)
                ]
            elif format == "prores_4444":
                output_file = target / f"{output_name}.mov"
                cmd = [
                    "ffmpeg", "-y", "-framerate", str(fps),
                    "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
                    "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
                    str(output_file)
                ]
            elif format == "webm_alpha":
                output_file = target / f"{output_name}.webm"
                cmd = [
                    "ffmpeg", "-y", "-framerate", str(fps),
                    "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
                    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
                    str(output_file)
                ]
            else:
                cmd = []
                
            if cmd:
                if progress_callback is not None:
                    progress_callback(frame_count, frame_count) # Max out progress bar during ffmpeg
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(f"FFMPEG export failed for {format}. Error: {e}")

        return ExportSummary(source, target, frame_count, fps, self.config.mode)

    @staticmethod
    def _is_image(path: Path) -> bool:
        return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    def _read_frame(self, path: Path, frame_index: int) -> np.ndarray:
        if self._is_image(path):
            return self._read_image(path)

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise FileNotFoundError(f"Unable to open input: {path}")

        try:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Unable to read frame {frame_index} from: {path}")
            return frame
        finally:
            capture.release()

    @staticmethod
    def _read_image(path: Path) -> np.ndarray:
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is None:
            raise FileNotFoundError(f"Unable to open image: {path}")
        return frame

    def _write_frame_outputs(
        self,
        result: FrameResult,
        rgba_dir: Path,
        matte_dir: Path,
        frame_index: int,
    ) -> None:
        rgba_path = rgba_dir / f"frame_{frame_index:05d}.png"
        rgba_bgra = cv2.cvtColor(result.rgba, cv2.COLOR_RGBA2BGRA)
        if not cv2.imwrite(str(rgba_path), rgba_bgra):
            raise IOError(f"Failed to write image to {rgba_path}")

        if self.config.export_alpha_matte:
            matte_path = matte_dir / f"alpha_{frame_index:05d}.png"
            alpha_u8 = np.clip(result.alpha * 255.0, 0.0, 255.0).astype(np.uint8)
            if not cv2.imwrite(str(matte_path), alpha_u8):
                raise IOError(f"Failed to write image to {matte_path}")

````

## tests\test_pipeline.py

````python
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2
import numpy as np

from alpha_fix.config import AlphaFixConfig
from alpha_fix.pipeline import AlphaFixProcessor
from alpha_fix.samples import SampleRegion, load_sample_regions, save_sample_regions


class AlphaFixPipelineTests(unittest.TestCase):
    def test_subject_mode_extracts_foreground_from_white_plate(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.circle(frame, (120, 120), 60, (32, 32, 32), -1, lineType=cv2.LINE_AA)

        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="subject",
                border_clusters=1,
                subject_low=0.8,
                subject_high=3.0,
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha[120, 120]), 0.8)
        self.assertLess(float(result.alpha[12, 12]), 0.1)

    def test_overlay_mode_carves_hole_inside_frame(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (239, 239), (20, 20, 160), 40)

        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="overlay",
                border_clusters=1,
                overlay_low=0.2,
                overlay_high=2.0,
                chhc_t_alpha=0.2,
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha[20, 20]), 0.8)
        self.assertLess(float(result.alpha[120, 120]), 0.1)

    def test_overlay_mode_auto_hole_opens_dark_center_window(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (40, 40), (200, 200), (30, 30, 200), 24)
        cv2.rectangle(frame, (85, 85), (155, 155), (8, 8, 8), -1)

        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="overlay",
                overlay_method="auto_hole",
                border_clusters=1,
                overlay_low=0.2,
                overlay_high=2.0,
                chhc_t_alpha=0.2,
                hole_dark_max=0.12,
                hole_flat_max=0.08,
                hole_min_area_frac=0.005,
                hole_seed_min_dist=4.0,
                hole_flood_tol=12,
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha[52, 120]), 0.8)
        self.assertLess(float(result.alpha[120, 120]), 0.1)

    def test_background_sample_forces_overlay_region_transparent(self) -> None:
        frame = np.full((200, 200, 3), 128, dtype=np.uint8)
        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="overlay",
                border_clusters=1,
                sample_regions=(
                    SampleRegion("background", "rectangle", 0.35, 0.35, 0.65, 0.65),
                ),
            )
        )
        result = processor.process_frame(frame)

        self.assertLess(float(result.alpha0[100, 100]), 0.05)
        self.assertLess(float(result.alpha[100, 100]), 0.05)

    def test_keep_sample_forces_subject_region_opaque(self) -> None:
        frame = np.full((200, 200, 3), 128, dtype=np.uint8)
        processor = AlphaFixProcessor(
            AlphaFixConfig(
                mode="subject",
                border_clusters=1,
                sample_regions=(
                    SampleRegion("keep", "ellipse", 0.35, 0.35, 0.65, 0.65),
                ),
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha0[100, 100]), 0.8)
        self.assertGreater(float(result.alpha[100, 100]), 0.8)

    def test_sample_preset_round_trip(self) -> None:
        regions = [
            SampleRegion("background", "rectangle", 0.1, 0.2, 0.3, 0.4),
            SampleRegion("keep", "ellipse", 0.5, 0.6, 0.8, 0.9),
        ]

        with TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / "samples.json"
            save_sample_regions(preset_path, regions)
            loaded = load_sample_regions(preset_path)

        self.assertEqual(loaded, [region.normalized() for region in regions])


if __name__ == "__main__":
    unittest.main()

````

## tests\test_sandbox_pipeline.py

````python
import unittest

import cv2
import numpy as np

from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.pipeline import AlphaFix2Processor


class AlphaFixSandboxPipelineTests(unittest.TestCase):
    def test_auto_hole_opens_dark_center_window(self) -> None:
        frame = np.full((240, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (40, 40), (200, 200), (30, 30, 200), 24)
        cv2.rectangle(frame, (85, 85), (155, 155), (8, 8, 8), -1)

        processor = AlphaFix2Processor(
            AlphaFix2Config(
                mode="overlay",
                overlay_method="auto_hole",
                border_clusters=1,
                overlay_low=0.2,
                overlay_high=2.0,
                chhc_t_alpha=0.2,
                hole_dark_max=0.12,
                hole_flat_max=0.08,
                hole_min_area_frac=0.005,
                hole_seed_min_dist=4.0,
                hole_flood_tol=12,
            )
        )
        result = processor.process_frame(frame)

        self.assertGreater(float(result.alpha[52, 120]), 0.8)
        self.assertLess(float(result.alpha[120, 120]), 0.1)
        self.assertIn("void_mask", result.debug_views)
        self.assertIn("hole_mask", result.debug_views)


if __name__ == "__main__":
    unittest.main()

````

