import cv2

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

prev_color = gray[0, 10]
print(f"y=0: color={prev_color}")

count = 0
for y in range(1, h):
    color = gray[y, 10]
    # Check if we crossed a transition (threshold 165)
    if (color > 165) != (prev_color > 165):
        print(f"y={y:4d}: transition from {prev_color:3d} to {color:3d} (Square {count} -> {count+1})")
        count += 1
        prev_color = color

print(f"Total transitions at x=10: {count}")
