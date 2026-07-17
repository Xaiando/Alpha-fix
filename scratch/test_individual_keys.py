import cv2
import numpy as np
from pathlib import Path
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

def test_file(file_path):
    file_path = Path(file_path)
    
    # 1. Test auto_hole
    config_hole = AlphaFix2Config(mode="overlay", overlay_method="auto_hole")
    service_hole = AlphaFix2Service(config_hole)
    res_hole = service_hole.preview(file_path, 0)
    bgra_hole = cv2.cvtColor(res_hole.frame_result.rgba, cv2.COLOR_RGBA2BGRA)
    cv2.imwrite(f"test_runs/{file_path.stem}_auto_hole.png", bgra_hole)
    
    # 2. Test checkerboard
    config_checker = AlphaFix2Config(
        mode="overlay",
        overlay_method="checkerboard",
        checkerboard_low=15.0,
        checkerboard_high=25.0,
        checkerboard_size=0,
        checkerboard_offset_x=-1,
        checkerboard_offset_y=-1
    )
    service_checker = AlphaFix2Service(config_checker)
    res_checker = service_checker.preview(file_path, 0)
    bgra_checker = cv2.cvtColor(res_checker.frame_result.rgba, cv2.COLOR_RGBA2BGRA)
    cv2.imwrite(f"test_runs/{file_path.stem}_checkerboard.png", bgra_checker)
    
    print(f"Done testing {file_path.name}")
    print(f"  Auto-hole center alpha: {np.mean(res_hole.frame_result.alpha[100:-100, 100:-100] < 0.5):.3f} transparent fraction")
    print(f"  Checkerboard center alpha: {np.mean(res_checker.frame_result.alpha[100:-100, 100:-100] < 0.5):.3f} transparent fraction")

test_file(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_cold.jpg")
test_file(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sad_30.jpg")
