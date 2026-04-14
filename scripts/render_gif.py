from pymol import cmd
import os
import glob

def render_movie(pdb_file, output_prefix):
    cmd.reinitialize()
    cmd.load(pdb_file, "movie_obj")
    cmd.hide("all")
    cmd.show("cartoon", "movie_obj")
    
    chains = cmd.get_chains("movie_obj")
    if len(chains) >= 2:
        cmd.color("cyan", f"chain {chains[0]}")
        cmd.color("magenta", f"chain {chains[1]}")
    else:
        cmd.color("blue", "movie_obj")
        
    cmd.bg_color("white")
    cmd.set("ray_opaque_background", "on")
    cmd.orient("movie_obj")
    
    cmd.mset("1 -%d" % cmd.count_states("movie_obj"))
    cmd.smooth("movie_obj", window=5)
    
    out_dir = f"frames_{output_prefix}"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    for f in glob.glob(f"{out_dir}/*.png"):
        os.remove(f)
        
    cmd.set("ray_trace_frames", 1) # Headless PyMOL needs ray tracing
    cmd.set("ray_trace_mode", 1)
    
    print(f"Rendering {cmd.count_states('movie_obj')} frames for {pdb_file} into {out_dir}...")
    cmd.mpng(f"{out_dir}/frame_")
    print(f"Done rendering {output_prefix}!")
