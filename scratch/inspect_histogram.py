import cv2
import numpy as np
from pathlib import Path

def analyze(path):
    img = cv2.imread(path)
    if img is None:
        # try video
        cap = cv2.VideoCapture(path)
        ok, img = cap.read()
        cap.release()
        if not ok:
            print(f"Failed to read {path}")
            return
            
    h, w = img.shape[:2]
    # Sample border
    mask = np.zeros((h, w), dtype=bool)
    bw = 16
    mask[:bw, :] = True
    mask[-bw:, :] = True
    mask[:, :bw] = True
    mask[:, -bw:] = True
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    border_pixels = gray[mask]
    
    # Histogram of border pixels
    hist, _ = np.histogram(border_pixels, bins=10, range=(0, 256))
    
    # K-means
    pixel_data = border_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    diff = color_max - color_min
    
    # Let's check if the pixels are clustered into two narrow peaks
    # We can measure the variance within each cluster
    var1 = np.var(border_pixels[labels.ravel() == 0])
    var2 = np.var(border_pixels[labels.ravel() == 1])
    mean_var = (var1 + var2) / 2.0
    
    print(f"File: {Path(path).name}")
    print(f"  K-means centers: {color_min:.1f}, {color_max:.1f} (diff={diff:.1f})")
    print(f"  Within-cluster variance (mean): {mean_var:.2f}")
    print(f"  Histogram: {hist.tolist()}")

analyze(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sparkle_joy.mp4")
analyze(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_cold.jpg")
analyze(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sad_30.jpg")
analyze(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png")
analyze(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_angry.jpg")
