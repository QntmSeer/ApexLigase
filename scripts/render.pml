load assets/superbinder_anim.pdb, mol
hide all

# Anchor animation
intra_fit mol and chain A and name CA

# Target Representation: Transparent Surface + Cartoon
show surface, chain A
show cartoon, chain A
color gray80, chain A
set transparency, 0.4

# Binder Representation: Cartoon + Sticks (Atomic detail)
show cartoon, chain B
show sticks, chain B
# Color chain B carbons magenta, rest by atom type
util.cbam chain B

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
    # Ensure background clears each frame
    cmd.png(f"data/frame_{i:03d}.png", ray=0)
python end
quit
