from __future__ import annotations

import argparse
from pathlib import Path

from alpha_fix.samples import load_sample_regions

from .config import AlphaFix2Config
from .service import AlphaFix2Service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alpha Fix sandbox desktop app.")
    parser.add_argument("--gui", action="store_true", help="Launch the sandbox GUI.")
    parser.add_argument("--input", help="Input image, video, or folder path.")
    parser.add_argument("--output", help="Output directory for exported frames and media.")
    parser.add_argument("--mode", choices=("subject", "overlay"), default="overlay")
    parser.add_argument("--overlay-method", choices=("auto_hole", "chhc", "radfield", "chroma", "checkerboard"), default="auto_hole")
    parser.add_argument(
        "--export-format",
        choices=("chroma_mp4", "prores_4444", "webm_alpha", "png_sequence"),
        default="png_sequence",
        help="Media export format. PNG frames are always written to rgba/ and alpha/.",
    )
    parser.add_argument("--sample-preset", help="JSON file with guided sample regions.")
    parser.add_argument("--recursive", action="store_true", default=True, help="Scan folders recursively.")
    parser.add_argument("--no-recursive", action="store_false", dest="recursive", help="Only scan the top folder.")
    parser.add_argument("--border-width", type=int, default=12)
    parser.add_argument("--border-clusters", type=int, default=3)
    parser.add_argument("--anchor-blend", type=float, default=0.0)
    parser.add_argument("--subject-low", type=float, default=0.8)
    parser.add_argument("--subject-high", type=float, default=2.5)
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
    parser.add_argument("--chroma-target-a", type=float, default=69.0)
    parser.add_argument("--chroma-target-b", type=float, default=185.0)
    parser.add_argument("--chroma-low", type=float, default=55.0)
    parser.add_argument("--chroma-high", type=float, default=82.0)
    parser.add_argument("--chroma-portal-x-min", type=float, default=0.22)
    parser.add_argument("--chroma-portal-x-max", type=float, default=0.78)
    parser.add_argument("--chroma-portal-y-min", type=float, default=0.15)
    parser.add_argument("--chroma-portal-y-max", type=float, default=0.88)
    parser.add_argument("--checkerboard-low", type=float, default=15.0)
    parser.add_argument("--checkerboard-high", type=float, default=25.0)
    parser.add_argument("--checkerboard-size", type=int, default=0)
    parser.add_argument("--checkerboard-offset-x", type=int, default=-1)
    parser.add_argument("--checkerboard-offset-y", type=int, default=-1)
    parser.add_argument("--srf-sigma-d", type=float, default=2000.0)
    parser.add_argument("--srf-sigma-c", type=float, default=18.0)
    parser.add_argument("--srf-gamma", type=float, default=2.2)
    parser.add_argument("--srf-tau-delta", type=float, default=12.0)
    parser.add_argument("--srf-lambda-t", type=float, default=0.30)
    parser.add_argument("--srf-edge-boost", type=float, default=0.15)
    parser.add_argument("--despill-enabled", action="store_true", default=True, help="Enable Spill Suppressor.")
    parser.add_argument("--no-despill", action="store_false", dest="despill_enabled", help="Disable Spill Suppressor.")
    parser.add_argument("--despill-target", choices=("auto", "green", "blue", "none"), default="auto", help="Spill Suppressor target color.")
    parser.add_argument("--despill-strength", type=float, default=1.0, help="Spill Suppressor strength (0.0 - 1.0).")
    parser.add_argument("--despill-threshold", type=float, default=1.0, help="Spill Suppressor threshold ratio.")
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

    config = AlphaFix2Config(
        mode=args.mode,
        overlay_method=args.overlay_method,
        sample_regions=sample_regions,
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
        chroma_target_a=args.chroma_target_a,
        chroma_target_b=args.chroma_target_b,
        chroma_low=args.chroma_low,
        chroma_high=args.chroma_high,
        chroma_portal_x_min=args.chroma_portal_x_min,
        chroma_portal_x_max=args.chroma_portal_x_max,
        chroma_portal_y_min=args.chroma_portal_y_min,
        chroma_portal_y_max=args.chroma_portal_y_max,
        checkerboard_low=args.checkerboard_low,
        checkerboard_high=args.checkerboard_high,
        checkerboard_size=args.checkerboard_size,
        checkerboard_offset_x=args.checkerboard_offset_x,
        checkerboard_offset_y=args.checkerboard_offset_y,
        srf_sigma_d=args.srf_sigma_d,
        srf_sigma_c=args.srf_sigma_c,
        srf_gamma=args.srf_gamma,
        srf_tau_delta=args.srf_tau_delta,
        srf_lambda_t=args.srf_lambda_t,
        srf_edge_boost=args.srf_edge_boost,
        despill_enabled=args.despill_enabled,
        despill_target=args.despill_target,
        despill_strength=args.despill_strength,
        despill_threshold=args.despill_threshold,
        export_alpha_matte=not args.no_alpha_matte,
    )

    service = AlphaFix2Service(config)

    def progress(done: int, total: int) -> None:
        print(f"[{done}/{total}] sandbox processing", flush=True)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_dir():
        def batch_progress(done: int, total: int, current_path: Path) -> None:
            print(f"[{done}/{total}] sandbox batch: {current_path.name}", flush=True)

        batch_summary = service.export_batch(
            input_path,
            output_path,
            args.export_format,
            recursive=args.recursive,
            progress_callback=batch_progress,
        )
        print(
            f"Sandbox batch exported {batch_summary.succeeded}/{batch_summary.item_count} file(s) "
            f"to {batch_summary.output_dir}. Failed: {batch_summary.failed}.",
            flush=True,
        )
    else:
        summary = service.export_sequence(
            input_path,
            output_path,
            args.export_format,
            progress_callback=progress,
        )
        media_suffix = ""
        if summary.media_path is not None:
            media_suffix = f" Media: {summary.media_path.name}."
        print(
            f"Sandbox exported {summary.frame_count} frame(s) to {summary.output_dir} "
            f"in {summary.mode} mode.{media_suffix}",
            flush=True,
        )
