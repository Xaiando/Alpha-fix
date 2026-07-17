import cv2
import numpy as np

def check_file(path):
    cap = cv2.VideoCapture(path)
    ok, img = cap.read()
    cap.release()
    if not ok:
        print(f"Failed to read {path}")
        return
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"\nFile: {path}")
    print("Row 0, col 0-48:")
    print(gray[0, :48])
    print("Row 16, col 0-48:")
    print(gray[16, :48])
    print("Row 32, col 0-48:")
    print(gray[32, :48])

check_file(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_angry.mp4")
check_file(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_applause.mp4")
check_file(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_wink.mp4")
