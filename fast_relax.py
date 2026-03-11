import os
import sys
import argparse
from pathlib import Path

# Initialize PyRosetta silently
import pyrosetta
pyrosetta.init("-mute all -ex1 -ex2 -use_input_sc -relax:default_repeats 2")
from pyrosetta import rosetta

def relax_and_score(pdb_path, output_dir):
    """Relaxes the given PDB complex and scores the interface."""
    pdb_path = Path(pdb_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading {pdb_path}...")
    pose = pyrosetta.pose_from_file(str(pdb_path))
    
    # 1. Setup ScoreFunction
    scorefxn = pyrosetta.get_fa_scorefxn() # uses ref2015 by default
    
    # 2. Setup MoveMap
    # We want to relax everything (backbone and sidechains) but we'll use distance restraints to hold the backbone close to the input.
    # An easier way is just to leave backbone fixed and only pack sidechains, but we want minor backbone movement to relieve clashes.
    # We will let FastRelax do its standard constrained protocol.
    movemap = rosetta.core.kinematics.MoveMap()
    movemap.set_bb(True)
    movemap.set_chi(True)
    movemap.set_jump(True)
    
    # 3. Setup FastRelax
    fast_relax = rosetta.protocols.relax.FastRelax()
    fast_relax.set_scorefxn(scorefxn)
    fast_relax.constrain_relax_to_start_coords(True) # Keep the topology identical to Chai-1
    fast_relax.set_movemap(movemap)
    # The default script is fine, but we can do fewer repeats to save time (default is usually 5)
    # 2 repeats is a good balance for quick but effective energy minimization
    # (Set via pyrosetta.init() above)
    
    print(f"Running Constrained FastRelax on {pdb_path.name}... (This will take 10-20 minutes)")
    fast_relax.apply(pose)
    
    # Saving relaxed structure
    relaxed_pdb = output_dir / f"{pdb_path.stem}_relaxed.pdb"
    pose.dump_pdb(str(relaxed_pdb))
    print(f"Relaxed structure saved to {relaxed_pdb}")
    
    # 4. Score the Interface
    # Assuming chains are A and B
    print("Scoring relaxed interface...")
    iam = rosetta.protocols.analysis.InterfaceAnalyzerMover("A_B")
    iam.set_pack_separated(True)
    iam.apply(pose)
    
    ddG = iam.get_interface_dG()
    print(f"\n==========================================")
    print(f"Final RELAXED ddG for {pdb_path.stem}: {ddG:.2f} REU")
    print(f"==========================================")
    
    # Write score out
    with open(output_dir / "relaxed_ddg_score.txt", "w") as f:
        f.write(f"Relaxed ddG: {ddG:.2f} REU\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Relax and score a PDB complex.")
    parser.add_argument("pdb_file", help="Path to the input PDB file.")
    parser.add_argument("--outdir", default="./relax_output", help="Output directory.")
    args = parser.parse_args()
    
    relax_and_score(args.pdb_file, args.outdir)
