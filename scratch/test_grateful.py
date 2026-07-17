import cv2
import numpy as np
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.pipeline import AlphaFix2Processor

# Load input
file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)
print("Input shape:", img_in.shape)

config = AlphaFix2Config(
    mode="overlay",
    overlay_method="checkerboard",
    checkerboard_low=15.0,
    checkerboard_high=25.0,
    checkerboard_size=0,
    checkerboard_offset_x=-1,
    checkerboard_offset_y=-1,
    export_alpha_matte=True
)

processor = AlphaFix2Processor(config)
result = processor.process_frame(img_in)
alpha = result.alpha
rgba = result.rgba

print("Alpha min:", alpha.min(), "max:", alpha.max())
print("Fully transparent pixels (alpha == 0):", np.sum(alpha == 0))
print("Fully opaque pixels (alpha == 1.0):", np.sum(alpha == 1.0))
print("Semi-transparent pixels (0 < alpha < 1):", np.sum((alpha > 0) & (alpha < 1)))

# Let's save the alpha map and the RGBA result
cv2.imwrite("scratch/grateful_alpha.png", (alpha * 255.0).astype(np.uint8))
cv2.imwrite("scratch/grateful_rgba.png", rgba)
print("Saved outputs to scratch/grateful_alpha.png and scratch/grateful_rgba.png")
