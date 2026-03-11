import mdtraj as md
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import numpy as np
import os
import argparse
from rmsx import run_rmsx, run_rmsx_flipbook

def analyze_and_plot(open_pdb, open_dcds, closed_pdb, closed_dcds, output_dir):
    print(f"Loading topologies and {len(open_dcds)} Open replicas / {len(closed_dcds)} Closed replicas...")
    
    # Load all replica trajectories
    t_opens = [md.load(dcd, top=open_pdb) for dcd in open_dcds]
    t_closeds = [md.load(dcd, top=closed_pdb) for dcd in closed_dcds]
    
    # Concatenate replicas into single massive trajectories for global analysis
    t_open = t_opens[0] if len(t_opens) == 1 else t_opens[0].join(t_opens[1:])
    t_closed = t_closeds[0] if len(t_closeds) == 1 else t_closeds[0].join(t_closeds[1:])
    
    print(f"Aggregated {len(t_open)} Open state frames and {len(t_closed)} Closed state frames.")
    
    open_ca = t_open.top.select('name CA')
    closed_ca = t_closed.top.select('name CA')
    
    t_open_ca = t_open.atom_slice(open_ca)
    t_closed_ca = t_closed.atom_slice(closed_ca)
    
    print("Aligning trajectories...")
    t_open_ca.superpose(t_open_ca, 0)
    t_closed_ca.superpose(t_open_ca, 0)
    
    print("Calculating RMSD...")
    rmsd_open = md.rmsd(t_open_ca, t_open_ca, 0)
    rmsd_closed = md.rmsd(t_closed_ca, t_open_ca, 0)
    
    print("Performing PCA dimensionality reduction...")
    xyz_open = t_open_ca.xyz.reshape(t_open_ca.n_frames, t_open_ca.n_atoms * 3)
    xyz_closed = t_closed_ca.xyz.reshape(t_closed_ca.n_frames, t_closed_ca.n_atoms * 3)
    
    combined_xyz = np.vstack((xyz_open, xyz_closed))
    pca = PCA(n_components=2)
    reduced_cartesian = pca.fit_transform(combined_xyz)
    
    reduced_open = reduced_cartesian[:len(t_open_ca)]
    reduced_closed = reduced_cartesian[len(t_open_ca):]
    
    print("Generating PCA plots...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. RMSD Plot
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    time_points_open = np.arange(len(rmsd_open)) * 10 / 1000 
    time_points_closed = np.arange(len(rmsd_closed)) * 10 / 1000
    
    ax1.plot(time_points_open, rmsd_open, label='Open Simulation (All Reps)', color='blue', alpha=0.7)
    ax1.plot(time_points_closed, rmsd_closed, label='Closed Simulation (All Reps)', color='red', alpha=0.7)
    ax1.set_xlabel('Time (ns)')
    ax1.set_ylabel('RMSD (nm)')
    ax1.set_title('Root Mean Square Deviation from Open Reference')
    ax1.legend()
    plt.savefig(os.path.join(output_dir, 'rmsd_plot.png'), dpi=300)
    plt.close(fig1)
    
    # 2. PCA Landscape Plot
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    ax2.scatter(reduced_open[:, 0], reduced_open[:, 1], c=np.arange(len(reduced_open)), cmap='Blues', alpha=0.6, s=15, label='Open Sim')
    ax2.scatter(reduced_closed[:, 0], reduced_closed[:, 1], c=np.arange(len(reduced_closed)), cmap='Reds', alpha=0.6, s=15, label='Closed Sim')
    ax2.scatter(reduced_open[0, 0], reduced_open[0, 1], c='cyan', marker='*', s=300, edgecolor='black', zorder=5, label='Open Start')
    ax2.scatter(reduced_closed[0, 0], reduced_closed[0, 1], c='yellow', marker='*', s=300, edgecolor='black', zorder=5, label='Closed Start')
    ax2.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)')
    ax2.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)')
    ax2.set_title('Conformational Landscape (PCA)')
    ax2.legend()
    plt.savefig(os.path.join(output_dir, 'pca_landscape.png'), dpi=300)
    plt.close(fig2)
    
    print("\n--- Running High-Resolution RMSX Mapping ---")
    try:
        # Run RMSX on just the first replica of each to save generating 6 flipbooks
        rmsx_out_open = os.path.join(output_dir, "RMSX_Open_Rep1")
        print(f"Running RMSX on Open State Trajectory (Rep 1: {open_dcds[0]})...")
        run_rmsx(topology_file=open_pdb, trajectory_file=open_dcds[0], output_dir=rmsx_out_open, num_slices=10, triple=True, palette='mako', overwrite=True)
        run_rmsx_flipbook(topology_file=open_pdb, trajectory_file=open_dcds[0], output_dir=rmsx_out_open, num_slices=10, spacingFactor="0.6", palette='mako', overwrite=True)
        
        rmsx_out_closed = os.path.join(output_dir, "RMSX_Closed_Rep1")
        print(f"Running RMSX on Closed State Trajectory (Rep 1: {closed_dcds[0]})...")
        run_rmsx(topology_file=closed_pdb, trajectory_file=closed_dcds[0], output_dir=rmsx_out_closed, num_slices=10, triple=True, palette='rocket', overwrite=True)
        run_rmsx_flipbook(topology_file=closed_pdb, trajectory_file=closed_dcds[0], output_dir=rmsx_out_closed, num_slices=10, spacingFactor="0.6", palette='rocket', overwrite=True)
    except Exception as e:
        print(f"RMSX execution encountered an issue: {e}")

    print("\nAll Post-simulation processing finished!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--open_pdb', default='trajectories/4AKE_solvated.pdb', help='PDB topology for open state')
    parser.add_argument('--open_dcds', nargs='+', default=['trajectories/4AKE_open_rep1_prod.dcd', 'trajectories/4AKE_open_rep2_prod.dcd', 'trajectories/4AKE_open_rep3_prod.dcd'], help='List of DCD trajectories for open state replicas')
    parser.add_argument('--closed_pdb', default='trajectories/1AKE_solvated.pdb', help='PDB topology for closed state')
    parser.add_argument('--closed_dcds', nargs='+', default=['trajectories/1AKE_closed_rep1_prod.dcd', 'trajectories/1AKE_closed_rep2_prod.dcd', 'trajectories/1AKE_closed_rep3_prod.dcd'], help='List of DCD trajectories for closed state replicas')
    parser.add_argument('--out', default='analysis_results', help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Filter out missing files to avoid crashes if they only ran 1 replica
    valid_open = [f for f in args.open_dcds if os.path.exists(f)]
    valid_closed = [f for f in args.closed_dcds if os.path.exists(f)]
    
    if not valid_open or not valid_closed:
         print("Error: Could not find any valid production DCD files for either Open or Closed state to aggregate!")
    else:
         analyze_and_plot(args.open_pdb, valid_open, args.closed_pdb, valid_closed, args.out)
