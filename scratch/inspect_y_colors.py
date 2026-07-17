import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

transitions = [26, 51, 77, 102, 128, 154, 179, 205, 230, 256, 282, 307, 333, 358, 384, 409, 435, 461, 487, 512, 538, 563, 589, 614, 640, 666, 691, 717, 742, 768, 794, 819, 845, 870, 896, 922, 947, 973, 998]

# Let's sample a point in each square:
# Square 0: y=10
# Square i: average of transitions[i-1] and transitions[i]
# Last Square: y=1010

y_points = [10]
for i in range(1, len(transitions)):
    y_points.append((transitions[i-1] + transitions[i]) // 2)
y_points.append(1010)

print("Vertical squares color sequence at x=1014:")
for idx, y in enumerate(y_points):
    color = gray[y, 1014]
    color_type = "LIGHT" if color > 165 else "DARK"
    print(f"Square {idx:2d} (y={y:4d}): color={color:3d} ({color_type})")
