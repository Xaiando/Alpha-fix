with open("alpha_fix_2/pipeline.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Occurrences of checkerboard in pipeline.py:")
for idx, line in enumerate(lines):
    if "checkerboard" in line:
        print(f"Line {idx+1}: {line.strip()}")
