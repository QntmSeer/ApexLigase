"""
Phase 13: Chai-1 Structure Prediction for Top RFdiffusion/ProteinMPNN Binders
Targets: rfd_binder_38 and rfd_binder_61 vs RBX1 RING domain
"""
import os
import shutil
import torch
import numpy as np
from pathlib import Path
from chai_lab.chai1 import run_inference

# ── Sequences from ESM3 leaderboard ──────────────────────────────────────────
# RBX1 RING domain (Chain A target — kept fixed in ProteinMPNN)
RBX1_SEQ = "DFSECVLCDRPGNGLCADCEEAGCEGSPESCGWTTLKNGHNFHSICLSRWLAVNKTCPVCKEPVEIEKSGS"

# Top binders from Phase 12 (Chain B)
BINDERS = {
    "rfd_binder_38": "GPAEAAARAARLRAAADAVRALAAAGDEAAAAAELAVLEALDPEAGRRTRERVAVDLALAAAAAAA",
    "rfd_binder_61": "LSPEEWKKLQEEAGKIKEEAEKEAKKLEAEGKKEEAEKVLKEAGEKIKELLEKA",
}

OUTPUT_BASE = Path("/home/qntmqrks/rbx1_design/Phase13_Chai1")
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Running on: {DEVICE}")


def write_fasta(name: str, rbx1_seq: str, binder_seq: str, out_dir: Path) -> Path:
    """Write a two-chain FASTA file for Chai-1."""
    fasta_path = out_dir / f"{name}.fasta"
    with open(fasta_path, "w") as f:
        f.write(f">protein|name=RBX1\n{rbx1_seq}\n")
        f.write(f">protein|name={name}\n{binder_seq}\n")
    return fasta_path


def run_chai1_prediction(name: str, binder_seq: str):
    out_dir = OUTPUT_BASE / name
    # Remove stale files — Chai-1 requires an empty (or non-existent) output_dir
    if out_dir.exists():
        shutil.rmtree(out_dir)
    # Do NOT mkdir — run_inference creates the directory itself

    # Write FASTA to parent dir so out_dir doesn't exist yet when passed to Chai-1
    fasta_path = write_fasta(name, RBX1_SEQ, binder_seq, OUTPUT_BASE)
    print(f"\n[{name}] Running Chai-1 inference ...")


    candidates = run_inference(
        fasta_file=fasta_path,
        output_dir=out_dir,
        num_trunk_recycles=3,
        num_diffn_timesteps=200,
        seed=42,
        device=DEVICE,
        use_esm_embeddings=True,
    )

    # Extract scores from saved npz files
    best_agg_score = 0.0
    best_iptm = 0.0
    best_ptm = 0.0
    
    for i in range(5):
        score_file = out_dir / f"scores.model_idx_{i}.npz"
        if score_file.exists():
            d = np.load(score_file)
            agg = float(d.get("aggregate_score", [0.0])[0])
            iptm = float(d.get("iptm", [0.0])[0])
            ptm = float(d.get("ptm", [0.0])[0])
            if agg > best_agg_score:
                best_agg_score = agg
                best_iptm = iptm
                best_ptm = ptm

    print(f"[{name}] Best aggregate score: {best_agg_score:.4f}")
    print(f"[{name}] ipTM: {best_iptm:.4f}")
    print(f"[{name}] pTM:  {best_ptm:.4f}")

    results = {
        "name": name,
        "best_agg_score": best_agg_score,
        "iptm": best_iptm,
        "ptm": best_ptm,
        "output_dir": str(out_dir),
    }

    # Save score summary
    score_path = out_dir / "chai1_scores.txt"
    with open(score_path, "w") as f:
        for k, v in results.items():
            f.write(f"{k}: {v}\n")
    print(f"[{name}] Scores saved to {score_path}")

    return results


def main():
    all_results = []
    for name, seq in BINDERS.items():
        try:
            r = run_chai1_prediction(name, seq)
            all_results.append(r)
        except Exception as e:
            print(f"[{name}] ERROR: {e}")

    print("\n\n=== CHAI-1 FINAL LEADERBOARD ===")
    all_results.sort(key=lambda x: x.get("iptm", 0), reverse=True)
    for r in all_results:
        print(f"  {r['name']:<30} ipTM={r.get('iptm',0):.4f}  pTM={r.get('ptm',0):.4f}  agg={r.get('best_agg_score',0):.4f}")

    # Upload results to GCS
    os.system("gsutil -m rsync -r /home/qntmqrks/rbx1_design/Phase13_Chai1/ gs://md_sim/Phase13_Chai1/")
    print("\nResults uploaded to gs://md_sim/Phase13_Chai1/")


if __name__ == "__main__":
    main()
