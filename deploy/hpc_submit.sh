#!/bin/bash
# =========================================================
# HPC Deployment Script for Adenylate Kinase MD 
# (6x 100ns Replicas)
# =========================================================

# 1. Archive check (Disabled to prevent overwriting upgraded scripts)
# if [ -f "hpc_md_run.zip" ]; then
#     echo "Unzipping payload..."
#     unzip -o hpc_md_run.zip
# fi

# 2. Ensure Environment Dependencies
echo "Ensuring OpenMM, MDTraj, scikit-learn, matplotlib, numpy and rmsx are installed..."
python3 -m pip install openmm mdtraj scikit-learn matplotlib numpy seaborn pandas || echo "Warning: Pip install failed. If running in conda, activate your env first."
rm -rf rmsx && git clone https://github.com/AntunesLab/rmsx.git /tmp/rmsx_install && cp -r /tmp/rmsx_install/rmsx . || echo "Warning: RMSX clone failed."

# 3. Create Output Directory
mkdir -p trajectories

# 4. Launch Production Run and Analysis in the Background
# We use nohup so the run continues even if SSH disconnects.
echo "Launching 700ns production pipeline and inline analysis via nohup..."
nohup bash -c "python3 -u run_production.py --workers 3 && python3 -u analyze_trajectory.py && zip -r final_results.zip analysis_results/" > hpc_production.log 2>&1 &

echo "========================================================="
echo "SUCCESS: MD Pipeline launched in background!"
echo "- Tail the log to watch progress:  tail -f hpc_production.log"
echo "- When finished, 'final_results.zip' will be generated in this directory."
echo "- The job will survive terminal disconnection."
echo "========================================================="
