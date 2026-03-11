#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh

# Kill any stale sessions
tmux kill-session -t mass_gen 2>/dev/null
tmux kill-session -t mass_watchdog 2>/dev/null
tmux kill-session -t mass_folding 2>/dev/null

echo "Starting sessions..."

# 1. Start Gen
tmux new-session -d -s mass_gen 'source /opt/conda/etc/profile.d/conda.sh && conda activate SE3nv && cd /home/qntmqrks/rbx1_design/Phase15_MassGeneration/ && bash launch_mass_gen.sh'
echo "mass_gen launched."

# 2. Start Watchdog
tmux new-session -d -s mass_watchdog 'source /opt/conda/etc/profile.d/conda.sh && conda activate SE3nv && cd /home/qntmqrks/rbx1_design/Phase15_MassGeneration/ && python3 mass_watchdog_v2.py'
echo "mass_watchdog launched."

# 3. Start Folding
tmux new-session -d -s mass_folding 'source /opt/conda/etc/profile.d/conda.sh && conda activate esm3_pip && cd /home/qntmqrks/rbx1_design/Phase15_MassGeneration/ && python3 mass_folding.py'
echo "mass_folding launched."

echo "All systems operational."
tmux ls
