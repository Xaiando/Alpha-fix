import cv2
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service
from scratch.process_missing_images import audit_png

p = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_mindblown.jpg")
config = AlphaFix2Config(mode="overlay", overlay_method="checkerboard",
                          checkerboard_low=30.0, checkerboard_high=45.0,
                          export_alpha_matte=True)

service = AlphaFix2Service(config)

for margin in (4, 8, 12, 16):
    preview = service.preview(p)
    rgba = preview.frame_result.rgba.copy()
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    
    # Apply border cleanup
    alpha[:margin, :] = 0.0
    alpha[-margin:, :] = 0.0
    alpha[:, :margin] = 0.0
    alpha[:, -margin:] = 0.0
    
    rgba[:, :, 3] = (alpha * 255).astype(np.uint8)
    
    dst = Path(f"C:\\Users\\Kaged\\Movies\\Hub\\Projects\\image-remix\\processed\\test_margin_{margin}.png")
    cv2.imwrite(str(dst), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    
    ok_corner, ok_center, issues = audit_png(dst)
    print(f"Margin {margin}: ok_corner={ok_corner}, issues={issues}")
