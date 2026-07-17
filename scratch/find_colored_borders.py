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

def main():
    input_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
    valid_suffixes = {".mp4", ".png", ".jpg", ".jpeg"}
    all_files = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_suffixes
    ])
    
    for f in all_files:
        img = get_first_frame(f)
        if img is None:
            continue
        h, w, c = img.shape
        # Sample borders (outer 16 px)
        mask = np.zeros((h, w), dtype=bool)
        bw = 16
        mask[:bw, :] = True
        mask[-bw:, :] = True
        mask[:, :bw] = True
        mask[:, -bw:] = True
        
        border_pixels = img[mask]
        mean_bgr = np.mean(border_pixels, axis=0)
        std_bgr = np.std(border_pixels, axis=0)
        max_std = np.max(std_bgr)
        
        mean_bgr_pixel = np.uint8([[mean_bgr]])
        mean_lab = cv2.cvtColor(mean_bgr_pixel, cv2.COLOR_BGR2LAB)[0, 0]
        L, A, B = float(mean_lab[0]), float(mean_lab[1]), float(mean_lab[2])
        
        if max_std < 10.0 and (abs(A - 128) > 8 or abs(B - 128) > 8):
            print(f"COLORED SOLID BORDER: {f.name} | std={max_std:.1f} | L={L:.1f} A={A:.1f} B={B:.1f} | BGR={mean_bgr}")
        elif abs(A - 128) > 8 or abs(B - 128) > 8:
            # Let's print any file with non-neutral borders even if not super solid
            print(f"COLORED BORDER (non-solid): {f.name} | std={max_std:.1f} | L={L:.1f} A={A:.1f} B={B:.1f} | BGR={mean_bgr}")

if __name__ == "__main__":
    main()
