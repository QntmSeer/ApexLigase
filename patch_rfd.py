import os

file_path = '/home/qntmqrks/RFdiffusion/rfdiffusion/inference/model_runners.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Patch 1: Robust _preprocess (standardizing input for MSA features)
    # We look for the place where msa_masked is assigned seq[None, None]
    if 'msa_masked[:, :, :, :22] = seq[None, None]' in line:
        # Check if we already added the robust logic
        if 'seq.argmax(-1)' not in new_lines[-1] and 'seq.argmax(-1)' not in new_lines[-2]:
            indent = line[:line.find('msa_masked')]
            new_lines.append(f"{indent}if len(seq.shape) > 1: seq = seq.argmax(-1)\n")
            new_lines.append(f"{indent}seq = torch.nn.functional.one_hot(seq.long(), num_classes=22).to(self.device).float()\n")
    
    # Patch 2: Removing recursive one-hot in sample_step
    if 'seq_t_1 = nn.one_hot(seq_init' in line:
        indent = line[:line.find('seq_t_1')]
        new_lines.append(f"{indent}seq_t_1 = seq_init\n")
        continue # Skip the original line
    
    new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("Successfully applied definitive RFdiffusion patches.")
