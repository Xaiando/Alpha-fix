import cv2
import numpy as np
from pathlib import Path
import sys
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service
from scratch.process_missing_images import detect_background_type, audit_png

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
out_dir = src_dir / "processed"

files_to_test = [
    "emoji_detective.jpg",
    "emoji_got_it_cool_32.png",
    "emoji_mindblown.jpg",
    "emoji_salute_1.jpg",
    "emoji_sleeping_1.jpg",
    "emoji_wink.jpg",
    "gao8bEg - Imgur(1).png",
    "teledra-emoji-fight-cute.jpg",
    "teledra-emoji-fight-you.jpg"
]

for name in files_to_test:
    p = src_dir / name
    if not p.exists():
        continue
    bg_type, bg_details = detect_background_type(p)
    print(f"\n=== Testing {name} ===")
    print(f"  Detected BG: {bg_type} ({bg_details})")
    
    if bg_type in ("solid_neutral", "solid_neutral_overflow"):
        config = AlphaFix2Config(mode="subject", subject_low=0.8, subject_high=2.5,
                                  anchor_blur_sigma=1.0, export_alpha_matte=True)
    elif bg_type == "checkerboard":
        config = AlphaFix2Config(mode="overlay", overlay_method="checkerboard",
                                  checkerboard_low=30.0, checkerboard_high=45.0,
                                  export_alpha_matte=True)
    else:
        config = AlphaFix2Config(mode="overlay", overlay_method="auto_hole",
                                  export_alpha_matte=True)
                                  
    dst = out_dir / f"test_{Path(name).stem}.png"
    try:
        service = AlphaFix2Service(config)
        preview = service.preview(p)
        rgba = preview.frame_result.rgba
        cv2.imwrite(str(dst), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
        
        ok_corner, ok_center, issues = audit_png(dst)
        if issues:
            print(f"  RESULT: FAIL. Issues: {'; '.join(issues)}")
        else:
            print(f"  RESULT: PASS!")
    except Exception as e:
        print(f"  RESULT: ERROR: {e}")
