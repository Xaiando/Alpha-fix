import cv2
import os

overlay_dir = r"C:\Users\Kaged\Documents\Projects\Overlay"
out_dir = r"C:\Users\Kaged\.gemini\antigravity\brain\9c45762a-e3b1-49b7-8965-96fb787a6613\artifacts"

files = [
    "Hailuo_Image_Make me a stream overlay conta_494485647038263305.jpg",
    "Hailuo_Video_Animate it for me keep it aliv_486914013302788101.mp4",
    "Hailuo_Video_Animate it, make environment c_486899422074089472.mp4",
    "Hailuo_Video_Animate this stream overlay_486850021716779018.mp4",
    "Shroom.mp4"
]

for filename in files:
    path = os.path.join(overlay_dir, filename)
    if not os.path.exists(path):
        print(f"Skipping {filename} (does not exist)")
        continue
    
    if filename.endswith(".jpg"):
        img = cv2.imread(path)
        if img is not None:
            out_name = filename.replace(".jpg", "_first.png")
            cv2.imwrite(os.path.join(out_dir, out_name), img)
            print(f"Saved {out_name}")
    else:
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            out_name = filename.replace(".mp4", "_first.png")
            cv2.imwrite(os.path.join(out_dir, out_name), frame)
            print(f"Saved {out_name}")
        else:
            print(f"Failed to read video {filename}")
