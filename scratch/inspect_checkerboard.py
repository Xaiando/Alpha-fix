import cv2
import numpy as np

def detect_checkerboard(img):
    # Convert to grayscale for detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # We will sample the borders (e.g., top, bottom, left, right, say 32 pixels wide)
    border_width = 32
    mask = np.zeros_like(gray, dtype=bool)
    mask[:border_width, :] = True
    mask[-border_width:, :] = True
    mask[:, :border_width] = True
    mask[:, -border_width:] = True
    
    border_pixels = gray[mask]
    
    # Use K-Means (K=2) on border pixels to find the two colors
    pixel_data = border_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    # Order them
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
    print(f"Detected checkerboard colors: {color_min:.1f} and {color_max:.1f}")
    
    # Now let's find cell_size and offsets.
    # We will test cell sizes from 4 to 64.
    # For each cell size, we try offsets.
    best_score = -1.0
    best_size = 8
    best_off_x = 0
    best_off_y = 0
    
    # We evaluate score on the border mask.
    y_indices, x_indices = np.where(mask)
    border_vals = gray[mask].astype(np.float32)
    
    for size in range(4, 65):
        # We can optimize: we don't need to check all offsets if we do a grid search
        # or we can check all offsets since size is small (<= 64)
        for off_x in range(0, size, max(1, size // 8)):
            for off_y in range(0, size, max(1, size // 8)):
                # Compute expected checker phase: (floor((x - off_x) / size) + floor((y - off_y) / size)) % 2
                phase = (((x_indices - off_x) // size) + ((y_indices - off_y) // size)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                
                # Score is inverse of mean absolute error
                mae = np.mean(np.abs(border_vals - expected))
                score = 1.0 / (mae + 1e-5)
                
                if score > best_score:
                    best_score = score
                    best_size = size
                    best_off_x = off_x
                    best_off_y = off_y
                    
    # Refine search around best_size with exact offsets
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
    print(f"Detected: size={best_size}, offset_x={best_off_x}, offset_y={best_off_y}, MAE={mae:.2f}")
    return best_size, best_off_x, best_off_y, color_min, color_max

if __name__ == "__main__":
    img = cv2.imread("test_runs/emoji_sparkle_joy_frame1.png")
    detect_checkerboard(img)
