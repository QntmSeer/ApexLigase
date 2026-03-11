import mdtraj as md
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def create_gif(pdb_file, dcd_file, output_gif):
    print(f"Loading topology {pdb_file} and trajectory {dcd_file}...")
    traj = md.load(dcd_file, top=pdb_file)
    
    # We want to animate the alpha carbons only for clarity
    ca_indices = traj.top.select('name CA')
    traj_ca = traj.atom_slice(ca_indices)
    
    # Center the trajectory on the origin to stop it from jumping around
    traj_ca.center_coordinates()
    
    print(f"Loaded {len(traj_ca)} frames.")
    
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_axis_off()
    
    # Set axis limits based on the min/max coordinates across all frames
    xyz = traj_ca.xyz
    min_xyz = np.min(xyz, axis=(0, 1))
    max_xyz = np.max(xyz, axis=(0, 1))
    
    ax.set_xlim(min_xyz[0], max_xyz[0])
    ax.set_ylim(min_xyz[1], max_xyz[1])
    ax.set_zlim(min_xyz[2], max_xyz[2])
    
    first_frame = xyz[0]
    scatter = ax.scatter(first_frame[:, 0], first_frame[:, 1], first_frame[:, 2], 
                         c='blue', marker='o', s=10, alpha=0.5)
                         
    # Also draw lines connecting the C-alphas to show the backbone
    lines, = ax.plot(first_frame[:, 0], first_frame[:, 1], first_frame[:, 2], color='black', alpha=0.3)
    
    def update(num):
        # Update coordinates and backbone line
        current_frame = xyz[num]
        scatter._offsets3d = (current_frame[:, 0], current_frame[:, 1], current_frame[:, 2])
        lines.set_data(current_frame[:, 0], current_frame[:, 1])
        lines.set_3d_properties(current_frame[:, 2])
        return scatter, lines
        
    print("Animating frames...")
    ani = animation.FuncAnimation(fig, update, frames=len(traj_ca), blit=False, interval=50)
    
    print(f"Saving to {output_gif}...")
    ani.save(output_gif, writer='pillow', fps=20)
    print("Done!")

if __name__ == '__main__':
    create_gif('structures/4AKE_h.pdb', 'test_traj.dcd', 'C:/Users/Gebruiker/.gemini/antigravity/brain/6d7c4b60-669a-4a05-ab38-a1dead1613d0/test_simulation.gif')
