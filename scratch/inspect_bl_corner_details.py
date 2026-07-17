import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

print("Grayscale values in bottom-left corner at x=10, y=980..1023:")
for y in range(980, 1024):
    print(f"y={y:4d}: gray={gray[y, 10]}")
