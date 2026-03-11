#!/bin/bash
# ================================================================
# Arm 1: BindCraft — Primary Binder Design (AF2 Hallucination)
# Target: 50 binder sequences against RBX1 RING domain
# Expected success rate: 30-50% experimental (Nature 2025 paper)
# ================================================================
set -e
WORKDIR="$HOME/rbx1_binder_design"
BINDCRAFT_DIR="$WORKDIR/BindCraft"
CONFIG="$WORKDIR/arm1_bindcraft/rbx1_config.json"
OUT_DIR="$WORKDIR/outputs/arm1_bindcraft"

mkdir -p "$OUT_DIR"
cd "$BINDCRAFT_DIR"

echo "================================================================"
echo "ARM 1: BindCraft — RBX1 Binder Hallucination"
echo "Config: $CONFIG"
echo "Output: $OUT_DIR"
echo "================================================================"

eval "$(conda shell.bash hook)"
conda activate bindcraft

# Run BindCraft with our RBX1 config
python bindcraft.py \
    --settings "$CONFIG" \
    --output_dir "$OUT_DIR" \
    --gpu 0

echo ""
echo "================================================================"
echo "BindCraft finished! Results in: $OUT_DIR"
echo "Check accepted_designs/ subdirectory for passing candidates"
echo "================================================================"

# Summarise results
python - <<'PYEOF'
import os, json, glob

out_dir = os.environ.get('OUT_DIR', 'outputs/arm1_bindcraft')
accepted = glob.glob(os.path.join(out_dir, 'accepted_designs', '*.pdb'))
print(f"  Accepted designs: {len(accepted)}")

scores_file = os.path.join(out_dir, 'all_scores.csv')
if os.path.exists(scores_file):
    import csv
    with open(scores_file) as f:
        rows = list(csv.DictReader(f))
    passing = [r for r in rows if float(r.get('iptm', 0)) > 0.70]
    print(f"  Designs with ipTM > 0.70: {len(passing)}")
    print(f"  Top 5 by ipTM:")
    passing.sort(key=lambda r: float(r.get('iptm', 0)), reverse=True)
    for r in passing[:5]:
        print(f"    {r.get('name','?')}  ipTM={r.get('iptm','?')}  pLDDT={r.get('plddt','?')}")
PYEOF
