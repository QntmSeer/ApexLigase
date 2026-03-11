#!/bin/bash
mkdir -p /home/qntmqrks/rbx1_design/Phase14_Optimization
/opt/conda/envs/rosetta_env/bin/python /home/qntmqrks/rbx1_design/Phase14_Optimization/fast_relax.py \
  /home/qntmqrks/rbx1_design/Phase13_Chai1/rfd_binder_61/pred.model_idx_1.pdb \
  --outdir /home/qntmqrks/rbx1_design/Phase14_Optimization/rfd_binder_61_relax \
  > /home/qntmqrks/rbx1_design/Phase14_Optimization/relax.log 2>&1
