import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def project_gradients(fname):
    img = cv2.imread(str(src_dir / fname))
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Compute gradients
    grad_x = np.abs(gray[:, 1:].astype(np.float32) - gray[:, :-1].astype(np.float32))
    grad_y = np.abs(gray[1:, :].astype(np.float32) - gray[:-1, :].astype(np.float32))
    
    # We want to sum only in the background region (outer 20% border)
    border_y = h // 5
    border_x = w // 5
    
    bg_mask_x = np.ones((h, w-1), dtype=bool)
    bg_mask_x[border_y:-border_y, border_x:-border_x] = False
    
    bg_mask_y = np.ones((h-1, w), dtype=bool)
    bg_mask_y[border_y:-border_y, border_x:-border_x] = False
    
    proj_x = np.sum(grad_x * bg_mask_x, axis=0)
    proj_y = np.sum(grad_y * bg_mask_y, axis=1)
    
    # Find local peaks of proj_x and proj_y
    def find_peaks(signal, min_dist=15):
        peaks = []
        for i in range(1, len(signal)-1):
            if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                # Check if it's the maximum in its neighborhood
                start = max(0, i - min_dist)
                end = min(len(signal), i + min_dist + 1)
                if signal[i] == np.max(signal[start:end]):
                    peaks.append(i)
        return np.array(peaks)
        
    peaks_x = find_peaks(proj_x)
    peaks_y = find_peaks(proj_y)
    
    # Fit a linear line to peak indices to find spacing and offset:
    # peak_index = size * n + offset
    # We can do this by fitting a line to peaks
    def fit_comb(peaks):
        best_r2 = -1.0
        best_size = 0.0
        best_off = 0.0
        # Search size from 25.0 to 26.0
        for s in np.arange(25.0, 26.0, 0.001):
            # For each size, compute the rounded expected peak positions
            # and match them to actual peaks
            for off in np.arange(0.0, s, 0.1):
                # Expected peaks: s * n + off
                n_min = int(np.floor((peaks[0] - off) / s))
                n_max = int(np.ceil((peaks[-1] - off) / s))
                expected = s * np.arange(n_min, n_max + 1) + off
                # For each actual peak, find distance to nearest expected peak
                dists = np.min(np.abs(peaks[:, None] - expected[None, :]), axis=1)
                score = np.mean(dists)
                if score < best_r2 or best_r2 < 0:
                    best_r2 = score
                    best_size = s
                    best_off = off
        return best_size, best_off, best_r2
        
    sx, ox, score_x = fit_comb(peaks_x)
    sy, oy, score_y = fit_comb(peaks_y)
    
    print(f"\n===== Comb Fit for {fname} =====")
    print(f"  X Grid: size={sx:.4f}, offset={ox:.2f}, avg_error={score_x:.3f} px (num_peaks={len(peaks_x)})")
    print(f"  Y Grid: size={sy:.4f}, offset={oy:.2f}, avg_error={score_y:.3f} px (num_peaks={len(peaks_y)})")

project_gradients("emoji_waving.jpg")
project_gradients("emoji_thinking_29.jpg")
