import torch
import pandas as pd
import os
import gc
import re
from pathlib import Path
from esm.models.esm3 import ESM3
from esm.sdk.api import ESMProtein, LogitsConfig

def clean_sequence(s):
    return re.sub(r'[^A-Z]', '', s.upper())

def is_valid_protein(name, seq):
    if len(seq) < 10: return False
    if len(set(seq)) < 5: return False # Ensure it's not poly-G/S
    return True

def parse_fasta(p):
    seqs = []
    try:
        with open(p, 'r') as f:
            name, seq = "", ""
            for line in f:
                if line.startswith(">"):
                    if name and seq:
                        cs = clean_sequence(seq)
                        if is_valid_protein(name, cs): seqs.append((name, cs))
                    name, seq = line[1:].strip(), ""
                else: seq += line.strip()
            if name and seq:
                cs = clean_sequence(seq)
                if is_valid_protein(name, cs): seqs.append((name, cs))
    except: pass
    return seqs

def score_extract(output):
    l = getattr(output, 'logits', None)
    if l is not None:
        s = getattr(l, 'sequence', None)
        if s is not None and hasattr(s, 'mean'):
            return s.mean().item()
    return 0.0

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device} | Loading ESM3...")
model = ESM3.from_pretrained("esm3_sm_open_v1").to(device).eval()

def run_tournament():
    results = []
    seen_seqs = set()
    
    home = os.path.expanduser("~")
    target_file = Path(home) / "chai_validation/arm3_peptides.fasta"
    
    if not target_file.exists():
        print("Searching system for arm3_peptides.fasta...")
        found = list(Path(home).rglob("arm3_peptides.fasta"))
        if not found:
            print("!! ERROR: No binders found.")
            return
        target_file = found[0]

    print(f"Scoring: {target_file}")
    pool = parse_fasta(target_file)
    print(f"Tournament size: {len(pool)} real sequences.")
    
    for name, seq in pool:
        if seq in seen_seqs: continue
        seen_seqs.add(seq)
        print(f"Scoring {name}...", end=" ", flush=True)
        try:
            protein = ESMProtein(sequence=seq)
            with torch.no_grad():
                encoded = model.encode(protein).to(device)
                output = model.logits(encoded, LogitsConfig(sequence=True))
                score = score_extract(output)
                print(f"Score: {score:.4f}")
                results.append({"Rank": 0, "Name": name, "Fitness": score, "Sequence": seq})
            del encoded, output, protein
            gc.collect(); torch.cuda.empty_cache()
        except: print("FAILED.")

    if results:
        df = pd.DataFrame(results).sort_values("Fitness")
        df['Rank'] = range(1, len(df) + 1)
        df.to_csv("/home/qntmqrks/RBX1_FINAL_SUBMISSION.csv", index=False)
        print("\n--- [GOLD] THE CLEAN LEADERBOARD IS READY ---")
        print(df.head(20))
    else:
        print("!! FAILURE: No valid sequences were scored.")

if __name__ == "__main__":
    run_tournament()
