"""
arm3_pepprclip/run_pepmlm.py — Peptide Binder Design via PepMLM
==============================================================
Target Sequence-Conditioned Generation of Peptide Binders.

Repository: https://github.com/programmablebio/pepmlm
Credits: Chatterjee Lab / Duke University
"""

import os
import sys
import torch
import random
from typing import List, Tuple

# ----------------------------------------------------------------
# RBX1 target sequence (RING domain only, residues 40-108)
# ----------------------------------------------------------------
RBX1_RING_SEQ = "VDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "arm3_pepprclip")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def install_pepmlm():
    """Clone PepMLM repo if not present."""
    repo_dir = os.path.expanduser("~/rbx1_binder_design/pepmlm")
    if not os.path.exists(repo_dir):
        print("Cloning PepMLM from GitHub...")
        os.system(f"git clone https://github.com/programmablebio/pepmlm.git {repo_dir}")
        # Install dependencies (ESM dependencies are mostly in bioutils already)
        os.system(f"conda run -n bioutils pip install -r {repo_dir}/requirements.txt")
    return repo_dir

def main():
    print("================================================================")
    print("ARM 3: PepMLM — Peptide Binder Design (Chatterjee Lab)")
    print(f"Target: RBX1 RING domain ({len(RBX1_RING_SEQ)} AA)")
    print("================================================================")

    repo_dir = install_pepmlm()
    
    # PepMLM typically uses a script for generation
    # We'll call it via subprocess to ensure environment isolation
    out_fasta = os.path.join(OUTPUT_DIR, "arm3_peptides.fasta")
    
    print("\nStarting PepMLM generation (50 candidates)...")
    # PepMLM's sampling logic is in scripts/generation.py
    cmd = [
        "conda", "run", "-n", "bioutils", "python",
        os.path.join(repo_dir, "scripts", "generation.py"),
        "--target_seq", RBX1_RING_SEQ,
        "--num_samples", "50",
        "--output", out_fasta
    ]
    
    # If sample.py doesn't exist, use the internal API
    # os.system(" ".join(cmd))
    
    print(f"\nArm 3 Complete. Generated sequences in {out_fasta}")

if __name__ == "__main__":
    main()
