from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .media import discover_media
from .project import FORMATS, METHODS, MediaItem, Project, Settings
from .service import export_batch


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Alpha Fix 3 — guided alpha-matte cleanup")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--input", type=Path, help="Image, video, or folder")
    parser.add_argument("--output", type=Path, help="Parent directory for isolated export runs")
    parser.add_argument("--project", type=Path, help="Open/export a saved .afix project")
    parser.add_argument("--engine", choices=METHODS, default="operator")
    parser.add_argument("--mode", choices=["overlay", "subject"], default="overlay")
    parser.add_argument("--overlay-method", choices=sorted(set().union(*(m.keys() for m in METHODS.values()))))
    parser.add_argument("--export-format", choices=FORMATS)
    parser.add_argument("--sample-preset", type=Path, help="Import old sample JSON or a new full settings preset")
    parser.add_argument("--set", action="append", default=[], metavar="NAME=JSON", help="Override an engine parameter; e.g. --set ema_decay=0.5")
    parser.add_argument("--no-recursive", action="store_true")
    parser.add_argument("--no-alpha-matte", action="store_true")
    args = parser.parse_args(argv)
    if args.gui or (not args.input and not args.project):
        from .ui.app import launch
        return launch(args.project, args.input)
    try:
        if args.project and args.input:
            parser.error("Choose --input or --project.")
        if args.project:
            project = Project.load(args.project)
        else:
            if not args.output:
                parser.error("--output is required for CLI input export.")
            settings = Settings(engine=args.engine, mode=args.mode, method=args.overlay_method or ("bounded_geodesic" if args.engine == "research" else "auto_hole"))
            if args.sample_preset:
                payload = json.loads(args.sample_preset.read_text(encoding="utf-8-sig"))
                if payload.get("type") == "alpha-fix-preset":
                    if payload.get("version") != 1:
                        raise ValueError("Unsupported preset version.")
                    settings = Settings.from_dict(payload["settings"])
                else:
                    from .samples import load_sample_regions
                    settings.samples = load_sample_regions(args.sample_preset)
            for parameter in args.set:
                name, value = parameter.split("=", 1)
                settings.parameters[name] = json.loads(value)
            if args.no_alpha_matte:
                settings.parameters["export_alpha_matte"] = False
            settings.config()
            items = [MediaItem(path, settings.clone()) for path in discover_media(args.input, args.output, not args.no_recursive)]
            project = Project(items, args.output)
        if not project.items:
            raise ValueError("No supported media files were found.")
        if args.output:
            project.output_dir = args.output
        if args.export_format:
            project.export_format = args.export_format
        def progress(done, total, message):
            print(f"[{done}/{total or '?'}] {message}", flush=True)
        results = export_batch(project.items, project.output_dir, project.export_format, progress=progress)
        for record in results:
            print(f"{project.items[record['index']].path.name}: {record['status']} — {record.get('output', record.get('error'))}")
        return 1 if any(r["status"] == "Failed" for r in results) else 0
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Alpha Fix: {exc}", file=sys.stderr)
        return 1
