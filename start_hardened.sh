#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh

PROJECT_DIR="/home/qntmqrks/rbx1_design/Phase15_MassGeneration"
BIN_DIR="$PROJECT_DIR/HARDENED_v1/bin"
REPORT_FILE="$PROJECT_DIR/leaderboard.csv"

# 1. Deduplicate Leaderboard
echo "Deduplicating leaderboard..."
if [ -f "$REPORT_FILE" ]; then
    python3 -c "import pandas as pd; df=pd.read_csv('$REPORT_FILE'); df.drop_duplicates(subset=['Design'], keep='last').sort_values('pLDDT', ascending=False).to_csv('$REPORT_FILE', index=False)"
fi

# 2. Kill stale sessions
tmux kill-session -t prod_gen 2>/dev/null
tmux kill-session -t prod_watchdog 2>/dev/null
tmux kill-session -t prod_folding 2>/dev/null

echo "Launching Standardized Production Environment (v1.0)..."

# 3. Start Generation
tmux new-session -d -s prod_gen "source /opt/conda/etc/profile.d/conda.sh && conda activate SE3nv && cd $PROJECT_DIR && bash $BIN_DIR/generator.sh"
echo "[1/3] Backbone Generation ACTIVE."

# 4. Start Watchdog
tmux new-session -d -s prod_watchdog "source /opt/conda/etc/profile.d/conda.sh && conda activate SE3nv && cd $PROJECT_DIR && python3 $BIN_DIR/watchdog.py"
echo "[2/3] Zinc-Finger Watchdog ACTIVE."

# 5. Start Folding (Sequential/Memory-Safe)
# Note: Validator.py implements its own internal loop with staggering
tmux new-session -d -s prod_folding "source /opt/conda/etc/profile.d/conda.sh && conda activate esm3_pip && cd $PROJECT_DIR && python3 $BIN_DIR/validator.py"
echo "[3/3] Chai-1 Validator (Sequential Path) ACTIVE."

echo "--- Deployment Complete ---"
tmux ls
