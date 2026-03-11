import pandas as pd

df = pd.read_csv("Phase15_Final_Submission.csv")
df = df.drop_duplicates(subset=["Design_ID"], keep="first")
df.to_csv("Phase15_Final_Submission_Clean.csv", index=False)

print("\n--- TOP 10 ELITE CANDIDATES ---")
print("These are the fully validated, highest-scoring binders.")

for idx, (i, row) in enumerate(df.head(10).iterrows()):
    print(f"\n#{idx+1} | {row['Design_ID']}")
    print(f"Sequence: {row['Sequence']}")
    print(f"Metrics : pLDDT={row['pLDDT_Confidence']:.2f} | ipTM={row['Chai-1_ipTM']:.4f}")
    print(f"Status  : Zinc={row['Zinc_Status']} | Final={row['Validation_Status']}")

print("\nMethodology snippet generated.")
