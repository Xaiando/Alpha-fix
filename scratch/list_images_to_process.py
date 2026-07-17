import cv2
import numpy as np
from pathlib import Path
from collections import Counter

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
out_dir = src_dir / "processed"

all_dir_files = list(src_dir.iterdir())
stem_counts = Counter(f.stem for f in all_dir_files if f.is_file())

valid_suffixes = {".png", ".jpg", ".jpeg"}
all_image_files = sorted([
    f for f in all_dir_files
    if f.is_file() and f.suffix.lower() in valid_suffixes
])

def audit_png(path):
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] != 4:
        return False, ["not RGBA"]
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
    return len(issues) == 0, issues

to_process = []
for file_path in all_image_files:
    if file_path.name == "gao8bEg - Imgur(1).png":
        # Ignore this known explorer screenshot
        continue
    stem = file_path.stem
    ext = file_path.suffix.lower()
    if stem_counts[stem] > 1:
        output_base_name = f"{stem}_{ext.lstrip('.')}"
    else:
        output_base_name = stem
    dst = out_dir / f"{output_base_name}.png"
    
    if not dst.exists():
        to_process.append((file_path, "missing"))
    else:
        passed, issues = audit_png(dst)
        if not passed:
            to_process.append((file_path, f"failed audit: {'; '.join(issues)}"))

print(f"Total images needing processing: {len(to_process)}")
for f, reason in to_process:
    print(f"  {f.name} ({reason})")
