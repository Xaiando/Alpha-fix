import cv2
import numpy as np
from pathlib import Path
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

def run_test(file_path, method, output_name, **overrides):
    file_path = Path(file_path)
    config = AlphaFix2Config(
        mode="overlay",
        overlay_method=method,
        **overrides
    )
    service = AlphaFix2Service(config)
    res = service.preview(file_path, 0)
    
    # Save the output RGBA
    out_dir = Path("test_runs")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / output_name
    # Convert RGBA to BGRA
    rgba = res.frame_result.rgba
    bgra = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
    cv2.imwrite(str(out_path), bgra)
    print(f"Saved {out_path}")

# Run tests
run_test(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png",
    "auto_hole",
    "sarcastic_auto_hole.png"
)
run_test(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png",
    "chroma",
    "sarcastic_chroma.png",
    chroma_target_a=128.0,
    chroma_target_b=128.0,
    chroma_low=5.0,
    chroma_high=15.0
)
run_test(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png",
    "auto_hole",
    "remove_bg_auto_hole.png"
)
run_test(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png",
    "chroma",
    "remove_bg_chroma.png",
    chroma_target_a=128.0,
    chroma_target_b=128.0,
    chroma_low=5.0,
    chroma_high=15.0
)
