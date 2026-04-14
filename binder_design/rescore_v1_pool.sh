#!/bin/bash
# ================================================================
# rescore_v1_pool.sh — Boltz2 rescore of all v1 RFdiffusion/MPNN outputs
#
# Run this on the HPC AFTER crunchy-peptides-v5 finishes.
# Rescores every sequence from the v1 pipeline with Boltz2 ipSAE.
# We likely have 10-20 more designs above 0.70 sitting in v1 outputs.
#
# Usage:
#   bash rescore_v1_pool.sh
# Output:
#   ~/rbx1_binder_design/outputs/v1_pool_boltz2_rescore.csv
# ================================================================
set -euo pipefail

WORKDIR="$HOME/rbx1_binder_design"
LOG="$WORKDIR/rescore_v1.log"
OUT_CSV="$WORKDIR/outputs/v1_pool_boltz2_rescore.csv"
BOLTZ_OUT="$WORKDIR/outputs/boltz2_rescore_pool"
RBX1_SEQ="VDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH"

mkdir -p "$BOLTZ_OUT"
eval "$(conda shell.bash hook)"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

# Ensure boltz2 env
if ! conda env list | grep -q "^boltz2 "; then
    log "Creating boltz2 env..."
    conda create -n boltz2 python=3.11 -y
    conda run -n boltz2 pip install boltz
fi

log "Collecting all v1 sequences from outputs/..."

# Extract all unique sequences from v1 outputs
python3 - <<PYEOF
import glob, os, csv
from pathlib import Path

workdir = Path.home() / "rbx1_binder_design"
all_seqs = []

# From all arm FASTAs
patterns = [
    "outputs/**/arm2_candidates.fasta",
    "outputs/**/arm2_rfdiffusion/**/*.fa",
    "outputs/**/arm1_bindcraft/**/*.fa*",
    "outputs/**/arm3_pepprclip/**/*.fa*",
    "outputs/**/arm5_esm3/**/*.fa*",
    "outputs/**/merged_candidates_top150.fasta",
    "outputs/**/chai1_validated.fasta",
    "outputs/**/final_candidates.fasta",
]

for pattern in patterns:
    for path in glob.glob(str(workdir / pattern), recursive=True):
        try:
            lines = open(path).readlines()
            for i in range(0, len(lines)-1, 2):
                hdr = lines[i].strip().lstrip('>')
                seq = lines[i+1].strip()
                if 40 <= len(seq) <= 150:
                    all_seqs.append({'name': hdr, 'seq': seq, 'source': Path(path).name})
        except Exception as e:
            print(f"  skip {path}: {e}")

# Complexity filter
charged = set('KRDEH')
hydro   = set('VILMFYW')
def passes(seq):
    run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1] and seq[i] in charged:
            run += 1
            if run >= 4: return False
        else:
            run = 1
    cf = sum(1 for aa in seq if aa in charged) / len(seq)
    hf = sum(1 for aa in seq if aa in hydro)   / len(seq)
    return cf <= 0.40 and hf >= 0.15

filtered = [s for s in all_seqs if passes(s['seq'])]

# Deduplicate
seen = set()
unique = []
for s in filtered:
    if s['seq'] not in seen:
        seen.add(s['seq'])
        unique.append(s)

# Write combined FASTA
out_fasta = workdir / "outputs/v1_pool_for_rescore.fasta"
with open(out_fasta, 'w') as f:
    for i, s in enumerate(unique):
        f.write(f">v1pool_{i:04d}|{s['name'][:60]}\n{s['seq']}\n")

print(f"Total collected  : {len(all_seqs)}")
print(f"After complexity : {len(filtered)}")
print(f"After dedup      : {len(unique)}")
print(f"Written to       : {out_fasta}")
PYEOF

POOL_FASTA="$WORKDIR/outputs/v1_pool_for_rescore.fasta"
POOL_SIZE=$(grep -c '^>' "$POOL_FASTA" 2>/dev/null || echo 0)
log "Pool size: $POOL_SIZE sequences to score"

# Boltz2 rescore in batch
log "Starting Boltz2 rescore..."
conda run -n boltz2 python3 "$HOME/apex_v2/binder_design/arm6_boltz2/run_boltz2_score.py" \
    --input "$POOL_FASTA" \
    --ipsae-cutoff 0.70 \
    2>&1 | tee -a "$LOG"

log "Rescore complete."
log "Results: $WORKDIR/outputs/boltz2_scores.csv"
log "Passing: $(grep -c 'True' $WORKDIR/outputs/boltz2_scores.csv 2>/dev/null || echo 0) designs >= 0.70 ipSAE"

# Notify
NTFY_TOPIC="apex-v2-$(hostname | tr -dc 'a-z0-9' | head -c8)"
PASS_COUNT=$(grep -c 'True' "$WORKDIR/outputs/boltz2_scores.csv" 2>/dev/null || echo "?")
curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
    -H "Title: ✅ v1 Pool Rescore Done" \
    -H "Priority: high" \
    -d "${PASS_COUNT} designs from v1 pool passed ipSAE >= 0.70" > /dev/null || true

log "Done."
