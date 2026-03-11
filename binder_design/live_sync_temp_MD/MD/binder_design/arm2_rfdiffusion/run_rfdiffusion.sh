#!/bin/bash
# ================================================================
# Arm 2: RFdiffusion → ProteinMPNN → AF2 Multimer
# Target: 30 binder sequences
# ================================================================
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

echo "================================================================"
echo "ARM 2A: RFdiffusion — Backbone Generation (300 scaffolds)"
echo "================================================================"
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

echo "RFdiffusion done: $(ls $OUT_DIFF/*.pdb | wc -l) backbones generated"

echo ""
echo "================================================================"
echo "ARM 2B: ProteinMPNN — Sequence Design (5 seqs per backbone)"
echo "================================================================"
# Run ProteinMPNN on all generated backbones
# Two temperatures: 0.1 (conservative) and 0.3 (diverse)
for TEMP in 0.1 0.3; do
    conda run -n rfdiffusion python "$MPNN_DIR/protein_mpnn_run.py" \
        --pdb_path_multi <(ls "$OUT_DIFF"/*.pdb | head -150 | tr '\n' ',' | sed 's/,$//') \
        --out_folder "$OUT_MPNN/temp_${TEMP}" \
        --num_seq_per_target 5 \
        --sampling_temp "$TEMP" \
        --seed 42 \
        --batch_size 16
done

echo "ProteinMPNN done."

echo ""
echo "================================================================"
echo "ARM 2C: Merge sequences → mpnn_candidates.fasta"
echo "================================================================"
python3 - <<'PYEOF'
import glob, os

out_mpnn = os.path.expanduser("~/rbx1_binder_design/outputs/arm2_rfdiffusion/sequences")
out_fasta = os.path.expanduser("~/rbx1_binder_design/outputs/arm2_candidates.fasta")

seqs = []
for fa in glob.glob(f"{out_mpnn}/**/*.fa", recursive=True):
    with open(fa) as f:
        lines = f.readlines()
    for i in range(0, len(lines)-1, 2):
        name = lines[i].strip().lstrip('>')
        seq = lines[i+1].strip()
        if 60 <= len(seq) <= 250:
            seqs.append((name, seq))

# Deduplicate
seen = set()
unique = []
for name, seq in seqs:
    if seq not in seen:
        seen.add(seq)
        unique.append((name, seq))

with open(out_fasta, "w") as f:
    for i, (name, seq) in enumerate(unique):
        f.write(f">arm2_{i:04d}|{name}\n{seq}\n")

print(f"Wrote {len(unique)} unique sequences to {out_fasta}")
PYEOF
