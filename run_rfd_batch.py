import subprocess
import os

# Define the target and hotspots
target_pdb = '/home/qntmqrks/rbx1_design/target/rbx1_ring.pdb'
hotspots = 'A43,A44,A46,A54,A55,A57,A58,A87,A91,A95,A96'
output_dir = '/home/qntmqrks/rbx1_design/Phase10_RFdiffusion/outputs'
num_designs = 100

# RFdiffusion command template
# In some installations, the dot notation fails if the parent dict doesn't exist
# We will try the most atomic override format: individual flags without quotes where possible
cmd = [
    '/opt/conda/bin/conda', 'run', '--no-capture-output', '-n', 'SE3nv', 'python', '/home/qntmqrks/RFdiffusion/scripts/run_inference.py',
    f'inference.output_prefix={output_dir}/rfd_binder',
    f'inference.input_pdb={target_pdb}',
    f'inference.num_designs={num_designs}',
    f'\"ppi.hotspot_res=[{hotspots}]\"',
    '\"contig.contigs=[A1-108/0 50-70]\"'
]

# Alternative: Using a temporary config file override
# But first, let's try the absolute canonical string format
# Some RFdiffusion versions require ['A1-108/0 50-70'] (notes quotes inside brackets)

print(f'Launching RFdiffusion targeting hotspots: {hotspots}')
full_cmd = ' '.join(cmd)
print(f'Command: {full_cmd}')
subprocess.run(full_cmd, shell=True)
