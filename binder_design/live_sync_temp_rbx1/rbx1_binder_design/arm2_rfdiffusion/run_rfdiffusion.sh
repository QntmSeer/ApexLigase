#!/bin/bash
set -e
WORKDIR="$HOME/rbx1_binder_design"
RFDIFF_DIR="$WORKDIR/RFdiffusion"
MPNN_DIR="$WORKDIR/ProteinMPNN"
TARGET_PDB="$WORKDIR/target/rbx1_ring.pdb"
OUT_DIFF="$WORKDIR/outputs/arm2_rfdiffusion/backbones"
OUT_MPNN="$WORKDIR/outputs/arm2_rfdiffusion/sequences"
HOTSPOTS="'A43','A44','A46','A54','A55','A57','A58','A87','A91','A95','A96'"

mkdir -p "$OUT_DIFF" "$OUT_MPNN"
eval "$(conda shell.bash hook)"
conda activate rfdiffusion

python "$RFDIFF_DIR/scripts/run_inference.py" \
    inference.output_prefix="$OUT_DIFF/binder" \
    inference.model_directory_path="$RFDIFF_DIR/models" \
    inference.input_pdb="$TARGET_PDB" \
    'ppi.hotspot_res=['"$HOTSPOTS"']' \
    contigmap.contigs="[A40-108/0 60-100]" \
    inference.num_designs=300 \
    denoiser.noise_scale_ca=0.5 \
    denoiser.noise_scale_frame=0.5 \
    inference.ckpt_override_path="$RFDIFF_DIR/models/Base_ckpt.pt"
