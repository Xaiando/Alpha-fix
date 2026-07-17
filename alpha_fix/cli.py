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
    parser.add_argument("--output", help="Output directory for exported frames and media.")
    parser.add_argument("--mode", choices=("subject", "overlay"), default="overlay")
    parser.add_argument("--overlay-method", choices=("auto_hole", "chhc"), default="auto_hole")
    parser.add_argument(
        "--export-format",
        choices=("prores_4444", "webm_alpha", "chroma_mp4", "png_sequence"),
        default="prores_4444",
        help="Media export format. PNG frames are always written to rgba/ and alpha/.",
    )
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
        export_format=args.export_format,
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
    media_suffix = ""
    if summary.video_artifact is not None:
        media_suffix = f" Media: {summary.video_artifact.output_path.name}."
    print(
        f"Exported {summary.frame_count} frame(s) to {summary.output_dir} in {summary.mode} mode.{media_suffix}",
        flush=True,
    )
