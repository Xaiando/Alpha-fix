import cv2
import numpy as np
from pathlib import Path

def get_first_frame(file_path):
    ext = file_path.suffix.lower()
    if ext in (".mp4", ".mov", ".avi", ".mkv"):
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            return None
        ok, frame = cap.read()
        cap.release()
        if ok:
            return frame
    else:
        return cv2.imread(str(file_path))
    return None

def detect_checkerboard(img, mask):
    # Convert to grayscale for detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    border_pixels = gray[mask]
    
    # Use K-Means (K=2) on border pixels to find the two colors
    pixel_data = border_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
    # We evaluate score on the border mask.
    y_indices, x_indices = np.where(mask)
    border_vals = gray[mask].astype(np.float32)
    
    best_score = -1.0
    best_size = 8
    best_off_x = 0
    best_off_y = 0
    
    for size in range(4, 65):
        for off_x in range(0, size, max(1, size // 8)):
            for off_y in range(0, size, max(1, size // 8)):
                phase = (((x_indices - off_x) // size) + ((y_indices - off_y) // size)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(border_vals - expected))
                score = 1.0 / (mae + 1e-5)
                
                if score > best_score:
                    best_score = score
                    best_size = size
                    best_off_x = off_x
                    best_off_y = off_y
                    
    # Refine search
    for off_x in range(max(0, best_off_x - 2), min(best_size, best_off_x + 3)):
        for off_y in range(max(0, best_off_y - 2), min(best_size, best_off_y + 3)):
            phase = (((x_indices - off_x) // best_size) + ((y_indices - off_y) // best_size)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(border_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > best_score:
                best_score = score
                best_off_x = off_x
                best_off_y = off_y
                
    mae = 1.0 / best_score
    return mae, best_size, best_off_x, best_off_y, color_min, color_max

def analyze_file(file_path):
    img = get_first_frame(file_path)
    if img is None:
        return {"name": file_path.name, "error": "Could not read frame"}
    
    h, w, c = img.shape
    # Sample border pixels (outer 16 pixels)
    mask = np.zeros((h, w), dtype=bool)
    bw = 16
    mask[:bw, :] = True
    mask[-bw:, :] = True
    mask[:, :bw] = True
    mask[:, -bw:] = True
    
    border_pixels = img[mask]
    
    # Border standard deviation in BGR
    std_bgr = np.std(border_pixels, axis=0)
    max_std = float(np.max(std_bgr))
    mean_bgr = np.mean(border_pixels, axis=0)
    
    # Convert average BGR of border to LAB to inspect chroma vs neutral
    mean_bgr_pixel = np.uint8([[mean_bgr]])
    mean_lab = cv2.cvtColor(mean_bgr_pixel, cv2.COLOR_BGR2LAB)[0, 0]
    L, A, B = float(mean_lab[0]), float(mean_lab[1]), float(mean_lab[2])
    
    # Checkerboard test (using full checkerboard detection)
    checker_mae, best_size, best_off_x, best_off_y, c_min, c_max = detect_checkerboard(img, mask)
    
    return {
        "name": file_path.name,
        "max_std": max_std,
        "mean_bgr": [float(x) for x in mean_bgr],
        "L": L, "A": A, "B": B,
        "checker_mae": checker_mae,
        "checker_size": best_size,
        "color_diff": c_max - c_min
    }

def main():
    input_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
    valid_suffixes = {".mp4", ".png", ".jpg", ".jpeg"}
    all_files = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_suffixes
    ])
    
    print(f"Analyzing {len(all_files)} files...")
    results = []
    for f in all_files:
        res = analyze_file(f)
        results.append(res)
        
    for res in results:
        if "error" in res:
            print(f"{res['name']}: {res['error']}")
            continue
        
        # Classify
        # 1. Solid check: max_std is small (under 6.0)
        is_solid = res["max_std"] < 6.0
        # Neutral check in LAB space
        # A=128, B=128 is neutral gray. Solid black or solid white are also neutral.
        # Let's see if abs(A - 128) < 10 and abs(B - 128) < 10
        is_neutral = abs(res["A"] - 128) < 10 and abs(res["B"] - 128) < 10
        
        # 2. Checkerboard check:
        # A checkerboard will have checker_mae < 10.0 and color_diff > 15.0 (ignoring solid backgrounds which might have very low diff)
        is_checker = (not is_solid) and res["checker_mae"] < 8.0 and res["color_diff"] > 15.0
        
        if is_solid:
            if is_neutral:
                category = f"solid_neutral (L={res['L']:.1f}, A={res['A']:.1f}, B={res['B']:.1f})"
            else:
                category = f"solid_chroma (L={res['L']:.1f}, A={res['A']:.1f}, B={res['B']:.1f})"
        elif is_checker:
            category = f"checkerboard (size={res['checker_size']}, MAE={res['checker_mae']:.1f}, diff={res['color_diff']:.1f})"
        else:
            category = "fallback(auto_hole)"
            
        print(f"{res['name']:45} | max_std={res['max_std']:5.1f} | L={res['L']:5.1f} A={res['A']:5.1f} B={res['B']:5.1f} | checker_mae={res['checker_mae']:4.1f} diff={res['color_diff']:5.1f} | -> {category}")

if __name__ == "__main__":
    main()
