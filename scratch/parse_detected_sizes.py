import re

log_path = r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\.system_generated\tasks\task-2827.log"
with open(log_path, 'r', encoding='utf-8') as f:
    log = f.read()

# Find matches of "[Checkerboard] Detected size=..., offset=(..., ...)"
matches = re.findall(r"\[Checkerboard\] Detected size=(\d+), offset=\((\d+), (\d+)\)", log)
print(f"Total checkerboard detections: {len(matches)}")
print("Detections (size, offset_x, offset_y):")
from collections import Counter
c = Counter(matches)
for k, v in c.most_common(20):
    print(f"  {k}: {v} times")
