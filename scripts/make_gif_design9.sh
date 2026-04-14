#!/bin/bash
rm -f data/frame_d9_*.png
echo "Rendering Design 9 trajectory in PyMOL..."
pymol -cq scripts/render_design9.pml
echo "Stitching GIF..."
convert -dispose Background -delay 10 -loop 0 data/frame_d9_*.png assets/design_9_animation_v2.gif
rm -f data/frame_d9_*.png
echo "Copying to artifacts..."
cp assets/design_9_animation_v2.gif /mnt/c/Users/Gebruiker/.gemini/antigravity/brain/6d7c4b60-669a-4a05-ab38-a1dead1613d0/design_9_animation_v2.gif
echo "Done!"
