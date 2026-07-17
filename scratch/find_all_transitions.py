import cv2
import numpy as np

img = cv2.imread(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Let's trace transitions along x = 10
transitions = []
prev_state = 1 if gray[0, 10] > 165 else 0

for y in range(1, h):
    state = 1 if gray[y, 10] > 165 else 0
    if state != prev_state:
        # We found a transition!
        transitions.append(y)
        prev_state = state

print("Detected transition y-indices:")
print(transitions)
print("Differences between consecutive transitions (square heights):")
diffs = np.diff(transitions)
print(diffs)
print("Mean square height:", np.mean(diffs))
