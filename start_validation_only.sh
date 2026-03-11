#!/bin/bash

# Configuration
PROJECT_DIR="/home/qntmqrks/rbx1_design/Phase15_MassGeneration"
BIN_DIR="$PROJECT_DIR/HARDENED_v1/bin"
REPORT_FILE="$PROJECT_DIR/leaderboard.csv"
CONDA_SH="/opt/conda/etc/profile.d/conda.sh"

# 1. Deduplicate Leaderboard (Using shell sort to be dependency-free)
echo "Deduplicating leaderboard..."
if [ -f "$REPORT_FILE" ]; then
    head -n 1 "$REPORT_FILE" > "$REPORT_FILE.new"
    tail -n +2 "$REPORT_FILE" | sort -t, -k1,1 -u >> "$REPORT_FILE.new"
    mv "$REPORT_FILE.new" "$REPORT_FILE"
fi

# 2. Kill stale sessions
tmux kill-session -t prod_gen 2>/dev/null
tmux kill-session -t prod_watchdog 2>/dev/null
tmux kill-session -t prod_folding 2>/dev/null

echo "Launching Validation-Only Environment (OOM-Safe)..."

# GENERATION IS DISABLED.

# 3. Start Watchdog
tmux new-session -d -s prod_watchdog "source $CONDA_SH && conda activate SE3nv && cd $PROJECT_DIR && python3 $BIN_DIR/watchdog.py"
echo "[1/2] Zinc-Finger Watchdog ACTIVE."

# 4. Start Folding (Sequential/Memory-Safe)
tmux new-session -d -s prod_folding "source $CONDA_SH && conda activate esm3_pip && cd $PROJECT_DIR && python3 $BIN_DIR/validator.py"
echo "[2/2] Chai-1 Validator (Sequential Path) ACTIVE."

echo "--- Deployment Complete ---"
tmux ls
