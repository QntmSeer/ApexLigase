"""
arm3_pepprclip/run_pepprclip.py — Peptide Binder Design via PepPrCLIP
======================================================================
PepPrCLIP uses contrastive language modelling to generate short peptides
that bind E3 ubiquitin ligase components — directly relevant to RBX1.

Paper: "De novo design of peptide binders to conformationally diverse
        targets with contrastive language modeling" (2024, NIH/Duke)

Output: 20 short peptide sequences (25-50 AA) targeting RBX1 RING domain.
These are highly novel by construction -> pass UniRef50 edit-distance filter easily.
"""

import os
import sys
import json
import random
import subprocess
import hashlib

# ----------------------------------------------------------------
# RBX1 target sequence (RING domain only, residues 40-108)
# ----------------------------------------------------------------
RBX1_RING_SEQ = "VDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH"

# Hotspot residues (positions within RING domain, 1-indexed)
# W87→W48 in ring, R91→R52, E55→E16, Q57→Q18 (adjusted for domain start at 40)
HOTSPOT_AAS = "WRECQILA"  # Key amino acids of the binding surface

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "arm3_pepprclip")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def install_pepprclip():
    """Clone and install PepPrCLIP if not present."""
    pepprclip_dir = os.path.expanduser("~/rbx1_binder_design/PepPrCLIP")
    if not os.path.exists(pepprclip_dir):
        print("Cloning PepPrCLIP...")
        subprocess.run([
            "git", "clone",
            "https://github.com/programmablebio/pepprclip.git",
            pepprclip_dir
        ], check=True)
        subprocess.run(
            ["pip", "install", "-q", "-r", "requirements.txt"],
            cwd=pepprclip_dir, check=True
        )
    return pepprclip_dir

def run_pepprclip_design(pepprclip_dir, target_seq, n_peptides=100, lengths=(25, 50)):
    """
    Run PepPrCLIP to generate peptide candidates.
    Returns list of (sequence, score) tuples.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pepprclip",
        os.path.join(pepprclip_dir, "pepprclip", "__init__.py")
    )
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        PepPrCLIP = getattr(mod, "PepPrCLIP", None)
    except Exception as e:
        print(f"Could not import PepPrCLIP module directly: {e}")
        print("Falling back to subprocess call...")
        return run_pepprclip_subprocess(pepprclip_dir, target_seq, n_peptides, lengths)

    model = PepPrCLIP()
    results = model.design(
        target_sequence=target_seq,
        n_designs=n_peptides,
        min_length=lengths[0],
        max_length=lengths[1],
        device="cuda"
    )
    return results

def run_pepprclip_subprocess(pepprclip_dir, target_seq, n_peptides, lengths):
    """Fallback: call PepPrCLIP via subprocess with a temp config."""
    config = {
        "target_sequence": target_seq,
        "n_designs": n_peptides,
        "min_length": lengths[0],
        "max_length": lengths[1],
        "output_fasta": os.path.join(OUTPUT_DIR, "pepprclip_raw.fasta")
    }
    cfg_file = os.path.join(OUTPUT_DIR, "pepprclip_config.json")
    with open(cfg_file, "w") as f:
        json.dump(config, f)

    result = subprocess.run(
        [sys.executable, os.path.join(pepprclip_dir, "design.py"), "--config", cfg_file],
        capture_output=True, text=True, cwd=pepprclip_dir
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"PepPrCLIP error:\n{result.stderr}")
        return []

    # Parse output fasta
    candidates = []
    raw_fasta = config["output_fasta"]
    if os.path.exists(raw_fasta):
        with open(raw_fasta) as f:
            lines = f.readlines()
        for i in range(0, len(lines) - 1, 2):
            header = lines[i].strip().lstrip('>')
            seq = lines[i+1].strip()
            score = float(header.split("score=")[-1]) if "score=" in header else 0.0
            candidates.append((seq, score))
    return candidates

def filter_candidates(candidates, min_len=25, max_len=50, top_n=20):
    """Filter by length and return top N by score."""
    filtered = [(seq, sc) for seq, sc in candidates
                if min_len <= len(seq) <= max_len]
    filtered.sort(key=lambda x: x[1], reverse=True)
    return filtered[:top_n]

def write_fasta(candidates, out_path, arm="arm3"):
    with open(out_path, "w") as f:
        for i, (seq, score) in enumerate(candidates):
            f.write(f">{arm}_{i:03d}|pepprclip|score={score:.4f}|len={len(seq)}\n{seq}\n")
    print(f"Wrote {len(candidates)} peptide sequences to {out_path}")

def main():
    print("================================================================")
    print("ARM 3: PepPrCLIP — Peptide Binder Design")
    print(f"Target: RBX1 RING domain ({len(RBX1_RING_SEQ)} AA)")
    print("================================================================")

    pepprclip_dir = install_pepprclip()

    print(f"\nGenerating 100 peptide candidates (length 25-50 AA)...")
    candidates = run_pepprclip_design(
        pepprclip_dir=pepprclip_dir,
        target_seq=RBX1_RING_SEQ,
        n_peptides=100,
        lengths=(25, 50)
    )

    if not candidates:
        print("WARNING: No candidates returned. Check PepPrCLIP installation.")
        return

    top = filter_candidates(candidates, top_n=20)
    out_fasta = os.path.join(OUTPUT_DIR, "arm3_peptides.fasta")
    write_fasta(top, out_fasta)

    print(f"\nTop 5 peptide candidates:")
    for i, (seq, score) in enumerate(top[:5]):
        print(f"  {i+1}. len={len(seq):3d}  score={score:.4f}  {seq[:30]}...")

    print("\nArm 3 complete.")

if __name__ == "__main__":
    main()
