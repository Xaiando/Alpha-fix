"""
Find source files that don't have a corresponding output in processed/.
Uses the same collision-resolution logic as batch_process.py.
"""
from pathlib import Path
from collections import Counter

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
out_dir = src_dir / "processed"

valid_suffixes = {".mp4", ".png", ".jpg", ".jpeg"}
all_files = sorted([
    f for f in src_dir.iterdir()
    if f.is_file() and f.suffix.lower() in valid_suffixes
])

stem_counts = Counter(f.stem for f in all_files)

missing = []
for file_path in all_files:
    stem = file_path.stem
    ext = file_path.suffix.lower()
    if stem_counts[stem] > 1:
        output_base_name = f"{stem}_{ext.lstrip('.')}"
    else:
        output_base_name = stem

    is_video = ext in (".mp4", ".mov", ".avi", ".mkv")
    if is_video:
        # Videos produce .webm and .mov
        webm = out_dir / f"{output_base_name}.webm"
        mov  = out_dir / f"{output_base_name}.mov"
        if not webm.exists() and not mov.exists():
            missing.append(file_path)
    else:
        png = out_dir / f"{output_base_name}.png"
        if not png.exists():
            missing.append(file_path)

print(f"Missing outputs: {len(missing)}")
for f in missing:
    print(f"  {f.name}")
