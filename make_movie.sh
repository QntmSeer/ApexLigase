#!/bin/bash
cd /home/qntmqrks/rbx1_design/Phase14_Optimization/traj
# Generate the PML script
echo "from pymol import cmd" > render_auto.pml
for f in $(ls traj_*.pdb | sort); do
    echo "cmd.load('$f', 'traj_movie')" >> render_auto.pml
done
cat << 'PML_EOF' >> render_auto.pml
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
cmd.set("fog", 1)
cmd.bg_color("white")
cmd.set("antialias", 2)
cmd.orient("traj_movie")
cmd.zoom("traj_movie", buffer=6.0)
num_states = cmd.count_states("traj_movie")
for i in range(1, num_states + 1):
    cmd.frame(i)
    cmd.png(f"frame_{i:03d}.png", width=1024, height=768, dpi=150, ray=1)
cmd.quit()
PML_EOF
xvfb-run -a /opt/conda/envs/rosetta_env/bin/pymol -qc render_auto.pml
convert -delay 15 -loop 0 frame_*.png relax_trajectory_3d.gif
