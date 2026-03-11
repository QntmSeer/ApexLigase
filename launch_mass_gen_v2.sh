#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh
conda activate SE3nv
cd /home/qntmqrks/rbx1_design/rbx1_binder_design/RFdiffusion

# Calculate how many already exist
EXISTING=$(ls /home/qntmqrks/rbx1_design/Phase15_MassGeneration/backbones/*.pdb 2>/dev/null | wc -l)
TOTAL=500
REMAINING=$((TOTAL - EXISTING))

if [ $REMAINING -le 0 ]; then
    echo "All 500 designs complete."
    exit 0
fi

echo "Resuming generation: $EXISTING complete, $REMAINING to go."

# Note: Using a numerical offset in the name to avoid collisions
python scripts/run_inference.py \
    inference.output_prefix=/home/qntmqrks/rbx1_design/Phase15_MassGeneration/backbones/batch2_design \
    inference.num_designs=$REMAINING \
    inference.input_pdb=/home/qntmqrks/rbx1_design/rbx1_binder_design/target/rbx1_ring.pdb \
    'contigmap.contigs=[A40-108/0 60-100]' \
    'ppi.hotspot_res=[A43,A44,A46,A54,A55,A57,A58,A87,A91,A95,A96]' \
    denoiser.noise_scale_ca=0.5 \
    denoiser.noise_scale_frame=0.5
