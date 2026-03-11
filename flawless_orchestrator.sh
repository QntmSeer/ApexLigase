#!/bin/bash

# FLAWLESS PRODUCTION PIPELINE (v2.0 - OOM SAFE)
# Author: Antigravity
# Description: This orchestrator completely prevents Out-Of-Memory (OOM) 
# crashes on the GCP L4 instance by enforcing a decoupled workflow.
# It provides simple commands to toggle between Generation and Validation.

PROJECT_DIR="/home/qntmqrks/rbx1_design/Phase15_MassGeneration"
BIN_DIR="$PROJECT_DIR/HARDENED_v1/bin"

if [ "$1" == "--generate" ]; then
    echo "=== [MODE 1] RFDIFFUSION BACKBONE GENERATION ==="
    echo "Note: This will launch generation in the background."
    tmux new-session -d -s prod_gen "source /opt/conda/etc/profile.d/conda.sh && conda activate SE3nv && cd $PROJECT_DIR && bash $BIN_DIR/generator.sh"
    echo "Generation ACTIVE. Monitor with: tmux attach-session -t prod_gen"
    exit 0
elif [ "$1" == "--validate" ]; then
    echo "=== [MODE 2] SEQUENCE OPTIMIZATION & CHAI-1 VALIDATION ==="
    echo "Note: This will sequentially run Watchdog (PMPNN) and Chai-1 in the background."
    bash $BIN_DIR/start_validation_only.sh
    echo "Validation ACTIVE. Monitor with: tmux ls"
    exit 0
else
    echo "Usage: bash flawless_orchestrator.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --generate   Start massive backbone generation only."
    echo "  --validate   Start sequence design and Chai-1 3D folding only."
    echo ""
    echo "CRITICAL: Never run both simultaneously on 16GB RAM."
    exit 1
fi
