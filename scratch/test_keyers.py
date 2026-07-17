import cv2
import numpy as np
from pathlib import Path
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

def test_file(file_path, method, **overrides):
    file_path = Path(file_path)
    print(f"--- Testing {file_path.name} with method={method} ---")
    config = AlphaFix2Config(
        mode="overlay",
        overlay_method=method,
        **overrides
    )
    service = AlphaFix2Service(config)
    try:
        res = service.preview(file_path, 0)
        # Check alpha channel statistics
        alpha = res.frame_result.alpha
        h, w = alpha.shape
        # Let's count fraction of transparent pixels (alpha < 0.5)
        trans_frac = np.mean(alpha < 0.5)
        # Let's check some pixels in the middle (e.g. central 100x100 region)
        mid_y, mid_x = h // 2, w // 2
        mid_alpha = np.mean(alpha[mid_y-50:mid_y+50, mid_x-50:mid_x+50])
        print(f"  Transparent fraction: {trans_frac:.3f}")
        print(f"  Center alpha (should be ~1.0 for subjects in center): {mid_alpha:.3f}")
        return alpha
    except Exception as e:
        print(f"  Failed: {e}")
        return None

# Let's test emoji_sarcastic.png with chroma keyer
# BGR for solid gray emoji_sarcastic is [161, 162, 161] -> LAB [170, 128, 128]
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png",
    "chroma",
    chroma_target_a=128.0,
    chroma_target_b=128.0,
    chroma_low=5.0,
    chroma_high=15.0
)

# Let's test emoji_sarcastic.png with auto_hole
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png",
    "auto_hole"
)

# Let's test emoji_sarcastic.png with chhc
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png",
    "chhc"
)

# Let's test remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png with chroma target A=128, B=128
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png",
    "chroma",
    chroma_target_a=128.0,
    chroma_target_b=128.0,
    chroma_low=5.0,
    chroma_high=15.0
)

# Let's test remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png with auto_hole
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png",
    "auto_hole"
)

# Let's test remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png with chhc
test_file(
    r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png",
    "chhc"
)
