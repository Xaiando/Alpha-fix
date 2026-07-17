"""Quick test on 4 representative images — view outputs to check quality before full run."""
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
out_dir = Path(r"C:\Users\Kaged\Documents\Projects\Tools\Alpha Fix\scratch")

test_files = [
    # checkerboard, low contrast (was failing visually)
    ("emoji_waving.jpg",     "checkerboard", 15.0, 25.0),
    # checkerboard, medium contrast
    ("emoji_party.jpg",      "checkerboard", 15.0, 25.0),
    # checkerboard, tight diff (~30) 
    ("emoji_thinking_29.jpg","checkerboard", 15.0, 25.0),
    # solid white BG
    ("emoji_hug.jpg",        "subject",      None,  None),
]

for fname, mode, low, high in test_files:
    src = src_dir / fname
    dst = out_dir / f"test__{fname.replace('.jpg','').replace('.png','')}.png"
    print(f"\n--- {fname} ---")
    if mode == "checkerboard":
        config = AlphaFix2Config(mode="overlay", overlay_method="checkerboard",
                                  checkerboard_low=low, checkerboard_high=high)
    else:
        config = AlphaFix2Config(mode="subject", subject_low=0.8, subject_high=2.5,
                                  anchor_blur_sigma=1.0)
    service = AlphaFix2Service(config)
    preview = service.preview(src)
    rgba = preview.frame_result.rgba
    cv2.imwrite(str(dst), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    # Quick alpha stats
    alpha = rgba[:, :, 3]
    h, w = alpha.shape
    cs = min(20, h//8, w//8)
    corner_mean = np.mean(np.concatenate([
        alpha[:cs, :cs].flatten(), alpha[:cs, -cs:].flatten(),
        alpha[-cs:, :cs].flatten(), alpha[-cs:, -cs:].flatten()]))
    center_mean = np.mean(alpha[h//2-50:h//2+50, w//2-50:w//2+50])
    pct_transparent = 100 * np.mean(alpha < 10)
    print(f"  Corners avg alpha: {corner_mean:.0f}/255  (want ~0)")
    print(f"  Center avg alpha:  {center_mean:.0f}/255  (want ~255)")
    print(f"  Total transparent: {pct_transparent:.1f}%")
    print(f"  Saved: {dst.name}")
