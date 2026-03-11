import torch
from esm.models.esm3 import ESM3
from esm.sdk.api import ESMProtein, LogitsConfig

client = ESM3.from_pretrained("esm3_sm_open_v1").to("cuda" if torch.cuda.is_available() else "cpu")
protein = ESMProtein(sequence="ACDEFGHIKLMNPQRSTVWY")
tensor = client.encode(protein)
print("tensor.sequence shape:", tensor.sequence.shape)
out = client.logits(tensor, LogitsConfig(sequence=True))
seq_tensor = out.logits.sequence
print("out.logits.sequence shape:", seq_tensor.shape if seq_tensor is not None else "None")
print("out.logits fields:", dir(out.logits))
