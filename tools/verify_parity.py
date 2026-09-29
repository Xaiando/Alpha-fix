r"""Compare the old and refactored algorithms in isolated Python processes.

Usage: uv run python tools/verify_parity.py "E:\Temp\Projects\Tools\Alpha Fix"
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def capture(source, destination):
    if source != "local":
        sys.path.insert(0, source)
        from alpha_fix.config import AlphaFixConfig as ResearchConfig
        from alpha_fix.pipeline import AlphaFixProcessor as ResearchProcessor
        from alpha_fix_2.config import AlphaFix2Config as OperatorConfig
        from alpha_fix_2.pipeline import AlphaFix2Processor as OperatorProcessor
    else:
        from alpha_fix.engines.research_config import ResearchConfig
        from alpha_fix.engines.research import ResearchProcessor
        from alpha_fix.engines.operator_config import OperatorConfig
        from alpha_fix.engines.operator import OperatorProcessor
    from alpha_fix.samples import SampleRegion
    import cv2
    import numpy as np
    cv2.setNumThreads(1)
    samples = (SampleRegion("background", "ellipse", .40, .35, .48, .43), SampleRegion("keep", "rectangle", .56, .42, .64, .58), SampleRegion("basin", "rectangle", .23, .21, .79, .82))
    frames = []
    for index in range(4):
        frame = np.full((120, 180, 3), (125, 123, 124), np.uint8)
        cv2.rectangle(frame, (17, 17), (161, 103), (35, 32, 145), 11)
        cv2.rectangle(frame, (32, 30), (148, 92), (25, 26, 24), -1)
        cv2.circle(frame, (106 + index * 2, 61), 11, (55, 180, 220), -1)
        frame[85:91, 37:43] = (50, 180, 35)
        frames.append(frame)
    arrays = {}
    for engine, cfg_type, proc_type, methods in [("operator", OperatorConfig, OperatorProcessor, ["auto_hole", "chhc", "radfield", "chroma", "checkerboard"]), ("research", ResearchConfig, ResearchProcessor, ["auto_hole", "chhc", "constellation", "bounded_geodesic"])]:
        for mode, method in [("overlay", m) for m in methods] + [("subject", "auto_hole")]:
            for guided in (False, True):
                cv2.setRNGSeed(7319)
                config = cfg_type(mode=mode, overlay_method=method, sample_regions=samples if guided else (), border_clusters=2)
                processor = proc_type(config)
                prev = None
                for index, frame in enumerate(frames):
                    result = processor.process_frame(frame, prev_alpha=prev)
                    if mode == "subject":
                        prev = result.alpha_ema
                    for field in ("alpha0", "alpha", "alpha_ema", "confidence", "rgba"):
                        arrays[f"{engine}_{mode}_{method}_{guided}_{index}_{field}"] = getattr(result, field)
    np.savez_compressed(destination, **arrays)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--capture")
    args = parser.parse_args()
    if args.capture:
        capture(args.source, args.capture)
        return
    import numpy as np
    import cv2
    with tempfile.TemporaryDirectory(prefix="alpha-fix-parity-") as temporary:
        folder = Path(temporary).resolve()
        for name, source in (("old", args.source), ("new", "local")):
            subprocess.run([sys.executable, __file__, source, "--capture", str(folder / (name + ".npz"))], check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        with np.load(folder / "old.npz") as old, np.load(folder / "new.npz") as new:
            assert set(old.files) == set(new.files)
            differences = {key: float(np.max(np.abs(old[key].astype(float) - new[key].astype(float)))) for key in old.files}
            failed = {key: value for key, value in differences.items() if value != 0}
            report = {"source": args.source, "numpy": np.__version__, "opencv": cv2.__version__, "scenarios": 22, "frames_per_scenario": 4, "arrays_compared": len(differences), "maximum_difference": max(differences.values()), "failures": failed}
    output = Path(__file__).resolve().parents[1] / "docs/parity-report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
