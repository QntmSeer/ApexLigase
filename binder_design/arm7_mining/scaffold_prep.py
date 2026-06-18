import json
import glob
import os
from pathlib import Path

# Competition v2 complexity gate (from filter_and_rank.py)
def passes_complexity(seq: str) -> bool:
    charged    = set('KRDEH')
    hydrophobic = set('VILMFYW')
    
    # Rule 1: no charged run >= 4
    run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1] and seq[i] in charged:
            run += 1
            if run >= 4: return False
        else:
            run = 1
    
    # Rule 2: charge fraction
    if sum(1 for aa in seq if aa in charged) / len(seq) > 0.40:
        return False
        
    # Rule 3: hydrophobic fraction
    if sum(1 for aa in seq if aa in hydrophobic) / len(seq) < 0.15:
        return False
        
    return True

def extract_candidates(json_path, top_n=500):
    """Parses Foldseek result JSON and extracts candidate sequences."""
    print(f"Processing Foldseek hits in {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    hits_data = data.get("results", [])
    if not hits_data:
        return []

    candidates = []
    for db_res in hits_data:
        db_name = db_res.get("db", "unknown")
        alignments = db_res.get("alignments", [])
        for aln_group in alignments:
            for hit in aln_group:
                # Foldseek aligns sequences. We want the full database sequence if possible.
                # If unavailable, we take the alignment string (dbAln) stripped of gaps.
                # Note: dbLen is available.
                raw_seq = hit.get("dbAln", "").replace("-", "")
                target_id = hit.get("target", "Unknown")
                eval_ = hit.get("eval", 1.0)
                
                if not raw_seq: continue
                
                # Filter by v2 complexity gate
                if passes_complexity(raw_seq):
                    candidates.append({
                        "id": f"{target_id} | db={db_name}",
                        "seq": raw_seq,
                        "eval": eval_
                    })

    # Sort by E-value and take unique sequences
    candidates.sort(key=lambda x: x["eval"])
    
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c["seq"] not in seen:
            seen.add(c["seq"])
            unique_candidates.append(c)
            if len(unique_candidates) >= top_n:
                break
                
    return unique_candidates

def main():
    # Find all mining JSON results
    json_files = glob.glob("target/mining_d9_full/*.json")
    if not json_files:
        print("No result files found in target/mining_d9_full/")
        return

    all_candidates = []
    for path in json_files:
        all_candidates.extend(extract_candidates(path))

    # Master dedup
    seen = set()
    final = []
    for c in all_candidates:
        if c["seq"] not in seen:
            seen.add(c["seq"])
            final.append(c)
            
    # Sort and limit
    final.sort(key=lambda x: x["eval"])
    final = final[:1000]

    out_fasta = "binder_design/arm7_mining/mining_candidates.fasta"
    with open(out_fasta, "w") as f:
        for i, c in enumerate(final):
            f.write(f">mining_{i:04d}|{c['id'][:100]}\n{c['seq']}\n")

    print(f"\nSaved {len(final)} unique, complexity-filtered candidates to {out_fasta}")

if __name__ == "__main__":
    main()
