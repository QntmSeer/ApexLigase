import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import MDAnalysis as mda
import os

def generate_animation(pdb_file, xtc_file, output_file):
    print(f"Loading trajectory: {xtc_file} with pdb: {pdb_file}")
    u = mda.Universe(pdb_file, xtc_file)
    protein = u.select_atoms("protein")
    rbx1 = u.select_atoms("resid 1-50") # Adjust based on actual residue numbering
    binder = u.select_atoms("resid 51-133") # Adjust based on actual residue numbering
    
    fig = plt.figure(figsize=(10, 8), facecolor='black')
    ax = fig.add_subplot(111, projection='3d', facecolor='black')
    
    # Set plot limits based on protein dimensions
    coords = protein.positions
    min_xyz = coords.min(axis=0)
    max_xyz = coords.max(axis=0)
    center = (min_xyz + max_xyz) / 2
    span = (max_xyz - min_xyz).max() / 2
    
    def update(frame):
        ax.clear()
        ax.set_facecolor('black')
        u.trajectory[frame]
        
        # Color palettes
        # RBX1: Sleek Cyan/Blue
        # Binder: Vibrant Orange/Gold
        ax.scatter(rbx1.positions[:, 0], rbx1.positions[:, 1], rbx1.positions[:, 2], 
                   c='#00f2ff', s=2, alpha=0.6, label='RBX1')
        ax.scatter(binder.positions[:, 0], binder.positions[:, 1], binder.positions[:, 2], 
                   c='#ff9100', s=2, alpha=0.8, label='Design_9 Binder')
        
        ax.set_xlim(center[0] - span, center[0] + span)
        ax.set_ylim(center[1] - span, center[1] + span)
        ax.set_zlim(center[2] - span, center[2] + span)
        
        ax.axis('off')
        ax.set_title(f"Design_9 vs RBX1 - Time: {u.trajectory.time/1000:.1f} ns", 
                     color='white', fontsize=12, fontweight='bold', pad=20)
        
        # Continuous rotation for dynamic feel
        ax.view_init(elev=20., azim=frame * 0.5)
        
        if frame == 0:
            ax.legend(loc='upper right', facecolor='black', edgecolor='white', labelcolor='white')

    print("Rendering animation...")
    num_frames = len(u.trajectory)
    # Slowing down: interval from 50ms to 150ms
    ani = animation.FuncAnimation(fig, update, frames=range(0, num_frames, 1), interval=150)
    
    # Save as high-quality MP4/GIF
    # Lowering FPS from 20 to 10 for slower playback
    writer = animation.FFMpegWriter(fps=10, metadata=dict(artist='Antigravity'), bitrate=2000)
    ani.save(output_file, writer=writer)
    plt.close()
    print(f"Success: Animation saved to {output_file}")

if __name__ == "__main__":
    if os.path.exists('md_viz_fixed.xtc') and os.path.exists('design_9_viz.pdb'):
        generate_animation('design_9_viz.pdb', 'md_viz_fixed.xtc', 'design_9_simulation.mp4')
    else:
        print("Error: Missing fixed trajectory or pdb files.")
