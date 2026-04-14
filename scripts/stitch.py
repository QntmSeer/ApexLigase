import imageio.v3 as iio
import os
import glob

frames = []
for i in range(1, 102):
    fname = f"data/frame_{i:03d}.png"
    if os.path.exists(fname):
        frames.append(iio.imread(fname))

if frames:
    output_path = "assets/superbinder_anim.gif"
    iio.imwrite(output_path, frames, duration=100, loop=0)
    print(f"GIF successfully stitched and saved to {output_path}")
else:
    print("No frames found to stitch!")
