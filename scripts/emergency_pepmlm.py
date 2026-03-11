import torch
import re
from esm.models.esm3 import ESM3
from esm.sdk.api import ESMProtein, GenerationConfig

# THE TARGET: RBX1 RING Domain
target_seq = "VVDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH"
mask_seq = "_" * 20 
full_prompt = target_seq + ":" + mask_seq

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading ESM3 on {device}...")
model = ESM3.from_pretrained("esm3_sm_open_v1").to(device)

# Higher temperature (1.2) for better sequence diversity
gen_config = GenerationConfig(track='sequence', temperature=1.2)

def clean_seq(s):
    # Remove <unk>, :, and non-AA characters
    return re.sub(r'[^A-Z]', '', s.replace("<unk>", ""))

with open("arm3_peptides.fasta", "w") as f:
    print("Generating 50 high-diversity binders...")
    seen = set()
    count = 0
    while count < 50:
        protein = ESMProtein(sequence=full_prompt)
        with torch.no_grad():
            output = model.generate(protein, gen_config)
            full_res = clean_seq(output.sequence)
            # The binder is the LAST 20 residues
            designed_binder = full_res[-20:]
            
            if len(designed_binder) == 20 and len(set(designed_binder)) > 5:
                if designed_binder not in seen:
                    seen.add(designed_binder)
                    count += 1
                    f.write(f">pepmlm_binder_{count}\n{designed_binder}\n")
                    print(".", end="", flush=True)

print(f"\n[SUCCESS] 50 real binders saved to ~/chai_validation/arm3_peptides.fasta")
