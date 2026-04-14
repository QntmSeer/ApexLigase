#!/bin/bash
# ============================================================
# SELF-CONTAINED GROMACS MD PIPELINE WITH AUTO-RESUME
# ============================================================

set -e

# 1. Environment Setup
source /opt/conda/etc/profile.d/conda.sh
conda activate gmx_gpu

INPUT_PDB="design_10_input.pdb"
DEFFNM="md_100ns"

if [ -f "${DEFFNM}.cpt" ]; then
    echo ">>> Checkpoint found! Resuming from ${DEFFNM}.cpt ..."
    # Check if tpr exists too
    if [ -f "${DEFFNM}.tpr" ]; then
        nohup gmx mdrun -v -deffnm "$DEFFNM" -cpi "${DEFFNM}.cpt" -nb gpu -pme gpu > production.log 2>&1 &
        echo "============================================================"
        echo " MD RESUMED IN BACKGROUND "
        echo "============================================================"
        exit 0
    fi
fi

echo ">>> Creating MDP files locally..."
# (Keep MDP content same as before)
cat <<EOF > ions.mdp
integrator  = steep
nsteps      = 1
cutoff-scheme = Verlet
EOF

cat <<EOF > minim.mdp
integrator  = steep
emtol       = 1000.0
emstep      = 0.01
nsteps      = 50000
nstlist     = 1
cutoff-scheme = Verlet
ns_type     = grid
coulombtype = PME
rcoulomb    = 1.0
rvdw        = 1.0
pbc         = xyz
EOF

cat <<EOF > nvt.mdp
integrator              = md
nsteps                  = 50000
dt                      = 0.002
nstlist                 = 10
rlist                   = 1.0
rcoulomb                = 1.0
rvdw                    = 1.0
coulombtype             = PME
tcoupl                  = V-rescale
tc-grps                 = Protein Non-Protein
tau_t                   = 0.1     0.1
ref_t                   = 300     300
pcoupl                  = no
pbc                     = xyz
gen_vel                 = yes
gen_temp                = 300
EOF

cat <<EOF > npt.mdp
integrator              = md
nsteps                  = 50000
dt                      = 0.002
nstlist                 = 10
rcoulomb                = 1.0
rvdw                    = 1.0
coulombtype             = PME
tcoupl                  = V-rescale
tc-grps                 = Protein Non-Protein
tau_t                   = 0.1     0.1
ref_t                   = 300     300
pcoupl                  = Parrinello-Rahman
pcoupltype              = isotropic
tau_p                   = 2.0
ref_p                   = 1.0
compressibility         = 4.5e-5
pbc                     = xyz
EOF

cat <<EOF > md.mdp
integrator              = md
nsteps                  = 50000000
dt                      = 0.002
nstxout-compressed      = 5000
compressed-x-grps       = System
continuation            = yes
constraint_algorithm    = lincs
constraints             = h-bonds
cutoff-scheme           = Verlet
nstlist                 = 10
rcoulomb                = 1.0
rvdw                    = 1.0
coulombtype             = PME
tcoupl                  = V-rescale
tc-grps                 = Protein Non-Protein
tau_t                   = 0.1     0.1
ref_t                   = 300     300
pcoupl                  = Parrinello-Rahman
pcoupltype              = isotropic
tau_p                   = 2.0
ref_p                   = 1.0
compressibility         = 4.5e-5
pbc                     = xyz
EOF

echo ">>> Phase 1-7: Setup and Equilibration"
echo "6 1" | gmx pdb2gmx -f "$INPUT_PDB" -o complex_processed.gro -water tip3p -ignh
gmx editconf -f complex_processed.gro -o complex_newbox.gro -c -d 1.0 -bt dodecahedron
gmx solvate -cp complex_newbox.gro -cs spc216.gro -o complex_solv.gro -p topol.top
gmx grompp -f ions.mdp -c complex_solv.gro -p topol.top -o ions.tpr
echo "SOL" | gmx genion -s ions.tpr -o complex_solv_ions.gro -p topol.top -pname NA -nname CL -neutral -conc 0.15
gmx grompp -f minim.mdp -c complex_solv_ions.gro -p topol.top -o em.tpr
gmx mdrun -v -deffnm em
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr
gmx mdrun -v -deffnm nvt -nb gpu -pme gpu
gmx grompp -f npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p topol.top -o npt.tpr
gmx mdrun -v -deffnm npt -nb gpu -pme gpu

echo ">>> Phase 8: Production"
gmx grompp -f md.mdp -c npt.gro -t npt.cpt -p topol.top -o "${DEFFNM}.tpr"
nohup gmx mdrun -v -deffnm "$DEFFNM" -nb gpu -pme gpu > production.log 2>&1 &

echo "============================================================"
echo " DESIGN_10 100ns MD RUN LAUNCHED IN BACKGROUND "
echo "============================================================"
