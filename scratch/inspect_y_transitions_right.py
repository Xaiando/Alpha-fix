import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Let's trace transitions along x = 1014
transitions = []
prev_state = 1 if gray[0, 1014] > 165 else 0

for y in range(1, h):
    state = 1 if gray[y, 1014] > 165 else 0
    if state != prev_state:
        transitions.append(y)
        prev_state = state

print("Transitions at x=1014:")
print(transitions)
print("Differences:")
print(np.diff(transitions))
