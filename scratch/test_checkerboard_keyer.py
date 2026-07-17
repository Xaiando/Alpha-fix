import cv2
import numpy as np

def detect_and_key(img_path, out_alpha_path, out_rgba_path):
    img = cv2.imread(img_path)
    h, w, c = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Detect checkerboard parameters
    border_width = 32
    mask = np.zeros_like(gray, dtype=bool)
    mask[:border_width, :] = True
    mask[-border_width:, :] = True
    mask[:, :border_width] = True
    mask[:, -border_width:] = True
    
    border_pixels = gray[mask]
    pixel_data = border_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
    # Grid search for cell size and offsets
    best_score = -1.0
    best_size = 16
    best_off_x = 0
    best_off_y = 0
    
    y_indices, x_indices = np.where(mask)
    border_vals = gray[mask].astype(np.float32)
    
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
                    
    # Refine
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
                
    print(f"Detected parameters: size={best_size}, offset_x={best_off_x}, offset_y={best_off_y}")
    
    # 2. Get color values in BGR
    # We create full meshgrid of coordinates
    y_all, x_all = np.indices((h, w))
    phase_all = (((x_all - best_off_x) // best_size) + ((y_all - best_off_y) // best_size)) % 2
    
    # We sample the average BGR colors for phase 0 and phase 1 from the border
    # to be robust to colored checkers (though usually they are gray)
    border_img_pixels = img[mask]
    border_phases = phase_all[mask]
    
    color1_bgr = np.mean(border_img_pixels[border_phases == 0], axis=0)
    color2_bgr = np.mean(border_img_pixels[border_phases == 1], axis=0)
    print(f"Detected BGR colors: color1={color1_bgr}, color2={color2_bgr}")
    
    # 3. Construct expected background image
    expected_bg = np.zeros_like(img, dtype=np.float32)
    expected_bg[phase_all == 0] = color1_bgr
    expected_bg[phase_all == 1] = color2_bgr
    
    # 4. Compute color distance (e.g. Euclidean in BGR or LAB)
    # Let's use Euclidean in BGR for now
    diff = img.astype(np.float32) - expected_bg
    dist = np.sqrt(np.sum(diff * diff, axis=-1))
    
    # 5. Threshold/Smoothstep to get alpha
    # Low threshold: distance below which is definitely background (alpha = 0)
    # High threshold: distance above which is definitely foreground (alpha = 1)
    low_thresh = 15.0
    high_thresh = 40.0
    
    t = np.clip((dist - low_thresh) / (high_thresh - low_thresh + 1e-6), 0.0, 1.0)
    alpha = t * t * (3.0 - 2.0 * t)
    
    # Save output
    alpha_u8 = (alpha * 255.0).astype(np.uint8)
    cv2.imwrite(out_alpha_path, alpha_u8)
    
    rgba = np.dstack([img, alpha_u8])
    cv2.imwrite(out_rgba_path, rgba)
    print("Successfully keyed and saved outputs.")

if __name__ == "__main__":
    detect_and_key(
        "test_runs/emoji_sparkle_joy_frame1.png",
        "test_runs/emoji_sparkle_joy_alpha1.png",
        "test_runs/emoji_sparkle_joy_rgba1.png"
    )
