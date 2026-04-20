import cv2
import numpy as np
from cv2 import VideoWriter_fourcc

# Video specifications
width, height = 1920, 1080
fps = 50
duration_sec = 10
num_frames = duration_sec * fps
output_file = "random_noise.mp4"


fourcc_chars = tuple(map(ord, "mp4v"))
fourcc = VideoWriter_fourcc(*fourcc_chars)
out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

print(f"Generating {num_frames} frames...")

for i in range(num_frames):
    # Generate random 8-bit noise (0-255)
    # Shape: (height, width, 3) for BGR color
    frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

    # Write the frame to the file
    out.write(frame)

# Release everything when job is finished
out.release()
print(f"Video saved as {output_file}")
