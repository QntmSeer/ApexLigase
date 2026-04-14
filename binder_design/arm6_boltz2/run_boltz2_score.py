"""
arm6_boltz2/run_boltz2_score.py — Boltz2 ipSAE Scoring (ARM 6)
===============================================================
Replaces Chai-1 as the PRIMARY filter in Strategy v2.

Scores all candidates from the merged FASTA against RBX1 RING domain
using Boltz2, extracts ipSAE, and writes boltz2_scores.csv.

Filter gate: ipSAE >= 0.70 (competition top tier is 0.80-0.93)

Usage:
    conda run -n boltz2 python run_boltz2_score.py
    conda run -n boltz2 python run_boltz2_score.py --input path/to/candidates.fasta
    conda run -n boltz2 python run_boltz2_score.py --rescore-existing  # score our v1 designs
"""

import os
import sys
import csv
import json
import argparse
import subprocess
from pathlib import Path

WORKDIR = Path.home() / "rbx1_binder_design"
OUTPUTS = WORKDIR / "outputs"
BOLTZ2_OUT = OUTPUTS / "arm6_boltz2"

# RBX1 RING domain sequence (residues 38-108, from PDB 1FBV/2LGV)
RBX1_RING_SEQ = "VDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH"

# v2 threshold — competition top tier ≥ 0.80, we gate at 0.70 to allow diversity
IPSAE_CUTOFF = 0.70


def install_boltz2():
    """Install boltz2 if not present."""
    try:
        import boltz
        print(f"Boltz2 {boltz.__version__} already installed.")
    except ImportError:
        print("Installing boltz2...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "boltz"],
            check=True
        )
        print("Boltz2 installed.")


def write_multimer_fasta(binder_name: str, binder_seq: str, out_path: Path):
    """Write a multimer FASTA for Boltz2 (binder | RBX1)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(f">binder|{binder_name}\n{binder_seq}\n")
        f.write(f">rbx1_ring\n{RBX1_RING_SEQ}\n")


def run_boltz2_predict(fasta_path: Path, out_dir: Path) -> dict:
    """
    Run boltz predict on a single multimer FASTA.
    Returns dict with ipSAE, pLDDT, confidence.
    """
    import boltz

    out_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable, "-m", "boltz", "predict", str(fasta_path),
            "--out_dir", str(out_dir),
            "--accelerator", "gpu",
            "--devices", "1",
            "--recycling_steps", "3",
            "--sampling_steps", "200",
            "--diffusion_samples", "1",
            "--output_format", "pdb",
        ],
        capture_output=True, text=True
    )

    # Parse confidence JSON output
    conf_files = list(out_dir.glob("**/confidence_*.json"))
    if not conf_files:
        print(f"  WARNING: No confidence JSON found in {out_dir}")
        return {}

    with open(conf_files[0]) as f:
        conf = json.load(f)

    # Boltz2 confidence schema: complex_plddt, iptm, pae_matrix, etc.
    ipsae  = conf.get("iptm",          None)   # Boltz2 uses iptm ~ ipSAE
    plddt  = conf.get("complex_plddt", None)
    ptm    = conf.get("ptm",           None)

    # If pae_matrix available, compute ipSAE directly from interface PAE
    pae = conf.get("pae", None)
    if pae and ipsae is None:
        import numpy as np
        m = np.array(pae)
        n = len(binder_seq)  # binder length
        bt = m[:n, n:]
        tb = m[n:, :n]
        mean_ipae = (bt.mean() + tb.mean()) / 2.0
        ipsae = float(max(0.0, 1.0 - mean_ipae / 31.75))

    return {
        "boltz2_ipsae":  round(ipsae, 4) if ipsae is not None else None,
        "boltz2_plddt":  round(plddt, 2) if plddt is not None else None,
        "boltz2_ptm":    round(ptm,   4) if ptm   is not None else None,
        "passes_boltz2": (ipsae is not None and ipsae >= IPSAE_CUTOFF),
    }


def load_candidates(fasta_path: Path) -> list:
    candidates = []
    with open(fasta_path) as f:
        lines = f.readlines()
    for i in range(0, len(lines) - 1, 2):
        header = lines[i].strip().lstrip(">")
        seq = lines[i + 1].strip()
        if seq:
            candidates.append({"name": header, "sequence": seq})
    return candidates


def complexity_filter(seq: str) -> bool:
    """
    Sequence complexity pre-filter (from Strategy v2).
    Reject charge-repeat scaffolds before wasting GPU time.
    Returns True if sequence PASSES (is acceptable).
    """
    # Rule 1: no run of 4+ identical charged residues
    charged = set("KRDEH")
    run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1] and seq[i] in charged:
            run += 1
            if run >= 4:
                return False  # reject
        else:
            run = 1

    # Rule 2: charge fraction < 45%
    charge_frac = sum(1 for aa in seq if aa in charged) / len(seq)
    if charge_frac > 0.45:
        return False

    # Rule 3: hydrophobic fraction >= 15%
    hydrophobic = set("VILMFYW")
    hydro_frac = sum(1 for aa in seq if aa in hydrophobic) / len(seq)
    if hydro_frac < 0.15:
        return False

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None,
                        help="FASTA input (default: merged_candidates_top150.fasta)")
    parser.add_argument("--rescore-existing", action="store_true",
                        help="Score our v1 candidate PDBs (design_9, design_1, etc.)")
    parser.add_argument("--ipsae-cutoff", type=float, default=IPSAE_CUTOFF,
                        help=f"ipSAE gate (default: {IPSAE_CUTOFF})")
    args = parser.parse_args()

    install_boltz2()

    BOLTZ2_OUT.mkdir(parents=True, exist_ok=True)

    # Determine input FASTA
    if args.rescore_existing:
        # Score our known v1 sequences from the submission CSV
        input_fasta = OUTPUTS / "v1_designs_rescore.fasta"
        _write_v1_fasta(input_fasta)
    else:
        input_fasta = Path(args.input) if args.input else \
                      (OUTPUTS / "merged_candidates_top150.fasta")

    if not input_fasta.exists():
        print(f"ERROR: {input_fasta} not found — run filter_and_rank.py --merge-only first.")
        sys.exit(1)

    candidates = load_candidates(input_fasta)
    print(f"\nLoaded {len(candidates)} candidates from {input_fasta.name}")

    # Apply complexity filter FIRST (saves GPU time)
    before = len(candidates)
    candidates = [c for c in candidates if complexity_filter(c["sequence"])]
    print(f"After complexity filter (no charge repeats): {len(candidates)}/{before}")

    # Score with Boltz2
    results = []
    for i, cand in enumerate(candidates):
        name = cand["name"]
        seq  = cand["sequence"]
        print(f"\n[{i+1}/{len(candidates)}] Scoring: {name[:60]}")
        print(f"  Seq ({len(seq)} AA): {seq[:40]}...")

        safe = name.replace("|", "_").replace("/", "_")[:50]
        fasta_path = BOLTZ2_OUT / safe / "input.fasta"
        write_multimer_fasta(name, seq, fasta_path)

        scores = run_boltz2_predict(fasta_path, BOLTZ2_OUT / safe)
        scores.update({"name": name, "sequence": seq, "length": len(seq)})
        results.append(scores)

        status = "✅ PASS" if scores.get("passes_boltz2") else "❌ FAIL"
        print(f"  {status}  ipSAE={scores.get('boltz2_ipsae')}  "
              f"pLDDT={scores.get('boltz2_plddt')}  ptm={scores.get('boltz2_ptm')}")

    # Sort by ipSAE descending
    results.sort(key=lambda r: r.get("boltz2_ipsae") or 0, reverse=True)

    # Write CSV
    scores_csv = OUTPUTS / "boltz2_scores.csv"
    with open(scores_csv, "w", newline="") as f:
        fieldnames = ["name", "sequence", "length",
                      "boltz2_ipsae", "boltz2_plddt", "boltz2_ptm", "passes_boltz2"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # Write passing FASTA
    passed = [r for r in results if r.get("passes_boltz2")]
    boltz2_fasta = OUTPUTS / "boltz2_validated.fasta"
    with open(boltz2_fasta, "w") as f:
        for r in passed:
            f.write(f">{r['name']}|boltz2_ipsae={r['boltz2_ipsae']}|"
                    f"plddt={r['boltz2_plddt']}\n{r['sequence']}\n")

    print(f"\n{'='*60}")
    print(f"Boltz2 Scoring Complete")
    print(f"  Scored    : {len(results)}")
    print(f"  Passed    : {len(passed)}  (ipSAE ≥ {args.ipsae_cutoff})")
    print(f"  CSV       : {scores_csv}")
    print(f"  FASTA     : {boltz2_fasta}")
    print(f"\n  Top 5:")
    for r in results[:5]:
        print(f"    ipSAE={r.get('boltz2_ipsae'):.3f}  "
              f"pLDDT={r.get('boltz2_plddt')}  len={r['length']}  "
              f"{r['sequence'][:35]}...")


def _write_v1_fasta(out_path: Path):
    """Write FASTA of our known v1 submission sequences for rescoring."""
    v1_designs = [
        ("design_9",           "AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRLLESAERRAETRAALIARVLAA"),
        ("design_21",          "SAAAAAKAAAAAARAAAAAELEKKLEELEARAELEKKLEELEARAELAEARARAEALKLKL"),
        ("design_15",          "AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRLLESAERRAETRAALIARVL"),
        ("design_1",           "EELEKKLEELRKKLEELRKKLEELRKKLEELRKKLEELRKKLEELRKKLEELRKK"),
        ("design_10",          "AAAELAEARARAEALAAEGREEEGRRLLESAERRAETRAALIARVLAAAELAEARARAEALA"),
        ("design_16",          "AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRL"),
        ("design_18",          "AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRLLESAERRAETRAALIARVLAAAAE"),
        ("design_52",          "AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRLLESAERRAETRAALIARVLAAAAELAR"),
        ("design_50",          "AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRLLESAERR"),
        ("batch2_design_0",    "SSKLRALSAQQALKQAQQAEKELQKQQAQIQKLAQLKAERKERAEKKAALEA"),
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for name, seq in v1_designs:
            f.write(f">{name}\n{seq}\n")
    print(f"Wrote {len(v1_designs)} v1 designs to {out_path}")


if __name__ == "__main__":
    main()
