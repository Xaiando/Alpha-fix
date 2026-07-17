import cv2
import numpy as np
from pathlib import Path
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

def test_file(file_path, **config_args):
    file_path = Path(file_path)
    config = AlphaFix2Config(**config_args)
    service = AlphaFix2Service(config)
    try:
        res = service.preview(file_path, 0)
        alpha = res.frame_result.alpha
        h, w = alpha.shape
        trans_frac = np.mean(alpha < 0.5)
        # Check center region alpha
        mid_y, mid_x = h // 2, w // 2
        mid_alpha = np.mean(alpha[mid_y-50:mid_y+50, mid_x-50:mid_x+50])
        print(f"File: {file_path.name}")
        print(f"  Mode: {config.mode}, Method: {config.overlay_method}")
        print(f"  Transparent fraction: {trans_frac:.3f}")
        print(f"  Center alpha (should be ~1.0): {mid_alpha:.3f}")
        
        # Save output image
        out_path = Path("test_runs") / f"{file_path.stem}_checkerboard_test.png"
        bgra = cv2.cvtColor(res.frame_result.rgba, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(out_path), bgra)
        print(f"  Saved to {out_path}")
    except Exception as e:
        print(f"  Failed: {e}")

print("Testing emoji_sparkle_joy.mp4 with checkerboard keyer:")
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sparkle_joy.mp4",
    mode="overlay",
    overlay_method="checkerboard",
    checkerboard_low=15.0,
    checkerboard_high=25.0,
    checkerboard_size=0,
    checkerboard_offset_x=-1,
    checkerboard_offset_y=-1
)
