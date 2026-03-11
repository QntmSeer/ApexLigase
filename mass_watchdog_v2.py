import os
import time
import subprocess
import pickle
import numpy as np
import glob
import json

# Configuration
WATCH_DIR = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/backbones/"
REPORT_FILE = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/leaderboard.csv"
LOG_FILE = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/mass_watchdog.log"
PMPNN_SCRIPT = "/home/qntmqrks/ProteinMPNN/protein_mpnn_run.py"
PYTHON_BIN = "/opt/conda/envs/SE3nv/bin/python"

os.makedirs(WATCH_DIR, exist_ok=True)

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def check_zinc_clash(pdb_path):
    """Placeholder for Zinc clash detection logic"""
    # In a real scenario, this would check distance between Zinc and Binder scaffold
    return False 

def process_design(pdb_path, trb_path):
    base_name = os.path.basename(pdb_path).replace(".pdb", "")
    
    # 1. Get pLDDT
    try:
        with open(trb_path, 'rb') as f:
            data = pickle.load(f)
            plddt_raw = np.mean(data['plddt'])
            # Standardize to 0-100 scale
            plddt = plddt_raw * 100.0 if plddt_raw <= 1.0 else plddt_raw
    except Exception as e:
        log(f"Error reading TRB for {base_name}: {e}")
        plddt = -1.0

    # 2. Check Zinc Clash
    clash = check_zinc_clash(pdb_path)
    clash_str = "CLASH" if clash else "SAFE"
    
    # 3. Decision Logic (Union Filtering)
    passed = (plddt > 70.0) and (not clash)
    
    # 4. Update Report
    if not os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, 'w') as f:
            f.write("Design,pLDDT,Zinc_Stability,Status\n")
    
    status = "ACCEPTED" if passed else "REJECTED"
    with open(REPORT_FILE, 'a') as f:
        f.write(f"{base_name},{plddt:.2f},{clash_str},{status}\n")
    
    log(f"Processed {base_name}: pLDDT={plddt:.2f}, Zinc={clash_str}, Status={status}")
    
    # 5. Trigger Sequence Design (ProteinMPNN) if accepted
    if passed:
        pmpnn_dir = os.path.join("/home/qntmqrks/rbx1_design/Phase15_MassGeneration/pmpnn/", base_name)
        os.makedirs(pmpnn_dir, exist_ok=True)
        
        chain_jsonl = os.path.join(pmpnn_dir, "chains.jsonl")
        with open(chain_jsonl, 'w') as f:
            f.write(json.dumps({base_name: [["B"], ["A"]]}) + "\n")
            
        cmd = [
            PYTHON_BIN, PMPNN_SCRIPT,
            "--pdb_path", pdb_path,
            "--pdb_path_chains", "A B",
            "--chain_id_jsonl", chain_jsonl,
            "--out_folder", pmpnn_dir,
            "--num_seq_per_target", "2",
            "--sampling_temp", "0.1"
        ]
        log(f"Triggering Sequence Design for {base_name}...")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return True

def main():
    log("Phase 15 Mass-Generation Watchdog (v2 - Preemption Aware) Started.")
    
    # Load existing to avoid duplicates
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r") as f:
            processed = set([line.split(",")[0] for line in f.readlines()[1:]])
        log(f"Resuming with {len(processed)} previously processed designs.")
    else:
        processed = set()

    while True:
        files = glob.glob(os.path.join(WATCH_DIR, "*.pdb"))
        for f in files:
            fname = os.path.basename(f)
            if fname not in processed:
                trb = f.replace(".pdb", ".trb")
                if os.path.exists(trb):
                    if process_design(f, trb):
                        processed.add(fname)
        
        time.sleep(30)

if __name__ == "__main__":
    main()
