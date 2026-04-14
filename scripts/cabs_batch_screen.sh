#!/bin/bash
# ============================================================
# CABS-flex Batch Screener
# Inputs: a directory of binder PDB files (with RBX1 as chain A)
# Outputs: per-candidate RMSF summary + ranked CSV
# Usage: bash scripts/cabs_batch_screen.sh data/candidates/
# ============================================================

set -e
CANDIDATES_DIR="${1:-data/candidates}"
OUT_ROOT="$(pwd)/data/cabs_screen_$(date +%Y%m%d_%H%M)"
RESULTS_CSV="${OUT_ROOT}/screening_results.csv"

mkdir -p "$OUT_ROOT"
echo "name,max_rmsf_binder,mean_rmsf_binder,max_rmsf_interface,n_residues_binder" > "$RESULTS_CSV"

echo ">>> Running CABS-flex for all candidates (Parallel mode)..."
MAX_JOBS=4
job_count=0

for pdb in "$CANDIDATES_DIR"/*.pdb; do
    name=$(basename "$pdb" .pdb)
    out_dir="${OUT_ROOT}/${name}"
    mkdir -p "$out_dir"
    echo "Starting $name ..."
    
    (
        docker run --rm \
            -v "$(pwd)/$(dirname $pdb):/input:ro" \
            -v "${out_dir}:/home" \
            lcbio/cabsflex CABSflex \
                -i "/input/$(basename $pdb)" \
                -v 2 \
                -w /home/cabs_out > /dev/null 2>&1
    ) &

    job_count=$((job_count + 1))
    if [ "$job_count" -ge "$MAX_JOBS" ]; then
        wait -n
        job_count=$((job_count - 1))
    fi
done
wait

echo ">>> Processing results..."
for pdb in "$CANDIDATES_DIR"/*.pdb; do
    name=$(basename "$pdb" .pdb)
    out_dir="${OUT_ROOT}/${name}"
    RMSF_CSV="${out_dir}/cabs_out/plots/RMSF.csv"
    if [ -f "$RMSF_CSV" ]; then
        python3 -c "
import sys
data = []
with open('${RMSF_CSV}') as f:
    for line in f:
        parts = line.strip().split()
        if len(parts)==2 and parts[0].startswith('B'):
            data.append(float(parts[1]))
if data:
    mx = max(data)
    mn = sum(data)/len(data)
    iface = sum(data[:10])/min(10,len(data))
    print(f'${name},{mx:.3f},{mn:.3f},{iface:.3f},{len(data)}')
else:
    print(f'${name},NA,NA,NA,0')
" >> "$RESULTS_CSV"
    else
        echo "${name},ERROR,ERROR,ERROR,0" >> "$RESULTS_CSV"
    fi
done

echo ""
echo "=== Screening complete: $RESULTS_CSV ==="
echo "Top 10 by lowest binder RMSF (most rigid):"
sort -t',' -k2 -n "$RESULTS_CSV" | head -11
