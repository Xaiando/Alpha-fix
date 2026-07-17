import cv2

img = cv2.imread(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

print("Top-left 15x15 pixel grid of gray values:")
for y in range(15):
    row_vals = [f"{gray[y, x]:3d}" for x in range(15)]
    print(" ".join(row_vals))
