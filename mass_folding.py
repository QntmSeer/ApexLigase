import os
import time
import subprocess
import glob
import numpy as np
import torch
from pathlib import Path
from chai_lab.chai1 import run_inference

# Paths
PROCESS_DIR = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration"
LEADERBOARD = os.path.join(PROCESS_DIR, "leaderboard.csv")
FOLDING_DIR = os.path.join(PROCESS_DIR, "folding")
PMPNN_DIR = os.path.join(PROCESS_DIR, "pmpnn")
LOG_FILE = os.path.join(PROCESS_DIR, "mass_folding.log")

# RBX1 Target Sequence
RBX1_SEQ = "DFSECVLCDRPGNGLCADCEEAGCEGSPESCGWTTLKNGHNFHSICLSRWLAVNKTCPVCKEPVEIEKSGS"

os.makedirs(FOLDING_DIR, exist_ok=True)

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def get_pmpnn_seq(design_name):
    """Retrieve the top sequence from ProteinMPNN output."""
    seq_dir = os.path.join(PMPNN_DIR, design_name, "seqs")
    fa_files = glob.glob(os.path.join(seq_dir, "*.fa"))
    if not fa_files:
        return None
    
    # Read the first sequence (usually the top one)
    with open(fa_files[0], "r") as f:
        lines = f.readlines()
        # FASTA: >name, score=X ... \n SEQUENCE
        if len(lines) >= 4: # First sequence is lines 2-3 (index 2-3)
            return lines[3].strip()
    return None

def run_chai_folding(design_name, binder_seq):
    out_dir = Path(FOLDING_DIR) / design_name
    if out_dir.exists():
        return True
    
    # Setup FASTA
    fasta_path = Path(FOLDING_DIR) / f"{design_name}.fasta"
    with open(fasta_path, "w") as f:
        f.write(f">protein|name=RBX1\n{RBX1_SEQ}\n")
        f.write(f">protein|name={design_name}\n{binder_seq}\n")
    
    log(f"Launching Chai-1 folding for {design_name}...")
    try:
        run_inference(
            fasta_file=fasta_path,
            output_dir=out_dir,
            num_trunk_recycles=3,
            num_diffn_timesteps=200,
            seed=42,
            device="cuda:0",
            use_esm_embeddings=True,
        )
        log(f"Success: {design_name} folded.")
        return True
    except Exception as e:
        log(f"Error folding {design_name}: {e}")
        return False

def main():
    log("Phase 15 High-Fidelity Validation Watchdog (Chai-1) Started.")
    processed = set()
    
    while True:
        if not os.path.exists(LEADERBOARD):
            time.sleep(30)
            continue
            
        with open(LEADERBOARD, "r") as f:
            lines = f.readlines()[1:] # skip header
            
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) < 4: continue
            
            design_name = parts[0]
            status = parts[3]
            
            if status == "ACCEPTED" and design_name not in processed:
                # Check if already folded on disk
                if os.path.exists(os.path.join(FOLDING_DIR, design_name)):
                    processed.add(design_name)
                    continue
                
                binder_seq = get_pmpnn_seq(design_name)
                if binder_seq:
                    if run_chai_folding(design_name, binder_seq):
                        processed.add(design_name)
                else:
                    log(f"Waiting for ProteinMPNN sequence for {design_name}...")
        
        time.sleep(60)

if __name__ == "__main__":
    main()
