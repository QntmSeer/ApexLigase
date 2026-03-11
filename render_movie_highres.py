import pymol
from pymol import cmd
import glob
import os

# Initialize PyMOL in headless mode
pymol.finish_launching(['pymol', '-qc'])

# User requested high accuracy and scientifically meaningful visualization
# This includes hydrogen bonds and interface polar contacts.

WORKDIR = "/home/qntmqrks/rbx1_design/Phase14_Optimization/traj_highres"
os.chdir(WORKDIR)

# Load frames
files = sorted(glob.glob("traj_*.pdb"))
print(f"Loading {len(files)} frames for high-res movie...")

for i, f in enumerate(files):
    cmd.load(f, "traj_movie", state=i+1)

num_states = cmd.count_states("traj_movie")
print(f"States loaded: {num_states}")

if num_states > 0:
    cmd.hide("everything", "all")
    cmd.show("cartoon", "all")
    
    # Target (Chain A) and Binder (Chain B)
    cmd.color("gray70", "chain A")
    cmd.color("marine", "chain B")
    
    # Selection of interface residues
    cmd.select("interface_binder", "chain B and (all within 5.0 of chain A)")
    cmd.select("interface_target", "chain A and (all within 5.0 of chain B)")
    
    cmd.show("sticks", "interface_binder or interface_target")
    cmd.util.cnc("interface_binder or interface_target")
    
    # Rendering enhancements
    cmd.set("ray_trace_frames", 1)
    cmd.set("ray_shadows", 0)
    cmd.set("depth_cue", 1)
    cmd.set("fog", 1)
    cmd.bg_color("white")
    cmd.set("antialias", 2)
    
    # Set the view to focus on the interface
    cmd.orient("interface_binder or interface_target")
    cmd.zoom("interface_binder or interface_target", buffer=8.0)
    
    # Capture each state
    for i in range(1, num_states + 1):
        cmd.frame(i)
        
        # In each frame, identify and show polar contacts (scientifically meaningful)
        cmd.delete("h_bonds")
        # Polar contacts including H-bonds
        cmd.distance("h_bonds", "interface_binder", "interface_target", 3.2, mode=2)
        cmd.set("dash_color", "red")
        cmd.set("dash_width", 3.0)
        cmd.set("dash_radius", 0.05)
        
        frame_name = f"frame_{i:03d}.png"
        cmd.png(frame_name, width=1200, height=900, dpi=300, ray=1)
        if i % 10 == 0:
            print(f"Saved {frame_name}")
else:
    print("Error: No frames found.")

cmd.quit()
