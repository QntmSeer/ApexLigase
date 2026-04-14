#!/bin/bash
source ~/miniconda3/bin/activate
echo "Installing PyMOL and imageio..."
conda config --remove channels defaults || true
conda config --add channels conda-forge
conda install pymol-open-source imageio -y

echo "Running PyMOL to generate PNG frames..."
pymol -cq scripts/render.pml

echo "Stitching GIF with Python..."
python scripts/stitch.py

echo "Cleaning up frames..."
rm -f data/frame_*.png
