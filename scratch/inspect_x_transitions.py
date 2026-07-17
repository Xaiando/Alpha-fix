import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

def find_transitions_x(y):
    transitions = []
    prev_state = 1 if gray[y, 0] > 165 else 0
    for x in range(1, w):
        state = 1 if gray[y, x] > 165 else 0
        if state != prev_state:
            transitions.append(x)
            prev_state = state
    return transitions

print("Top-left transitions at y=10:")
trans_top = find_transitions_x(10)
print(trans_top[:15])

print("\nBottom-left transitions at y=1010:")
trans_bot = find_transitions_x(1010)
print(trans_bot[:15])
