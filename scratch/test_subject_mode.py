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
        out_path = Path("test_runs") / f"{file_path.stem}_subject.png"
        bgra = cv2.cvtColor(res.frame_result.rgba, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(out_path), bgra)
        print(f"  Saved to {out_path}")
    except Exception as e:
        print(f"  Failed: {e}")

print("Testing emoji_sarcastic.png in subject mode:")
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png",
    mode="subject",
    subject_low=0.8,
    subject_high=2.5,
    anchor_blur_sigma=1.0
)

print("\nTesting remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png in subject mode:")
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png",
    mode="subject",
    subject_low=0.8,
    subject_high=2.5,
    anchor_blur_sigma=1.0
)
