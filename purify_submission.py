import os
import glob
import json
import pandas as pd
import numpy as np

PROJECT_DIR = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration"
LEADERBOARD = os.path.join(PROJECT_DIR, "leaderboard.csv")
PMPNN_DIR = os.path.join(PROJECT_DIR, "pmpnn")
FOLDING_DIR = os.path.join(PROJECT_DIR, "folding")
OUTPUT_CSV = os.path.join(PROJECT_DIR, "Phase15_Final_Submission.csv")

def extract_chai_scores(design_id):
    score_file = os.path.join(FOLDING_DIR, design_id, "scores.model_idx_0.npz")
    if not os.path.exists(score_file):
        return None, None
    try:
        data = np.load(score_file)
        iptm = data['iptm'].item()
        ptm = data['ptm'].item()
        return round(iptm, 4), round(ptm, 4)
    except Exception as e:
        return None, None

def extract_sequence(design_id):
    seq_dir = os.path.join(PMPNN_DIR, design_id, "seqs")
    fa_files = glob.glob(os.path.join(seq_dir, "*.fa"))
    if not fa_files: return None
    try:
        with open(fa_files[0], 'r') as f:
            lines = f.readlines()
            if len(lines) >= 4:
                # Same bugfix as validator.py: seq string may be AAAA/BBBB
                seq = lines[3].strip().split('/')[-1]
                return seq
    except Exception:
        pass
    return None

def compile_submission():
    if not os.path.exists(LEADERBOARD):
        print(f"Error: {LEADERBOARD} not found.")
        return

    df = pd.read_csv(LEADERBOARD)
    
    records = []
    for _, row in df.iterrows():
        design_id = row['Design']
        plddt = row['pLDDT']
        status = row['Status']
        
        sequence = extract_sequence(design_id)
        iptm, ptm = extract_chai_scores(design_id)
        
        records.append({
            "Design_ID": design_id,
            "Sequence": sequence,
            "pLDDT_Confidence": plddt,
            "Chai-1_ipTM": iptm,
            "Chai-1_pTM": ptm,
            "Zinc_Status": row.get('Zinc_Stability', 'SAFE'),
            "Validation_Status": status if pd.notnull(iptm) else "FOLDING_FAILED"
        })
        
    final_df = pd.DataFrame(records)
    # Sort by ipTM descending
    final_df = final_df.sort_values(by="Chai-1_ipTM", ascending=False)
    final_df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n[SUCCESS] Final Submission Data compiled successfully!")
    print(f"Total entries: {len(final_df)}")
    print(f"Top 5 Candidates by Chai-1 ipTM:")
    print(final_df.head(5).to_string(index=False))

if __name__ == "__main__":
    compile_submission()
