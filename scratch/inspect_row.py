import cv2
import numpy as np

def inspect_row(path):
    img = cv2.imread(path)
    if img is None:
        cap = cv2.VideoCapture(path)
        ok, img = cap.read()
        cap.release()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"\n{path}:")
    print("Row 0, col 0-64:")
    print(gray[0, :64])
    print("Row 16, col 0-64:")
    print(gray[16, :64])

inspect_row(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sparkle_joy.mp4")
inspect_row(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_cold.jpg")
inspect_row(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_angry.jpg")
inspect_row(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_sarcastic.png")
