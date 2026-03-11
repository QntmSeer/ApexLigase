#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate bindcraft
export LD_LIBRARY_PATH="/home/shadeform/miniconda3/envs/bindcraft/lib/python3.10/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
export XLA_FLAGS="--xla_gpu_cuda_data_dir=/usr/local/cuda"
export TF_FORCE_GPU_ALLOW_GROWTH=true
cd ~/rbx1_binder_design/BindCraft
python bindcraft.py --settings ../arm1_bindcraft/rbx1_config.json
