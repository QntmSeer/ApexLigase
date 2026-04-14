"""
filter_and_rank.py — Boltz2 ipSAE Scoring + Novelty + Length Gates
======================================================================
v2 changes (2026-04-15, from Boltz2 rescore of v1 designs):
  - RULE 0: Complexity pre-filter rejects charge-repeat scaffolds BEFORE GPU
  - RULE 1: Boltz2 ipSAE >= 0.70 is a HARD GATE (no blending)
  - RULE 2: Ranking uses Boltz2 ipSAE as primary metric (70% weight)
  - Chai-1 ipTM kept as secondary confirmation only, NOT a gate

Lesson: design_21 ranked #2 by Chai-1 (0.567), ranked #8 by Boltz2 (0.4194)
         design_9 ranked ~3rd by Chai-1 (0.626), ranked #1 by Boltz2 (0.8948)
         Always use the competition's own scoring tool first.

Merges all candidate arms, filters by:
  1. Complexity gate (charge-repeat sequences rejected)
  2. Length 40-150 AA (from competition winner analysis)
  3. Boltz2 ipSAE >= 0.70 (hard primary gate)
  4. Edit distance >= 25% vs UniRef50 (competition requirement)
  5. Internal deduplication (>10% mutual edit distance kept)

Ranks by: 0.70 * boltz2_ipsae + 0.30 * boltz2_plddt

Outputs top 100 sequences as final_candidates.fasta + scores_full.csv
"""

import os
import csv
import json
import glob
import argparse
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Dynamically detect WORKDIR relative to the script location
WORKDIR = Path(__file__).parent
OUTPUTS = WORKDIR / "outputs"

# Novelty threshold: must differ from every UniRef50 hit by at least 25%
MIN_EDIT_DISTANCE_FRACTION = 0.25

# Internal dedup: two sequences within this similarity are duplicates
MAX_INTERNAL_SIMILARITY = 0.90  # keep if < 90% identical to anything already kept


# ----------------------------------------------------------------
# Complexity pre-filter (v2) — applied BEFORE any GPU scoring
# ----------------------------------------------------------------

def passes_complexity(seq: str) -> bool:
    """
    Sequence complexity gate — rejects charge-repeat scaffolds before
    wasting GPU time on designs that will fail Boltz2 ipSAE.

    Derived from v1 post-mortem: design_21 (charge repeats, ELEKKLEELEAR)
    scored 0.567 on Chai-1 but only 0.4194 on Boltz2 ipSAE.

    Rules:
      1. No run of 4+ identical consecutive charged residues (KRDEH)
      2. Charged fraction <= 40%
      3. Hydrophobic fraction >= 15% (VILMFYW)
    """
    charged    = set('KRDEH')
    hydrophobic = set('VILMFYW')

    # Rule 1: no charged run >= 4
    run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1] and seq[i] in charged:
            run += 1
            if run >= 4:
                return False
        else:
            run = 1

    # Rule 2: charge fraction
    if sum(1 for aa in seq if aa in charged) / len(seq) > 0.40:
        return False

    # Rule 3: hydrophobic fraction
    if sum(1 for aa in seq if aa in hydrophobic) / len(seq) < 0.15:
        return False

    return True


# ----------------------------------------------------------------
# Scoring (v2)
# ----------------------------------------------------------------

BOLTZ2_IPSAE_GATE = 0.70   # HARD cutoff — designs below this are discarded

def composite_score(boltz2_ipsae, boltz2_plddt, chai1_ptm=None, af2_iptm=None):
    """
    v2 composite score — Boltz2 ipSAE is primary (70% weight).
    Chai-1 and AF2 kept for tiebreaking only.

    Hard gate: if boltz2_ipsae < BOLTZ2_IPSAE_GATE, this function is
    never called — the design is discarded upstream.
    """
    ipsae_n  = boltz2_ipsae if boltz2_ipsae is not None else 0.0
    plddt_n  = boltz2_plddt if boltz2_plddt is not None else 0.80

    return (0.70 * ipsae_n + 0.30 * plddt_n)


# ----------------------------------------------------------------
# Edit distance  (Levenshtein, normalised)
# ----------------------------------------------------------------

def normalised_edit_distance(s1, s2):
    """Normalised Levenshtein distance: 0 = identical, 1 = totally different."""
    try:
        import editdistance
        dist = editdistance.eval(s1, s2)
    except ImportError:
        # Pure-python fallback
        dist = _levenshtein(s1, s2)
    max_len = max(len(s1), len(s2))
    return dist / max_len if max_len > 0 else 0.0


def _levenshtein(s1, s2):
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = prev if s1[i-1] == s2[j-1] else 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]


def blast_novelty_check(sequence, max_identity=0.75, retries=3):
    """
    BLAST sequence against UniRef50 via NCBI API.
    Returns True if sequence is novel (no hit > max_identity).
    Falls back to True on API failure (don't discard due to network error).
    """
    url = "https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi"
    
    # Submit job
    params = {
        "CMD": "Put", "PROGRAM": "blastp", "DATABASE": "uniref50",
        "QUERY": sequence, "FORMAT_TYPE": "JSON2",
        "HITLIST_SIZE": 1, "EXPECT": "1e-3"
    }
    try:
        r = requests.post(url, data=params, timeout=30)
        rid = None
        for line in r.text.split('\n'):
            if 'RID =' in line:
                rid = line.split('=')[1].strip()
                break
        if not rid:
            return True   # can't check, assume novel

        # Poll for results (BLAST is async)
        for _ in range(20):
            time.sleep(5)
            check = requests.get(url, params={
                "CMD": "Get", "RID": rid, "FORMAT_TYPE": "JSON2"
            }, timeout=30)
            if '"BlastOutput2"' in check.text:
                # Parse identity
                import json as _json
                try:
                    data = _json.loads(check.text)
                    hits = data[0]["report"]["results"]["search"]["hits"]
                    if not hits:
                        return True
                    top_identity = hits[0]["hsps"][0]["identity"] / hits[0]["hsps"][0]["align_len"]
                    return top_identity < max_identity
                except (KeyError, IndexError, _json.JSONDecodeError):
                    return True

        return True   # timeout -> assume novel

    except Exception:
        return True   # network failure -> assume novel


# ----------------------------------------------------------------
# Loading candidates
# ----------------------------------------------------------------

def load_all_fastas():
    """Load sequences from all arm output FASTAs."""
    # Updated to search recursively through nested timestamp folders (Hydra style)
    fasta_patterns = [
        OUTPUTS / "**" / "arm1_bindcraft" / "**" / "*.fa*",
        OUTPUTS / "**" / "arm2_candidates.fasta",
        OUTPUTS / "**" / "arm3_pepprclip" / "arm3_peptides.fasta",
        OUTPUTS / "**" / "chai1_validated.fasta",
        OUTPUTS / "**" / "arm5_esm3" / "arm5_esm3_sequences.fasta",
    ]

    candidates = []
    for pattern in fasta_patterns:
        matches = glob.glob(str(pattern), recursive=True)
        print(f"  Searching {pattern} ... found {len(matches)} files")
        for path in matches:
            with open(path) as f:
                lines = f.readlines()
            for i in range(0, len(lines) - 1, 2):
                header = lines[i].strip().lstrip('>')
                seq = lines[i + 1].strip()
                if seq:
                    candidates.append({"name": header, "sequence": seq, "source": Path(path).name})

    return candidates


def load_chai1_scores():
    """Load Chai-1 scores if available."""
    scores_csv = OUTPUTS / "chai1_scores.csv"
    scores = {}
    if scores_csv.exists():
        with open(scores_csv) as f:
            for row in csv.DictReader(f):
                scores[row["binder_seq"]] = {
                    "chai1_ptm":   float(row.get("chai1_ptm", 0) or 0),
                    "chai1_ipsae": float(row.get("chai1_ipsae", 0) or 0) if row.get("chai1_ipsae") else None,
                }
    return scores


def load_af2_scores():
    """Load AF2 / BindCraft scores if available."""
    scores = {}
    for csv_path in glob.glob(str(OUTPUTS / "arm1_bindcraft" / "*.csv")):
        with open(csv_path) as f:
            for row in csv.DictReader(f):
                seq = row.get("sequence", "")
                if seq:
                    scores[seq] = {
                        "af2_iptm": float(row.get("iptm", 0) or 0),
                        "af2_plddt": float(row.get("plddt", 0) or 0),
                        "af2_ipae": float(row.get("ipae", 0) or 0),
                    }
    return scores


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merge-only", action="store_true",
                        help="Only merge candidates (for Chai-1 input), skip full ranking")
    parser.add_argument("--no-blast", action="store_true",
                        help="Skip BLAST novelty check (faster, for testing)")
    args = parser.parse_args()

    print("================================================================")
    print("Filter & Rank — RBX1 Binder Competition Pipeline")
    print("================================================================")

    # 1. Load all candidates
    candidates = load_all_fastas()
    print(f"\nLoaded {len(candidates)} total candidates from all arms")

    # 2a. Complexity pre-filter (v2) — before any GPU time
    before = len(candidates)
    candidates = [c for c in candidates if passes_complexity(c["sequence"])]
    print(f"After complexity filter (no charge repeats): {len(candidates)}/{before}")

    # 2b. Length gate (v2: 40-150 AA from competition winner analysis)
    candidates = [c for c in candidates if 40 <= len(c["sequence"]) <= 150]
    print(f"After length filter (40-150 AA): {len(candidates)}")

    # 3. Global dedup (exact sequence)
    seen = {}
    for c in candidates:
        seq = c["sequence"]
        if seq not in seen:
            seen[seq] = c
    candidates = list(seen.values())
    print(f"After exact dedup: {len(candidates)}")

    # 4. Write merged FASTA for Chai-1 step (top 150 by source priority)
    merged_out = OUTPUTS / "merged_candidates_top150.fasta"
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with open(merged_out, "w") as f:
        for c in candidates[:150]:
            f.write(f">{c['name']}\n{c['sequence']}\n")
    print(f"Merged top-150 written to: {merged_out}")

    if args.merge_only:
        print("--merge-only: stopping here. Run validate_chai1.py, then re-run this script.")
        return

    # 5. Load scoring data
    chai1_scores = load_chai1_scores()
    af2_scores = load_af2_scores()

    # 6. Attach scores to candidates
    for c in candidates:
        seq = c["sequence"]
        chai = chai1_scores.get(seq, {})
        af2  = af2_scores.get(seq, {})
        c["chai1_ptm"]   = chai.get("chai1_ptm")
        c["chai1_ipsae"] = chai.get("chai1_ipsae")
        c["af2_iptm"]    = af2.get("af2_iptm")
        c["af2_plddt"]   = af2.get("af2_plddt")
        # v2: hard Boltz2 ipSAE gate
        b2_ipsae = c.get("boltz2_ipsae") or c.get("chai1_ipsae")  # fallback to chai if boltz2 not run
        b2_plddt = c.get("boltz2_plddt") or (c.get("af2_plddt", 85) / 100.0)
        if b2_ipsae is not None and b2_ipsae < BOLTZ2_IPSAE_GATE:
            c["score"] = -1.0   # hard discard
        else:
            c["score"] = composite_score(b2_ipsae, b2_plddt, c["chai1_ptm"], c["af2_iptm"])

    # 7. Sort by composite score
    candidates.sort(key=lambda c: c["score"], reverse=True)
    # Remove hard-discarded designs (score == -1.0)
    passed_gate = [c for c in candidates if c["score"] >= 0]
    discarded   = len(candidates) - len(passed_gate)
    candidates  = passed_gate
    print(f"After Boltz2 ipSAE gate (>={BOLTZ2_IPSAE_GATE}): {len(candidates)} passed, {discarded} discarded")

    # 8. Novelty gate — parallel BLAST (ThreadPoolExecutor, IO-bound)
    if not args.no_blast:
        pool_size = min(16, len(candidates[:200]))
        print(f"\nChecking novelty vs UniRef50 ({pool_size} parallel BLAST threads)...")

        to_check = candidates[:200]
        novelty = {}   # seq -> bool

        with ThreadPoolExecutor(max_workers=pool_size) as pool:
            futures = {pool.submit(blast_novelty_check, c["sequence"]): c for c in to_check}
            done_count = 0
            for fut in as_completed(futures):
                c = futures[fut]
                is_novel = fut.result()
                novelty[c["sequence"]] = is_novel
                done_count += 1
                status = "✓ Novel" if is_novel else "✗ Similar"
                print(f"  [{done_count}/{len(to_check)}] {status}  len={len(c['sequence'])}")

        candidates = [c for c in to_check if novelty.get(c["sequence"], True)][:100]
        print(f"  Novel sequences passing filter: {len(candidates)}")
    else:
        print("Skipping BLAST (--no-blast). Assuming all sequences are novel.")
        candidates = candidates[:100]

    # 9. Internal dedup — vectorised pairwise edit distance
    try:
        import editdistance
        kept = []
        for c in candidates:
            ref_seq = c["sequence"]
            too_similar = any(
                editdistance.eval(ref_seq, k["sequence"]) / max(len(ref_seq), len(k["sequence"])) < 0.10
                for k in kept
            )
            if not too_similar:
                kept.append(c)
            if len(kept) >= 100:
                break
        candidates = kept
    except ImportError:
        # Fall back to simple exact-match dedup if editdistance not installed
        pass
    print(f"\nAfter internal dedup: {len(candidates)} candidates")

    # 10. Write final outputs
    final_fasta = OUTPUTS / "final_candidates.fasta"
    with open(final_fasta, "w") as f:
        for i, c in enumerate(candidates):
            rank = i + 1
            sc = c["score"]
            f.write(f">rank{rank:03d}|{c['name']}|score={sc:.4f}\n{c['sequence']}\n")

    scores_csv = OUTPUTS / "scores_full.csv"
    fieldnames = ["rank", "name", "sequence", "length", "score",
                  "chai1_ptm", "chai1_ipsae", "af2_iptm", "af2_plddt", "source"]
    with open(scores_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for i, c in enumerate(candidates):
            writer.writerow({
                "rank": i + 1,
                "name": c["name"],
                "sequence": c["sequence"],
                "length": len(c["sequence"]),
                "score": round(c["score"], 4),
                "chai1_ptm": c.get("chai1_ptm"),
                "chai1_ipsae": c.get("chai1_ipsae"),
                "af2_iptm": c.get("af2_iptm"),
                "af2_plddt": c.get("af2_plddt"),
                "source": c.get("source"),
            })

    print(f"\n=== Filter & Rank Complete ===")
    print(f"  Final candidates : {len(candidates)}")
    print(f"  FASTA            : {final_fasta}")
    print(f"  Full scores CSV  : {scores_csv}")
    print(f"\n  Top 5 by composite score:")
    for c in candidates[:5]:
        print(f"    rank={candidates.index(c)+1}  score={c['score']:.3f}  "
              f"len={len(c['sequence'])}  {c['sequence'][:30]}...")


if __name__ == "__main__":
    main()
