#!/bin/bash
mkdir -p /home/qntmqrks/rbx1_design/Phase14_Optimization/traj
/opt/conda/envs/rosetta_env/bin/python /home/qntmqrks/rbx1_design/Phase14_Optimization/animate_rosetta.py \
  /home/qntmqrks/rbx1_design/Phase13_Chai1/rfd_binder_61/pred.model_idx_1.pdb \
  --outdir /home/qntmqrks/rbx1_design/Phase14_Optimization/traj \
  > /home/qntmqrks/rbx1_design/Phase14_Optimization/traj.log 2>&1
