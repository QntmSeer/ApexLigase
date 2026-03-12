import argparse
import sys
import os
from pathlib import Path
import pyrosetta
from pyrosetta import rosetta

def generate_trajectory(pdb_path, outdir):
    pyrosetta.init('-relax:constrain_relax_to_start_coords -relax:coord_constrain_sidechains -out:level 100')
    
    pdb_path = Path(pdb_path)
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(output_dir))
    
    pose = pyrosetta.pose_from_pdb(str(pdb_path))
    scorefxn = pyrosetta.get_fa_scorefxn()
    
    iam = rosetta.protocols.analysis.InterfaceAnalyzerMover("A_B")
    iam.set_pack_separated(True)
    
    # Save first frame
    pose.dump_pdb("traj_000.pdb")
    
    movemap = rosetta.core.kinematics.MoveMap()
    movemap.set_bb(True)
    movemap.set_chi(True)
    movemap.set_jump(True)
    
    # Setup FastRelax with a custom script for fine steps
    fr = rosetta.protocols.relax.FastRelax()
    fr.set_scorefxn(scorefxn)
    fr.constrain_relax_to_start_coords(True)
    fr.set_movemap(movemap)
    fr.set_task_factory(rosetta.core.pack.task.TaskFactory())
    
    print("Beginning High-Resolution FastRelax trajectory (100 frames)...")
    
    # We will do 100 small steps to capture a smooth movie
    for i in range(1, 101):
        # We alternate between small relax steps and minimization
        # to ensure physical realism while keeping the steps distinct
        if i % 5 == 0:
            # Occasional small FastRelax repeat
            fr.max_iter(10)
            fr.apply(pose)
        else:
            # Iterative minimization
            min_mover = rosetta.protocols.minimization_packing.MinMover()
            min_mover.movemap(movemap)
            min_mover.score_function(scorefxn)
            min_mover.min_type("lbfgs_armijo_nonmonotone")
            min_mover.tolerance(0.005)
            min_mover.max_iter(5)
            min_mover.apply(pose)
            
        # Calculate scores
        iam.apply(pose)
        ddG = iam.get_interface_dG()
        total_e = scorefxn(pose)
        
        # Save PDB with metadata in header for PyMOL
        frame_name = f"traj_{i:03d}.pdb"
        pose.dump_pdb(frame_name)
        if i % 10 == 0:
            print(f"Frame {i:03d}: Total Energy = {total_e:.2f}, Interface ddG = {ddG:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a high-res relaxation trajectory.")
    parser.add_argument("pdb_file", help="Path to the input PDB file.")
    parser.add_argument("--outdir", default="./traj_highres", help="Output directory.")
    args = parser.parse_args()
    
    generate_trajectory(args.pdb_file, args.outdir)
