import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

size = 25.6000
off_x = 25.00
off_y = -0.60

def inspect(y, x):
    x_val = (x - off_x) / size
    y_val = (y - off_y) / size
    x_term = np.floor(x_val)
    y_term = np.floor(y_val)
    phase = (x_term + y_term) % 2
    actual = gray[y, x]
    print(f"y={y:4d}, x={x:4d}: actual={actual:3d}, x_val={x_val:6.2f} (floor={x_term:3.0f}), y_val={y_val:6.2f} (floor={y_term:3.0f}), phase={phase:.0f}")

print("--- Top-Left Corner ---")
inspect(10, 10)
inspect(10, 30)
inspect(30, 10)
inspect(30, 30)

print("\n--- Bottom-Left Corner ---")
inspect(1010, 10)
inspect(1010, 30)
inspect(980, 10)
inspect(980, 30)
