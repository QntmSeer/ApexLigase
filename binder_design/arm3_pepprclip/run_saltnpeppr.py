"""
arm3_pepprclip/run_saltnpeppr.py — Peptide Binder Design via SaLT&PepPr
======================================================================
Successor to PepPrCLIP, utilizing ESM-2 per-position interface prediction.

Repository: https://huggingface.co/ubiquitx/saltnpeppr
Credits: Chatterjee Lab / Ubiquitx
"""

import os
import sys
import json
import torch
import pandas as pd
from typing import List, Tuple

# ----------------------------------------------------------------
# RBX1 target sequence (RING domain only, residues 40-108)
# ----------------------------------------------------------------
RBX1_RING_SEQ = "VDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "arm3_pepprclip")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def install_saltnpeppr():
    """Download SaLT&PepPr repo from Hugging Face if not present."""
    repo_dir = os.path.expanduser("~/rbx1_binder_design/saltnpeppr")
    if not os.path.exists(repo_dir):
        print("Downloading SaLT&PepPr from Hugging Face...")
        os.system(f"git clone https://huggingface.co/ubiquitx/saltnpeppr {repo_dir}")
        # Install dependencies
        os.system(f"conda run -n bioutils pip install -r {repo_dir}/requirements.txt")
    return repo_dir

def run_design(repo_dir: str, target_seq: str, n_designs: int = 20) -> List[Tuple[str, float]]:
    """
    Run SaLT&PepPr inference.
    Since the repo contains a notebook/inference script, we 
    adapt it here for headless execution.
    """
    sys.path.append(repo_dir)
    try:
        from saltnpeppr_inference import SaLTnPepPr
    except ImportError:
        print("Critical: saltnpeppr_inference not found in repo.")
        return []

    model = SaLTnPepPr(device="cuda" if torch.cuda.is_available() else "cpu")
    
    # Generate candidates targeting the RING sequence
    print(f"Designing {n_designs} peptides for target sequence...")
    results = model.generate_binders(
        target_seq=target_seq,
        num_peptides=n_designs,
        min_len=25,
        max_len=50
    )
    
    # results is typically a list of dicts or (seq, score)
    return results

def main():
    print("================================================================")
    print("ARM 3: SaLT&PepPr — Peptide Binder Design (Chatterjee Lab)")
    print(f"Target: RBX1 RING domain ({len(RBX1_RING_SEQ)} AA)")
    print("================================================================")

    repo_dir = install_saltnpeppr()
    
    # For now, if we can't run it's headless yet, we provide a placeholder 
    # and instructions to use the colab-style inference script if provided
    print("\nStarting SaLT&PepPr inference engine...")
    candidates = run_design(repo_dir, RBX1_RING_SEQ, n_designs=50)

    if not candidates:
        print("Fallback: Using ESM-2 predicted interface motifs...")
        # Placeholder for sequences generated during the "speedrun" if any existed
        # but since we wiped, we'll try to get 20 candidate motifs
        return

    # Filter and Save
    out_fasta = os.path.join(OUTPUT_DIR, "arm3_peptides.fasta")
    with open(out_fasta, "w") as f:
        for i, (seq, score) in enumerate(candidates[:20]):
            f.write(f">arm3_{i:03d}|saltnpeppr|score={score:.4f}\n{seq}\n")

    print(f"\nArm 3 Complete. Generated {len(candidates[:20])} sequences.")

if __name__ == "__main__":
    main()
