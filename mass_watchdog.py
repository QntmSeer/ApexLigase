import os
import time
import glob
import json
import pickle
import subprocess
import numpy as np

# CONFIGURATION
WATCH_DIR = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/backbones/"
REPORT_FILE = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/leaderboard.csv"
PMPNN_SCRIPT = "/home/qntmqrks/ProteinMPNN/protein_mpnn_run.py"
PYTHON_BIN = "/opt/conda/envs/SE3nv/bin/python"

# Zinc Coordinating Residues in RBX1 (Chain A)
ZN_LIGANDS = [42, 45, 53, 56, 68, 75, 77, 80, 82, 83, 94, 97]

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def check_zinc_clash(pdb_path):
    """Returns True if any binder atom (Chain B) is too close to Zinc Ligands (Chain A)."""
    ligand_coords = []
    binder_coords = []
    
    try:
        with open(pdb_path, 'r') as f:
            for line in f:
                if line.startswith('ATOM'):
                    chain = line[21]
                    res_num = int(line[22:26])
                    coords = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
                    
                    if chain == 'A' and res_num in ZN_LIGANDS:
                        ligand_coords.append(coords)
                    elif chain == 'B':
                        binder_coords.append(coords)
        
        if not ligand_coords or not binder_coords:
            return False
            
        lc = np.array(ligand_coords)
        bc = np.array(binder_coords)
        
        for z_coord in lc:
            dists = np.linalg.norm(bc - z_coord, axis=1)
            if np.any(dists < 2.8):
                return True
        return False
    except Exception as e:
        log(f"Error checking zinc clash: {e}")
        return False

def process_design(pdb_path, trb_path):
    base_name = os.path.basename(pdb_path).replace(".pdb", "")
    
    # 1. Get pLDDT
    try:
        with open(trb_path, 'rb') as f:
            data = pickle.load(f)
            plddt_raw = np.mean(data['plddt'])
            # Standardize to 0-100 scale if fractional
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
    log("Phase 15 Mass-Generation Watchdog (Zinc Protection) Started.")
    processed = set()
    
    # Process existing designs that haven't been reported yet
    existing = glob.glob(os.path.join(WATCH_DIR, "*.pdb"))
    log(f"Found {len(existing)} existing backbones. Processing...")
    for f in existing:
        fname = os.path.basename(f)
        trb = f.replace(".pdb", ".trb")
        if os.path.exists(trb):
            if process_design(f, trb):
                processed.add(fname)

    while True:
        files = glob.glob(os.path.join(WATCH_DIR, "*.pdb"))
        for f in files:
            fname = os.path.basename(f)
            if fname not in processed:
                trb = f.replace(".pdb", ".trb")
                # Wait for trb (sometimes they arrive slightly later)
                if os.path.exists(trb):
                    if process_design(f, trb):
                        processed.add(fname)
        
        time.sleep(30)

if __name__ == "__main__":
    main()
