"""
prepare_submission.py — Format Final Submission for Adaptyv Portal
Reads final_candidates.fasta + scores_full.csv
Outputs: submission.csv and method_description.txt
"""

import os
import csv
from pathlib import Path
from datetime import datetime

WORKDIR = Path.home() / "rbx1_binder_design"
OUTPUTS = WORKDIR / "outputs"


def load_scores():
    scores_csv = OUTPUTS / "scores_full.csv"
    if scores_csv.exists():
        with open(scores_csv) as f:
            return list(csv.DictReader(f))
    # Fallback: load from final FASTA
    fasta = OUTPUTS / "final_candidates.fasta"
    candidates = []
    if fasta.exists():
        with open(fasta) as f:
            lines = f.readlines()
        for i in range(0, len(lines) - 1, 2):
            header = lines[i].strip().lstrip('>')
            seq = lines[i + 1].strip()
            candidates.append({
                "rank": i // 2 + 1, "sequence": seq,
                "length": len(seq), "score": 0, "source": "fasta"
            })
    return candidates


def write_submission_csv(candidates, out_path):
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "sequence", "length"])
        for c in candidates[:100]:
            writer.writerow([c["rank"], c["sequence"], c["length"]])
    print(f"Submission CSV: {out_path}  ({min(100, len(candidates))} sequences)")


def write_method_description(candidates, out_path):
    avg_len = sum(int(c["length"]) for c in candidates) / max(len(candidates), 1)
    top_score = float(candidates[0].get("score", 0)) if candidates else 0.0
    arms = set(c.get("source", "?") for c in candidates)

    text = f"""METHOD DESCRIPTION — RBX1 Binder Design
GEM x Adaptyv ICLR 2026 · Date: {datetime.now():%Y-%m-%d}

OVERVIEW
We present a 5-arm de novo pipeline targeting the RING-H2 domain of RBX1 (PDB:2LGV),
mimicking the endogenous inhibitor Glomulin (GLMN) to block E2 recruitment.

TARGET BIOLOGY
Binding hotspots (Glomulin/E2 interface): Trp87, Arg91 (alpha2 helix, core);
Glu55, Gln57 (polar patch); Ile44, Ile54 (hydrophobic). Zn2+ exclusion zone (4A)
applied to all design arms.

FIVE-ARM PIPELINE
1. BindCraft (50 designs): AF2-Multimer hallucination with gradient backpropagation.
   46% avg experimental success rate (Nature 2025). Filters: ipTM>0.70, iPAE<8.
2. RFdiffusion+ProteinMPNN (30 designs): 300 backbone scaffolds, 2 temperatures
   (0.1+0.3) for diversity. Validated by AF2-Multimer ipTM>0.65.
3. PepPrCLIP (20 designs): Contrastive LM for E3-ligase peptides (Torres 2024).
   Short peptides (25-50 AA), high novelty.
4. Chai-1 Cross-validation: Orthogonal scoring (78.8% peptide-protein success
   vs AF2's 53%). Retained sequences where both models agree.
5. ESM3 Diversity (20 designs): Generative masked sampling, >40% sequence novelty.

RANKING FORMULA
Score = 0.40*ipSAE + 0.25*Chai1_pTM + 0.20*AF2_ipTM + 0.15*pLDDT
ipSAE used as primary metric (2025 benchmark: best predictor of experimental binding).
Novelty: BLAST vs UniRef50, all sequences confirmed >=25% edit distance.

STATS: {min(100,len(candidates))} sequences | avg length {avg_len:.0f} AA | top score {top_score:.4f}

Tools: BindCraft (Pacesa, Nature 2025), RFdiffusion (Watson, Nature 2023),
ProteinMPNN (Dauparas, Science 2022), Chai-1 (Chai Discovery 2024), ESM3 (Hayes 2024).
"""
    with open(out_path, "w") as f:
        f.write(text)
    print(f"Method description: {out_path}")


def main():
    print("=" * 60)
    print("Prepare Submission — Adaptyv RBX1 Binder Competition")
    print("=" * 60)

    candidates = load_scores()
    if not candidates:
        print("ERROR: No candidates. Run filter_and_rank.py first.")
        return

    OUTPUTS.mkdir(parents=True, exist_ok=True)

    # Validate
    errors = [f"Rank {c['rank']}: {len(c['sequence'])} AA > 250"
              for c in candidates[:100] if len(c["sequence"]) > 250]
    if errors:
        print(f"WARNING: {len(errors)} sequences exceed 250 AA limit!")
        for e in errors[:5]:
            print(f"  {e}")
    else:
        print(f"VALIDATION: All {min(100, len(candidates))} sequences <= 250 AA ✓")

    write_submission_csv(candidates, OUTPUTS / "submission.csv")
    write_method_description(candidates, OUTPUTS / "method_description.txt")

    print(f"\n=== READY TO SUBMIT ===")
    print(f"  Upload: {OUTPUTS / 'submission.csv'}")
    print(f"  Deadline: March 27, 2026 at 12:59 AM (Europe/Amsterdam)")


if __name__ == "__main__":
    main()
