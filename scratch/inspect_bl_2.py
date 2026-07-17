import cv2
import numpy as np

img = cv2.imread(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Parameters
size = 25.68
off_x = 22.5
off_y = -1.0

print("Bottom-left corner grid (y=1000..1009, x=0..9):")
print("Format: Actual / ExpectedPhase / CalculatedPhase")

for y in range(1000, 1010):
    row_strs = []
    for x in range(10):
        actual = gray[y, x]
        # In this script, color1 (around 147) is phase 0, color2 (around 185) is phase 1.
        # So actual > 165 should be phase 1, actual <= 165 should be phase 0!
        actual_phase = 1 if actual > 165 else 0
        calc_phase = int((np.floor((x - off_x) / size) + np.floor((y - off_y) / size)) % 2)
        row_strs.append(f"{actual:3d}:{actual_phase}:{calc_phase}")
    print(" | ".join(row_strs))
