import os
import sys
import argparse
from pathlib import Path

import pyrosetta
pyrosetta.init("-mute all -ex1 -ex2 -use_input_sc -relax:default_repeats 2")
from pyrosetta import rosetta

class PDBTrajectoryRecorder(rosetta.core.pose.metrics.PoseMetricCalculator):
    def __init__(self, prefix="frame"):
        rosetta.core.pose.metrics.PoseMetricCalculator.__init__(self)
        self.counter = 0
        self.prefix = prefix
        
    def lookup(self, key, pose):
        pass
        
    def recompute(self, pose):
        out_name = f"{self.prefix}_{self.counter:03d}.pdb"
        pose.dump_pdb(out_name)
        print(f"Dumped {out_name}")
        self.counter += 1

def generate_trajectory(pdb_path, output_dir):
    pdb_path = Path(pdb_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    os.chdir(str(output_dir))
    
    print(f"Loading {pdb_path}...")
    pose = pyrosetta.pose_from_file(str(pdb_path))
    
    scorefxn = pyrosetta.get_fa_scorefxn()
    iam = rosetta.protocols.analysis.InterfaceAnalyzerMover("A_B")
    iam.set_pack_separated(True)
    
    # Save starting structure
    pose.dump_pdb("traj_000.pdb")
    
    # Setup movemap (same as standard fast relax)
    movemap = rosetta.core.kinematics.MoveMap()
    movemap.set_bb(True)
    movemap.set_chi(True)
    movemap.set_jump(True)
    
    # FastRelax
    fast_relax = rosetta.protocols.relax.FastRelax()
    fast_relax.set_scorefxn(scorefxn)
    fast_relax.constrain_relax_to_start_coords(True)
    fast_relax.set_movemap(movemap)
    fast_relax.max_iter(500) # Ensure we don't go on forever
    
    # Since writing a C++ PyRosetta Observer is tricky, we will trick FastRelax 
    # to dump PDBs by manually doing smaller relaxations or we can use the MinMover 
    # and loop manually.
    # A cleaner approach in pure PyRosetta without overriding C++ Mover logic:
    # Use MinMover in a loop and capture frames.
    
    print("Beginning iterative Cartesian minimization for visualization...")
    min_mover = rosetta.protocols.minimization_packing.MinMover()
    min_mover.movemap(movemap)
    min_mover.score_function(scorefxn)
    min_mover.min_type("lbfgs_armijo_nonmonotone")
    min_mover.tolerance(0.01) # fairly loose to get distinct steps
    
    # Just do 20 manual mini-steps of minimization to simulate a trajectory
    for i in range(1, 21):
        min_mover.apply(pose)
        
        # Calculate ddG at this step
        iam.apply(pose)
        ddG = iam.get_interface_dG()
        total_e = scorefxn(pose)
        
        frame_name = f"traj_{i:03d}.pdb"
        pose.dump_pdb(frame_name)
        print(f"Step {i:03d}: Total Energy = {total_e:.2f}, Interface ddG = {ddG:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a relaxation trajectory.")
    parser.add_argument("pdb_file", help="Path to the input PDB file.")
    parser.add_argument("--outdir", default="./relax_traj", help="Output directory.")
    args = parser.parse_args()
    
    generate_trajectory(args.pdb_file, args.outdir)
