import cv2
import numpy as np
from pathlib import Path

out_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\processed")

# We list all PNG files in out_dir and delete those that fail the audit
files = sorted(list(out_dir.glob("*.png")))
deleted_count = 0

for p in files:
    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] != 4:
        continue
    h, w = img.shape[:2]
    alpha = img[:, :, 3]
    cs = min(20, h // 8, w // 8)
    corners_alpha = np.concatenate([
        alpha[:cs, :cs].flatten(),
        alpha[:cs, -cs:].flatten(),
        alpha[-cs:, :cs].flatten(),
        alpha[-cs:, -cs:].flatten(),
    ])
    center_alpha = alpha[h//2 - 60:h//2 + 60, w//2 - 60:w//2 + 60]
    
    corner_mean = float(np.mean(corners_alpha))
    center_opaque = float(np.mean(center_alpha > 200))
    
    issues = []
    if corner_mean > 30:
        issues.append(f"corners mean={corner_mean:.1f}")
    if center_opaque < 0.5:
        issues.append(f"center opaque={center_opaque*100:.1f}%")
        
    if issues:
        print(f"Deleting failed file {p.name} due to: {'; '.join(issues)}")
        p.unlink()
        deleted_count += 1

print(f"\nSuccessfully deleted {deleted_count} failed files.")
