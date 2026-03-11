import pymol
from pymol import cmd
import glob
import os

# Initialize PyMOL in headless mode
pymol.finish_launching(['pymol', '-qc'])

WORKDIR = "/home/qntmqrks/rbx1_design/Phase14_Optimization/traj"
os.chdir(WORKDIR)

# Load frames
files = sorted(glob.glob("traj_*.pdb"))
print(f"Loading {len(files)} frames...")

for i, f in enumerate(files):
    cmd.load(f, "traj_movie", state=i+1)

num_states = cmd.count_states("traj_movie")
print(f"States loaded: {num_states}")

if num_states > 0:
    cmd.hide("everything", "all")
    cmd.show("cartoon", "all")
    cmd.color("gray70", "chain A")
    cmd.color("marine", "chain B")
    
    cmd.select("interface_binder", "chain B and (all within 5.0 of chain A)")
    cmd.select("interface_target", "chain A and (all within 5.0 of chain B)")
    cmd.show("sticks", "interface_binder or interface_target")
    cmd.util.cnc("interface_binder or interface_target")
    
    cmd.set("ray_trace_frames", 1)
    cmd.set("ray_shadows", 0)
    cmd.set("depth_cue", 1)
    cmd.bg_color("white")
    cmd.set("antialias", 2)
    
    cmd.orient("traj_movie")
    cmd.zoom("traj_movie", buffer=6.0)
    
    for i in range(1, num_states + 1):
        cmd.frame(i)
        frame_name = f"frame_{i:03d}.png"
        cmd.png(frame_name, width=1024, height=768, dpi=150, ray=1)
        print(f"Saved {frame_name}")
else:
    print("Error: No frames found.")

cmd.quit()
