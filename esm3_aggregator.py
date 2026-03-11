import os
import glob
import json
import torch
import numpy as np
import pandas as pd
from Bio import SeqIO
from esm.models.esm3 import ESM3
from esm.sdk.api import ESMProtein, LogitsConfig

# Paths
PROCESSED_DIR = "/home/qntmqrks/rbx1_design/Phase11_Optimization/processed"
RFD_OUTPUT = "/home/qntmqrks/rbx1_design/Phase10_RFdiffusion/outputs"
OUTPUT_CSV = "/home/qntmqrks/rbx1_design/Phase12_Scoring/esm3_ranked_roster.csv"
OUTPUT_FASTA = "/home/qntmqrks/rbx1_design/Phase12_Scoring/esm3_ranked_roster.fa"

def gather_pmpnn_data():
    """Compiles all ProteinMPNN sequences and their corresponding pLDDTs."""
    print("Gathering ProteinMPNN sequences...")
    roster = []
    
    pdbs = [d for d in os.listdir(PROCESSED_DIR) if os.path.isdir(os.path.join(PROCESSED_DIR, d))]
    
    for pdb_dir in pdbs:
        seq_dir = os.path.join(PROCESSED_DIR, pdb_dir, "seqs")
        fasta_files = glob.glob(os.path.join(seq_dir, "*.fa"))
        
        skip_file = os.path.join(PROCESSED_DIR, pdb_dir, "skipped_low_plddt.txt")
        if os.path.exists(skip_file):
            continue
            
        if not fasta_files:
            continue
            
        target_fasta = None
        for f in fasta_files:
            if pdb_dir in os.path.basename(f):
                target_fasta = f
                break
                
        if not target_fasta and len(fasta_files) > 0:
            target_fasta = fasta_files[0]
            
        if not target_fasta:
            continue
            
        for record in SeqIO.parse(target_fasta, "fasta"):
            desc = record.description
            try:
                score_part = desc.split("score=")[1]
                pmpnn_score = float(score_part.split(",")[0])
            except Exception:
                pmpnn_score = 999.0
            
            if "T=" in desc and "score=" in desc:
                 seq_str = str(record.seq)
                 parts = seq_str.split("/")
                 if len(parts) == 2:
                     target_seq = parts[0]
                     binder_seq = parts[1] # Chain B
                     
                     roster.append({
                         "design_id": f"{pdb_dir}_pmpnn",
                         "target_seq": target_seq,
                         "binder_seq": binder_seq,
                         "pmpnn_score": pmpnn_score,
                         "pdb_source": pdb_dir
                     })

    return pdbs, pd.DataFrame(roster)

def score_with_esm3(df, client):
    """Scores a dataframe of sequences using ESM3 forward tracking."""
    print(f"Scoring {len(df)} sequences with ESM3-sm-open-v1...")
    
    scores = []
    with torch.no_grad():
        for idx, row in df.iterrows():
            # To get a meaningful sequence likelihood, we pass the Binder Sequence mapped conceptually.
            # Using only the binder sequence to gauge intrinsic folding stability from ESM3 language prior.
            seq = row["binder_seq"]
            try:
                 protein = ESMProtein(sequence=seq)
                 tensor = client.encode(protein)
                 
                 # Get sequence logits: shape [1, L, V=64]
                 logits_out = client.logits(tensor, LogitsConfig(sequence=True))
                 seq_logits = logits_out.logits.sequence.squeeze(0)  # [L, V]
                 
                 # Calculate log likelihood of the actual sequence tokens
                 tokens = tensor.sequence  # [L]
                 log_probs = torch.nn.functional.log_softmax(seq_logits, dim=-1)  # [L, V]
                 
                 # Gather log_probs at actual token positions
                 token_log_probs = log_probs.gather(1, tokens.unsqueeze(1).long()).squeeze(1)  # [L]
                 
                 mean_log_prob = float(token_log_probs.mean().cpu())
                 
                 scores.append(mean_log_prob)
                 print(f"[{idx+1}/{len(df)}] Scored {row['design_id']}: ESM3 log-likelihood = {mean_log_prob:.4f}")
                 
            except Exception as e:
                 print(f"[{idx+1}/{len(df)}] Error scoring {row['design_id']}: {e}")
                 scores.append(-999.0)
             
    df["esm3_score"] = scores
    return df

def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    pdbs, roster_df = gather_pmpnn_data()
    print(f"Found {len(pdbs)} completed backbones, expanding to {len(roster_df)} ProteinMPNN candidates.")
    
    if len(roster_df) == 0:
        print("No candidates found. Exiting.")
        return

    # Filter to top 50 based on PMPNN score to save ESM3 inference time (O(1))
    roster_df = roster_df.sort_values("pmpnn_score", ascending=True).head(50).reset_index(drop=True)
    
    # Initialize ESM3 (Requires HF_TOKEN env var for caching weights)
    print("Loading ESM3 sm_open_v1 weights to CUDA...")
    client = ESM3.from_pretrained("esm3_sm_open_v1").to("cuda" if torch.cuda.is_available() else "cpu")
    
    scored_df = score_with_esm3(roster_df, client)
    
    # Rank by ESM3 log-likelihood (higher is better, e.g., -1.5 is better than -3.2)
    final_df = scored_df.sort_values("esm3_score", ascending=False).reset_index(drop=True)
    
    # Save CSV
    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved ranked results to {OUTPUT_CSV}")
    
    # Save Top 10 FASTA
    top10 = final_df.head(10)
    with open(OUTPUT_FASTA, "w") as f:
        for idx, row in top10.iterrows():
            f.write(f">{row['design_id']} | ESM3: {row['esm3_score']:.4f} | PMPNN: {row['pmpnn_score']:.4f}\n")
            # Reconstruct full AB chain sequence matching MPNN format
            f.write(f"{row['target_seq']}/{row['binder_seq']}\n")
    print(f"Saved top 10 FASTA to {OUTPUT_FASTA}")

if __name__ == "__main__":
    main()
