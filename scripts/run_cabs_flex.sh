#!/bin/bash
# Script to prepare and run CABS-flex on the Super-Binder using Docker

# Extract the first frame of the input trajectories
awk '/ENDMDL/{print; exit} {print}' assets/superbinder_anim.pdb > data/superbinder_input.pdb
awk '/ENDMDL/{print; exit} {print}' assets/design_9_anim.pdb > data/design_9_input.pdb

echo "Pulling CABS-flex Docker image..."
docker pull lcbio/cabsflex

echo "Running CABS-flex rapid flexibility test via Docker..."
docker run --rm -v \$(pwd)/data:/home lcbio/cabsflex CABSflex -i /home/design_9_input.pdb -v 4 -w /home/cabs_output_d9
docker run --rm -v \$(pwd)/data:/home lcbio/cabsflex CABSflex -i /home/superbinder_input.pdb -v 4 -w /home/cabs_output_superbinder

echo ""
