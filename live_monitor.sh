#!/bin/bash
# Live Telemetry Monitor for GCP Pipeline
# Run this from your local WSL terminal to watch the servers progress in real-time.

echo "============================================="
echo "   🚀 CHAI-1 LIVE FOLDING TELEMETRY 🚀   "
echo "============================================="
echo "Establishing secure connection to crunchy-peptides..."
echo "(Press Ctrl+C to stop watching at any time)"
echo ""

gcloud compute ssh qntmqrks@crunchy-peptides --zone=us-central1-a --command="tail -f /home/qntmqrks/rbx1_design/Phase15_MassGeneration/mass_folding.log"
