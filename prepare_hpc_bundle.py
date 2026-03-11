import os
import zipfile

def create_hpc_bundle(bundle_name='hpc_md_run.zip'):
    """Zips the necessary files for execution."""
    # Ensure the structures are included correctly
    files_to_bundle = [
        'run_production.py',
        'analyze_trajectory.py',
        'hpc_submit.sh',
        'structures/4AKE.pdb',
        'structures/1AKE.pdb',
    ]
    
    print(f"Creating HPC bundle: {bundle_name}...")
    
    with zipfile.ZipFile(bundle_name, 'w') as zipf:
        for file in files_to_bundle:
            if os.path.exists(file):
                zipf.write(file)
                print(f"  Added {file}")
            else:
                print(f"  WARNING: {file} not found in the current directory!")
                
    print(f"\nBundle {bundle_name} is ready!")
    print("Unzip it and run: python run_production.py")

if __name__ == '__main__':
    create_hpc_bundle()
