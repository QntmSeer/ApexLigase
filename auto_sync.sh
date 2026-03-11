#!/bin/bash
# =========================================================
# AdK Super-Simulation Auto-Sync Service
# Pulls data from md-sim-god every 30 minutes
# =========================================================

INSTANCE="md-sim-god"
REMOTE_DIR="/home/shadeform/MD/"
LOCAL_DIR="$(pwd)"

echo "--- CORE ADK SYNC ACTIVE ---"
echo "Target Instance: $INSTANCE"
echo "Local Directory: $LOCAL_DIR"
echo "Sync Interval: 30 minutes"
echo "---------------------------------------------------------"

while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$TIMESTAMP] Starting sync..."
    
    # 1. Pull the log file for quick progress checks
    brev copy "$INSTANCE:$REMOTE_DIR/hpc_production.log" "$LOCAL_DIR/" 2>/dev/null
    
    # 2. Pull the trajectories folder (where .dcd data lives)
    # Note: brev copy handles recursive transfer for directories
    brev copy "$INSTANCE:$REMOTE_DIR/trajectories/" "$LOCAL_DIR/trajectories/" 2>/dev/null
    
    echo "[$TIMESTAMP] Sync Complete. Sleeping for 30m..."
    sleep 1800
done
