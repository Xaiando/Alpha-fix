import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
transcript_path = Path(r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\.system_generated\logs\transcript.jsonl")

steps = []
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            steps.append(data)
        except Exception as e:
            pass

for data in steps:
    step = data.get("step_index", 0)
    if 3510 <= step <= 3527:
        source = data.get("source")
        step_type = data.get("type")
        content = data.get("content", "")
        if content and content.strip():
            print(f"Step {step} ({step_type}, {source}):")
            print(content.strip())
            print("=" * 70)


