import cv2
import numpy as np

def copy_frame():
    input_path = "C:/Users/Kaged/Movies/Hub/Projects/image-remix/emoji_sparkle_joy.mp4"
    cap = cv2.VideoCapture(input_path)
    for _ in range(50):
        ret, frame = cap.read()
    cap.release()
    output_path = "C:/Users/Kaged/.gemini/antigravity/brain/9c45762a-e3b1-49b7-8965-96fb787a6613/artifacts/emoji_sparkle_joy_original_00050.png"
    cv2.imwrite(output_path, frame)
    print("Saved original frame to:", output_path)

if __name__ == "__main__":
    copy_frame()
