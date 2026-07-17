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
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    border_pixels = gray[mask]
    
    pixel_data = border_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
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
                    
    for off_x in range(max(0, best_off_x - 2), min(best_size, best_off_x + 3)):
        for off_y in range(max(0, best_off_y - 2), min(best_size, best_off_y + 3)):
            phase = (((x_indices - off_x) // best_size) + ((y_indices - best_off_y) // best_size)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(border_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > best_score:
                best_score = score
                best_off_x = ox = off_x
                best_off_y = oy = off_y
                
    return 1.0 / best_score, best_size, color_max - color_min

def main():
    input_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
    valid_suffixes = {".mp4", ".png", ".jpg", ".jpeg"}
    all_files = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_suffixes
    ])
    
    potential_checkers = []
    for f in all_files:
        img = get_first_frame(f)
        if img is None:
            continue
        h, w = img.shape[:2]
        mask = np.zeros((h, w), dtype=bool)
        bw = 16
        mask[:bw, :] = True
        mask[-bw:, :] = True
        mask[:, :bw] = True
        mask[:, -bw:] = True
        
        std = np.max(np.std(img[mask], axis=0))
        if std < 6.0:
            continue # solid
            
        mae, size, diff = detect_checkerboard(img, mask)
        # Check ratio of mae to diff
        ratio = mae / (diff + 1e-6)
        if mae < 15.0 and diff > 15.0:
            potential_checkers.append((f.name, mae, size, diff, ratio))
            
    potential_checkers.sort(key=lambda x: x[1])
    print("Potential Checkerboard Backgrounds:")
    for name, mae, size, diff, ratio in potential_checkers:
        print(f"  {name:45} | MAE={mae:5.2f} | size={size:2d} | diff={diff:5.2f} | ratio={ratio:5.2f}")

if __name__ == "__main__":
    main()
