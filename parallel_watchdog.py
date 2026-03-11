import os
import time
import subprocess
import torch
import numpy as np
import pickle
import glob
import json

# Paths
WATCH_DIR = "/home/qntmqrks/rbx1_design/Phase10_RFdiffusion/outputs"
PMPNN_DIR = "/home/qntmqrks/ProteinMPNN"
PMPNN_SCRIPT = os.path.join(PMPNN_DIR, "protein_mpnn_run.py")
OUTPUT_ROOT = "/home/qntmqrks/rbx1_design/Phase11_Optimization/processed"
LOG_FILE = "/home/qntmqrks/rbx1_design/Phase11_Optimization/watchdog.log"
PYTHON_BIN = "/opt/conda/envs/SE3nv/bin/python"

os.makedirs(OUTPUT_ROOT, exist_ok=True)

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def process_design(pdb_path, trb_path):
    base_name = os.path.basename(pdb_path).replace(".pdb", "")
    pmpnn_out_dir = os.path.join(OUTPUT_ROOT, base_name)
    
    if os.path.exists(pmpnn_out_dir):
        if glob.glob(os.path.join(pmpnn_out_dir, "seqs", "*.fa")):
            return True

    log(f"--- Processing {base_name} ---")
    
    # 1. Check pLDDT
    try:
        with open(trb_path, 'rb') as f:
            data = pickle.load(f)
        plddt_raw = np.mean(data['plddt'])
        plddt = plddt_raw * 100 if plddt_raw <= 1.0 else plddt_raw
        log(f"{base_name} pLDDT: {plddt:.2f}")
        
        if plddt < 50.0:
            log(f"Skipping {base_name} - Low confidence ({plddt:.1f})")
            os.makedirs(pmpnn_out_dir, exist_ok=True)
            with open(os.path.join(pmpnn_out_dir, "skipped_low_plddt.txt"), "w") as f:
                f.write(str(plddt))
            return True
    except Exception as e:
        log(f"Error reading .trb: {e}")
        return False

    # 2. Setup JSONL for Chain Fixing
    os.makedirs(pmpnn_out_dir, exist_ok=True)
    chain_jsonl_path = os.path.join(pmpnn_out_dir, "chains.jsonl")
    
    # We want to design Chain B (Binder) and hold Chain A (RBX1) fixed.
    chain_dict = {
        base_name: [["B"], ["A"]]
    }
    with open(chain_jsonl_path, "w") as f:
        f.write(json.dumps(chain_dict) + "\n")

    # 3. Launch ProteinMPNN
    cmd = [
        PYTHON_BIN, PMPNN_SCRIPT,
        "--pdb_path", pdb_path,
        "--pdb_path_chains", "A B", 
        "--chain_id_jsonl", chain_jsonl_path, 
        "--out_folder", pmpnn_out_dir,
        "--num_seq_per_target", "8",
        "--sampling_temp", "0.1",
        "--batch_size", "8"
    ]
    
    try:
        log(f"Launching ProteinMPNN for {base_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log(f"Success: {base_name} ProteinMPNN complete.")
            return True
        else:
            log(f"ProteinMPNN failed for {base_name}: {result.stderr}")
            with open(os.path.join(pmpnn_out_dir, "failed.txt"), "w") as f:
                f.write(result.stderr)
            return True # Mark as "processed" so we don't retry forever
    except Exception as e:
        log(f"Error for {base_name}: {e}")
        return False

def main():
    log("L4 Watchdog v6 started (JSONL Chain Fixing).")
    processed = set()
    
    while True:
        pdbs = sorted(glob.glob(os.path.join(WATCH_DIR, "*.pdb")), key=os.path.getmtime)
        for pdb in pdbs:
            fname = os.path.basename(pdb)
            if fname not in processed:
                trb = pdb.replace(".pdb", ".trb")
                if os.path.exists(trb):
                    success = process_design(pdb, trb)
                    if success:
                        processed.add(fname)
        
        time.sleep(15)

if __name__ == "__main__":
    main()
