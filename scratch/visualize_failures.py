import cv2
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
art_dir = Path(r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\artifacts")
art_dir.mkdir(parents=True, exist_ok=True)

failed_names = [
    "emoji_detective.jpg",
    "emoji_got_it_cool_32.png",
    "emoji_mindblown.jpg",
    "emoji_salute_1.jpg",
    "emoji_sleeping_1.jpg",
    "emoji_tired_salute.png",
    "emoji_wink.jpg",
    "gao8bEg - Imgur(1).png",
    "teledra-emoji-fight-cute.jpg",
    "teledra-emoji-fight-you.jpg"
]

from scratch.process_missing_images import detect_background_type

for name in failed_names:
    p = src_dir / name
    if not p.exists():
        continue
    bg_type, bg_details = detect_background_type(p)
    print(f"\nProcessing {name} ({bg_type}, {bg_details})")
    
    if bg_type in ("solid_neutral", "solid_neutral_overflow"):
        config = AlphaFix2Config(mode="subject", subject_low=0.8, subject_high=2.5,
                                  anchor_blur_sigma=1.0, export_alpha_matte=True)
    elif bg_type == "checkerboard":
        config = AlphaFix2Config(mode="overlay", overlay_method="checkerboard",
                                  checkerboard_low=15.0, checkerboard_high=25.0,
                                  export_alpha_matte=True)
    else:
        config = AlphaFix2Config(mode="overlay", overlay_method="auto_hole",
                                  export_alpha_matte=True)
                                  
    try:
        service = AlphaFix2Service(config)
        preview = service.preview(p)
        rgba = preview.frame_result.rgba
        alpha = preview.frame_result.alpha
        
        orig = cv2.imread(str(p))
        
        # Save images to artifacts
        stem = Path(name).stem
        cv2.imwrite(str(art_dir / f"fail_{stem}_orig.png"), orig)
        cv2.imwrite(str(art_dir / f"fail_{stem}_alpha.png"), (alpha * 255).astype(np.uint8))
        cv2.imwrite(str(art_dir / f"fail_{stem}_rgba.png"), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
        print(f"Saved visualization for {name}")
    except Exception as e:
        print(f"Error on {name}: {e}")
