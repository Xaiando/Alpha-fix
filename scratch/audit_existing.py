import cv2
import numpy as np
from pathlib import Path

out_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\processed")

files = sorted(list(out_dir.glob("*.png")))
print(f"Total files in processed/: {len(files)}")

failed = []
for p in files:
    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] != 4:
        # Skip non-RGBA
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
        issues.append(f"corners not transparent (mean={corner_mean:.1f})")
    if center_opaque < 0.5:
        issues.append(f"center transparent (opaque={center_opaque*100:.1f}%)")
        
    if issues:
        failed.append((p.name, issues))

print(f"Failed files count: {len(failed)}")
for name, issues in failed:
    print(f"  {name}: {'; '.join(issues)}")
