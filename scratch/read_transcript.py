from pathlib import Path

log_path = Path(r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\.system_generated\tasks\task-3938.log")
if log_path.exists():
    text = log_path.read_text('utf-8')
    failed_names = [
        "emoji_detective.jpg",
        "emoji_got_it_cool_32.png",
        "emoji_mindblown.jpg",
        "emoji_salute_1.jpg",
        "emoji_sleeping_1.jpg",
        "emoji_tired_salute.png",
        "emoji_wink.jpg",
        "gao8bEg - Imgur(1).png",
        "teledra-emoji-fight-cute.jpg",
        "teledra-emoji-fight-you.jpg"
    ]
    
    # We will search for sections starting with "--- name ---" to the next "---"
    sections = text.split("--- ")
    for section in sections:
        for name in failed_names:
            if section.startswith(name):
                print(f"=== {name} ===")
                print(section.strip())
                print("=" * 40)
else:
    print("Log not found")
