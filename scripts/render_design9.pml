load assets/design_9_anim.pdb, mol
hide all

# Anchor animation to target C-alpha
intra_fit mol and chain A and name CA

# Target aesthetics
show surface, chain A
show cartoon, chain A
color gray80, chain A
set transparency, 0.4

# Design_9 Binder aesthetics
show cartoon, chain B
show sticks, chain B
util.cbam chain B

# Potential third chain (if multimeric)
show cartoon, chain C
show sticks, chain C
util.cbac chain C

bg_color white
set ray_opaque_background, 1
set depth_cue, 1

orient mol
zoom mol, 1.2

set ray_trace_frames, 0
mset 1 - 101
viewport 800, 600

python
for i in range(1, 102):
    cmd.frame(i)
    cmd.png(f"data/frame_d9_{i:03d}.png", ray=0)
python end
quit
