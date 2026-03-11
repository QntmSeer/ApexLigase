import os
import sys
import glob
from pathlib import Path
from Bio.PDB import MMCIFParser, PDBIO

def convert_cif_to_pdb(cif_path, pdb_path):
    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure("complex", cif_path)
    io = PDBIO()
    io.set_structure(structure)
    io.save(pdb_path)

print("Initializing PyRosetta...")
import pyrosetta
from pyrosetta import rosetta
pyrosetta.init("-mute all")
from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover

TARGETS = ["rfd_binder_38", "rfd_binder_61"]
BASE_DIR = Path("/home/qntmqrks/rbx1_design/Phase13_Chai1")

def score_binder(binder_name):
    # Find the best cif model based on aggregate_score (or just test model 1 since we know it's best for 61, but let's just score the one with the best aggregate score).
    # We printed the best score in chai1_scores.txt but we can just score all of them or the best one.
    
    # Let's read the scores file that our chai1_validate.py wrote
    best_cif = None
    best_score = -1
    
    # Just grab all pred.model_idx_*.cif and score them.
    cif_files = glob.glob(str(BASE_DIR / binder_name / "pred.model_idx_*.cif"))
    
    results = []
    for cif in cif_files:
        pdb = cif.replace(".cif", ".pdb")
        convert_cif_to_pdb(cif, pdb)
        
        # Load into PyRosetta
        try:
            pose = pyrosetta.pose_from_file(pdb)
            # Chai-1 generated models usually have chain A (target) and chain B (binder)
            iam = InterfaceAnalyzerMover("A_B")
            iam.set_pack_separated(True)
            iam.apply(pose)
            
            # The ddG of binding
            ddG = iam.get_interface_dG()
            results.append((cif, ddG))
            print(f"[{binder_name}] {os.path.basename(cif)} -> ddG={ddG:.2f} REU")
        except Exception as e:
            print(f"Failed to score {cif}: {e}")
            
    # Print the best binding energy (most negative)
    if results:
        results.sort(key=lambda x: x[1])
        print(f"--> {binder_name} BEST ddG: {results[0][1]:.2f} REU ({os.path.basename(results[0][0])})")
        
for t in TARGETS:
    score_binder(t)
