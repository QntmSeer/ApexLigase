#!/bin/bash
# ================================================================
# run_v2.sh — ApexLigase Strategy v2 HPC Launch Script
#
# SAFE TO RUN ALONGSIDE v1 — completely separate WORKDIR.
# Does NOT touch: ~/rbx1_binder_design (v1 workspace)
#
# v2 changes vs v1:
#   - ARM 6 (Boltz2 ipSAE) added as PRIMARY filter
#   - Sequence complexity filter (no charge repeats)
#   - RFdiffusion: expanded hotspots, 500 designs vs 300
#   - MPNN: 3 temperatures (0.1, 0.2, 0.3), 5 seqs each
#   - ProteinMPNN diversification from design_9 seed (our grounded v1 hit)
#   - Boltz2 ipSAE >= 0.70 primary gate (replaces Chai-1 ipTM >= 0.60)
# ================================================================
set -euo pipefail

# ----------------------------------------------------------------
# Config — separate from v1
# ----------------------------------------------------------------
WORKDIR="$HOME/rbx1_binder_design_v2"
LOG="$WORKDIR/run_v2.log"
SCRIPTS="$HOME/apex_v2"          # synced from local via rsync
BG_PIDS=()

mkdir -p "$WORKDIR/outputs" "$WORKDIR/target"

log()     { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
section() { echo "" | tee -a "$LOG"; echo "================================================================" | tee -a "$LOG"; log "$*"; echo "================================================================" | tee -a "$LOG"; }
fail()    { log "FATAL: $*"; exit 1; }

# ----------------------------------------------------------------
# Notifications (ntfy.sh — same as v1, different tag)
# ----------------------------------------------------------------
NTFY_TOPIC="apex-v2-$(hostname | tr -dc 'a-z0-9' | head -c8)"
log "ntfy topic: https://ntfy.sh/$NTFY_TOPIC"
notify() {
    curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
        -H "Title: $1" -H "Priority: ${3:-default}" -H "Tags: dna" \
        -d "$2" > /dev/null 2>&1 || true
    log "[NOTIFY] $1 — $2"
}

eval "$(conda shell.bash hook)"

# ----------------------------------------------------------------
# Verify conda envs
# ----------------------------------------------------------------
section "Environment Check"
for env in rfdiffusion bioutils boltz2; do
    conda activate "$env" 2>/dev/null && log "  ✅ $env" || log "  ⚠️  $env not found — will create on first use"
    conda deactivate 2>/dev/null || true
done

# Create boltz2 env if missing
if ! conda env list | grep -q "^boltz2 "; then
    log "Creating boltz2 conda env..."
    conda create -n boltz2 python=3.11 -y
    conda run -n boltz2 pip install boltz
    log "boltz2 env ready."
fi

# ----------------------------------------------------------------
# STEP 0: Stage target PDB (copy from v1 if exists, else download)
# ----------------------------------------------------------------
section "STEP 0: Target PDB"
TARGET_PDB="$WORKDIR/target/rbx1_ring.pdb"
if [ ! -f "$TARGET_PDB" ]; then
    V1_TARGET="$HOME/rbx1_binder_design/target/rbx1_ring.pdb"
    if [ -f "$V1_TARGET" ]; then
        cp "$V1_TARGET" "$TARGET_PDB"
        log "Copied rbx1_ring.pdb from v1 workspace."
    else
        conda run -n bioutils python3 "$SCRIPTS/02_prep_target.py" --outdir "$WORKDIR/target"
        log "rbx1_ring.pdb downloaded from PDB."
    fi
fi

# ----------------------------------------------------------------
# STEP 1: ProteinMPNN diversification of design_9 (v1 grounded seed)
#
# design_9 is our ONLY grounded design (experimental grounding 0.76).
# Generate 50 variants at 3 temperatures to explore sequence space
# around that backbone without losing the interface geometry.
# ----------------------------------------------------------------
section "STEP 1: design_9 Backbone Diversification (ARM 0 — seed)"
SEED_PDB="$HOME/rbx1_binder_design/data/candidates/design_9/design_9_complex.pdb"
SEED_OUT="$WORKDIR/outputs/arm0_seed"
mkdir -p "$SEED_OUT"

if [ -f "$SEED_PDB" ]; then
    log "Running ProteinMPNN on design_9 backbone (50 seqs × 3 temps)..."
    for TEMP in 0.1 0.2 0.3; do
        conda run -n rfdiffusion python \
            "$HOME/rbx1_binder_design/ProteinMPNN/protein_mpnn_run.py" \
            --pdb_path "$SEED_PDB" \
            --chain_id_jsonl /dev/null \
            --fixed_positions_jsonl /dev/null \
            --out_folder "$SEED_OUT/temp_${TEMP}" \
            --num_seq_per_target 17 \
            --sampling_temp "$TEMP" \
            --seed 42 \
            --batch_size 8 2>&1 | tee -a "$LOG"
    done
    log "design_9 diversification complete."
    SEED_COUNT=$(find "$SEED_OUT" -name "*.fa" | wc -l)
    notify "✅ ARM 0 Done" "design_9 seed diversified: ~${SEED_COUNT} variant files." low
else
    log "WARNING: design_9 PDB not found at $SEED_PDB — skipping seed arm."
fi

# ----------------------------------------------------------------
# STEP 2: ARM 2 — RFdiffusion (v2 config: 500 designs, RING hotspots)
#
# v2 changes:
#   - 500 designs (up from 300)
#   - contigs 80-120 AA (up from 60-100, targets optimal winning range)
#   - noise_scale reduced to 0.5 for tighter interface conditioning
#   - hotspot_res unchanged (already had RING residues in v1)
# ----------------------------------------------------------------
section "STEP 2: ARM 2 — RFdiffusion v2 (500 designs, 80-120 AA)"
OUT_DIFF="$WORKDIR/outputs/arm2_rfdiffusion/backbones"
OUT_MPNN="$WORKDIR/outputs/arm2_rfdiffusion/sequences"
mkdir -p "$OUT_DIFF" "$OUT_MPNN"

conda activate rfdiffusion

python "$HOME/rbx1_binder_design/RFdiffusion/scripts/run_inference.py" \
    inference.output_prefix="$OUT_DIFF/binder" \
    inference.model_directory_path="$HOME/rbx1_binder_design/RFdiffusion/models" \
    inference.input_pdb="$WORKDIR/target/rbx1_ring.pdb" \
    'ppi.hotspot_res=["A43","A44","A46","A54","A55","A57","A58","A87","A91","A95","A96"]' \
    contigmap.contigs="[A40-108/0 80-120]" \
    inference.num_designs=500 \
    denoiser.noise_scale_ca=0.5 \
    denoiser.noise_scale_frame=0.5 \
    inference.ckpt_override_path="$HOME/rbx1_binder_design/RFdiffusion/models/Base_ckpt.pt" \
    2>&1 | tee -a "$LOG"

conda deactivate
log "RFdiffusion complete: $(ls $OUT_DIFF/*.pdb 2>/dev/null | wc -l) backbones"
notify "✅ ARM 2 Done" "$(ls $OUT_DIFF/*.pdb 2>/dev/null | wc -l) RFdiffusion backbones generated." default

# ----------------------------------------------------------------
# STEP 3: ProteinMPNN on RFdiffusion backbones (3 temps)
# ----------------------------------------------------------------
section "STEP 3: ProteinMPNN on RFdiffusion backbones"

for TEMP in 0.1 0.2 0.3; do
    conda run -n rfdiffusion python \
        "$HOME/rbx1_binder_design/ProteinMPNN/protein_mpnn_run.py" \
        --pdb_path_multi <(ls "$OUT_DIFF"/*.pdb | head -200 | tr '\n' ',' | sed 's/,$//') \
        --out_folder "$OUT_MPNN/temp_${TEMP}" \
        --num_seq_per_target 5 \
        --sampling_temp "$TEMP" \
        --seed 42 \
        --batch_size 16 2>&1 | tee -a "$LOG"
done

log "ProteinMPNN done."

# ----------------------------------------------------------------
# STEP 4: Merge all candidates (ARM 0 seed + ARM 2 RFdiff/MPNN)
# ----------------------------------------------------------------
section "STEP 4: Merge all candidates → pre-filter pool"

python3 - <<'PYEOF'
import glob, os, re
from pathlib import Path

workdir = Path.home() / "rbx1_binder_design_v2"
seed_dir = workdir / "outputs/arm0_seed"
mpnn_dir = workdir / "outputs/arm2_rfdiffusion/sequences"
out_fasta = workdir / "outputs/merged_v2_candidates.fasta"

seqs = []

# Collect from seed arm
for fa in list(seed_dir.glob("**/*.fa")):
    lines = open(fa).readlines()
    for i in range(0, len(lines)-1, 2):
        seq = lines[i+1].strip()
        if 60 <= len(seq) <= 150:
            seqs.append(("seed_" + fa.stem, seq))

# Collect from RFdiff/MPNN arm
for fa in list(mpnn_dir.glob("**/*.fa")):
    lines = open(fa).readlines()
    for i in range(0, len(lines)-1, 2):
        seq = lines[i+1].strip()
        if 60 <= len(seq) <= 150:
            seqs.append(("rfd_" + fa.stem, seq))

# Complexity filter
charged = set("KRDEH")
hydro   = set("VILMFYW")
passed  = []
for name, seq in seqs:
    # reject charge runs >= 4
    run = 1
    bad = False
    for j in range(1, len(seq)):
        if seq[j] == seq[j-1] and seq[j] in charged:
            run += 1
            if run >= 4:
                bad = True; break
        else:
            run = 1
    if bad: continue
    if sum(1 for aa in seq if aa in charged)/len(seq) > 0.45: continue
    if sum(1 for aa in seq if aa in hydro)/len(seq) < 0.15: continue
    passed.append((name, seq))

# Deduplicate
seen = set()
unique = []
for name, seq in passed:
    if seq not in seen:
        seen.add(seq)
        unique.append((name, seq))

out_fasta.parent.mkdir(parents=True, exist_ok=True)
with open(out_fasta, "w") as f:
    for i, (name, seq) in enumerate(unique):
        f.write(f">v2_{i:04d}|{name}\n{seq}\n")

print(f"Total collected : {len(seqs)}")
print(f"After complexity filter : {len(passed)}")
print(f"After dedup : {len(unique)}")
print(f"Written to  : {out_fasta}")
PYEOF

notify "✅ Merge Done" "$(grep -c '^>' $WORKDIR/outputs/merged_v2_candidates.fasta) candidates after complexity filter." default

# ----------------------------------------------------------------
# STEP 5: ARM 6 — Boltz2 ipSAE scoring (PRIMARY filter, v2)
# ----------------------------------------------------------------
section "STEP 5: ARM 6 — Boltz2 ipSAE Scoring (PRIMARY gate, cutoff=0.70)"
conda run -n boltz2 python3 "$SCRIPTS/arm6_boltz2/run_boltz2_score.py" \
    --input "$WORKDIR/outputs/merged_v2_candidates.fasta" \
    --ipsae-cutoff 0.70 \
    2>&1 | tee -a "$LOG"

BOLTZ_PASS=$(grep -c "True" "$WORKDIR/outputs/boltz2_scores.csv" 2>/dev/null || echo "?")
notify "✅ Boltz2 Done" "${BOLTZ_PASS} sequences passed ipSAE >= 0.70." high

# ----------------------------------------------------------------
# STEP 6: Chai-1 cross-check on Boltz2 survivors (secondary confirmation)
# ----------------------------------------------------------------
section "STEP 6: Chai-1 cross-check on Boltz2 survivors"
conda run -n chai1 python3 "$HOME/rbx1_binder_design/binder_design/validate_chai1.py" \
    2>&1 | tee -a "$LOG" || log "WARNING: Chai-1 step failed or skipped."

# ----------------------------------------------------------------
# STEP 7: Final ranking & submission prep
# ----------------------------------------------------------------
section "STEP 7: Final Ranking"
python3 - <<'PYEOF'
import csv
from pathlib import Path

workdir = Path.home() / "rbx1_binder_design_v2"
b2_csv  = workdir / "outputs/boltz2_scores.csv"
out_csv = workdir / "outputs/submission_v2.csv"

results = []
with open(b2_csv) as f:
    for row in csv.DictReader(f):
        ipsae = float(row.get("boltz2_ipsae") or 0)
        plddt = float(row.get("boltz2_plddt") or 0)
        if row.get("passes_boltz2") == "True":
            results.append({**row, "_score": ipsae*0.7 + (plddt/100)*0.3})

results.sort(key=lambda r: r["_score"], reverse=True)
top10 = results[:10]

with open(out_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["rank","name","sequence","length",
                                            "boltz2_ipsae","boltz2_plddt"])
    writer.writeheader()
    for i, r in enumerate(top10):
        writer.writerow({"rank": i+1, "name": r["name"], "sequence": r["sequence"],
                         "length": r["length"],
                         "boltz2_ipsae": r["boltz2_ipsae"],
                         "boltz2_plddt": r["boltz2_plddt"]})

print(f"\nTop 10 by Boltz2 ipSAE:")
for r in top10:
    print(f"  ipSAE={r['boltz2_ipsae']}  pLDDT={r['boltz2_plddt']}  "
          f"len={r['length']}  {r['sequence'][:40]}...")
print(f"\nWritten: {out_csv}")
PYEOF

# ----------------------------------------------------------------
# DONE
# ----------------------------------------------------------------
section "v2 PIPELINE COMPLETE — $(date)"
log "Outputs  : $WORKDIR/outputs/"
log "Submit   : $WORKDIR/outputs/submission_v2.csv"
notify "🏁 v2 COMPLETE!" "Strategy v2 pipeline done. submission_v2.csv ready." urgent
