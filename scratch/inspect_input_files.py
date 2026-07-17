import cv2
import numpy as np

def analyze_file(path):
    img = cv2.imread(path)
    if img is None:
        print(f"Failed to read {path}")
        return
    h, w, c = img.shape
    print(f"File: {path}, Size: {w}x{h}, Channels: {c}")
    # Sample border pixels (outer 16 pixels)
    mask = np.zeros((h, w), dtype=bool)
    bw = 16
    mask[:bw, :] = True
    mask[-bw:, :] = True
    mask[:, :bw] = True
    mask[:, -bw:] = True
    border_pixels = img[mask]
    
    # Calculate stats
    mean = np.mean(border_pixels, axis=0)
    std = np.std(border_pixels, axis=0)
    print(f"  Border mean BGR: {mean}")
    print(f"  Border std BGR: {std}")
    print(f"  Max standard deviation across channels: {np.max(std)}")

analyze_file(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png")
analyze_file(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\remove-bg-12e951df-4dce-4240-90d7-fb06d037309b.png")
