import sys
import os
import glob
from PIL import Image

def make_gif(frame_dir, output_gif):
    frames = sorted(glob.glob(os.path.join(frame_dir, "frame_*.png")))
    if not frames:
        print(f"No frames found in {frame_dir}")
        return
    imgs = [Image.open(f) for f in frames]
    imgs[0].save(output_gif, save_all=True, append_images=imgs[1:], duration=50, loop=0)
    print(f"Saved {output_gif}")

if __name__ == "__main__":
    make_gif(sys.argv[1], sys.argv[2])
