#!/bin/bash
# ============================================================
# CABS-flex on MD Trajectory Frames
# Feeds evenly-spaced frames from the 100ns MD as a multi-PDB
# input to CABS-flex, getting trajectory-aware RMSF.
#
# Usage: bash scripts/cabs_on_trajectory.sh superbinder|design9
# ============================================================

set -e
TARGET="${1:-superbinder}"

if [ "$TARGET" = "superbinder" ]; then
    TRAJ="assets/superbinder_anim.pdb"
    OUTDIR="data/cabs_traj_superbinder"
else
    TRAJ="assets/design_9_anim.pdb"
    OUTDIR="data/cabs_traj_design9"
fi

mkdir -p "$OUTDIR/frames"

echo ">>> Splitting trajectory: $TRAJ"
# Split multi-model PDB into individual frame files (every 5th frame = 20 frames)
python3 - "$TRAJ" "$OUTDIR/frames" 5 <<'PYEOF'
import sys, os

traj = sys.argv[1]
outdir = sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 5

os.makedirs(outdir, exist_ok=True)

frame_idx = 0
current = []
saved = 0

with open(traj) as f:
    for line in f:
        current.append(line)
        if line.startswith("ENDMDL"):
            if frame_idx % step == 0:
                out_path = os.path.join(outdir, f"frame_{frame_idx:03d}.pdb")
                with open(out_path, "w") as out:
                    out.writelines(current)
                saved += 1
            current = []
            frame_idx += 1

print(f"Extracted {saved} frames from {frame_idx} total to {outdir}/")
PYEOF
wait

echo ">>> Running CABS-flex on each frame (Parallel mode)..."
RMSF_ACCUMULATOR="$OUTDIR/combined_rmsf.csv"
: > "$RMSF_ACCUMULATOR"

MAX_JOBS=4
job_count=0

for pdb in "$OUTDIR/frames"/*.pdb; do
    fname=$(basename "$pdb" .pdb)
    echo "Starting $fname ..."
    
    (
        docker run --rm \
            -v "$(pwd)/$OUTDIR/frames:/input:ro" \
            -v "$(pwd)/$OUTDIR/${fname}_out:/home" \
            lcbio/cabsflex CABSflex \
                -i "/input/$(basename $pdb)" \
                -v 2 -w /home/cabs_out > /dev/null 2>&1
    ) &
    
    job_count=$((job_count + 1))
    if [ "$job_count" -ge "$MAX_JOBS" ]; then
        wait -n
        job_count=$((job_count - 1))
    fi
done
wait

echo ">>> Aggregating RMSF data..."
for pdb in "$OUTDIR/frames"/*.pdb; do
    fname=$(basename "$pdb" .pdb)
    RMSF="$OUTDIR/${fname}_out/cabs_out/plots/RMSF.csv"
    if [ -f "$RMSF" ]; then
        cat "$RMSF" >> "$RMSF_ACCUMULATOR"
    fi
done

echo ">>> Computing per-residue mean RMSF across trajectory frames..."
export OUTDIR
python3 - <<'PYEOF'
import os
from collections import defaultdict
import numpy as np

outdir = os.environ.get("OUTDIR")
combined = os.path.join(outdir, "combined_rmsf.csv")

per_res = defaultdict(list)
if os.path.exists(combined):
    with open(combined) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                per_res[parts[0]].append(float(parts[1]))

if not per_res:
    print("Error: No RMSF data accumulated.")
    sys.exit(1)

out = os.path.join(outdir, "trajectory_mean_rmsf.csv")
with open(out, "w") as f:
    f.write("residue\tmean_rmsf\tstd_rmsf\n")
    # Sort correctly by chain and residue number
    sorted_keys = sorted(per_res.keys(), key=lambda x: (x[0], int(x[1:])))
    for res in sorted_keys:
        v = np.array(per_res[res])
        f.write(f"{res}\t{v.mean():.3f}\t{v.std():.3f}\n")
print(f"Trajectory-averaged RMSF written to: {out}")
PYEOF
echo "Done! Results in: $OUTDIR/trajectory_mean_rmsf.csv"
