#!/bin/bash
set -e
cd /home/qntmqrks/MD_production
export GMX_MAXCONSTRWARN=-1
# Perform RMSD Analysis (Backbone)
echo "1 1" | /usr/bin/gmx rms -s production.tpr -f production.xtc -o rmsd_design10.xvg -tu ns
# Perform RMSF Analysis (Per-residue)
echo "1" | /usr/bin/gmx rmsf -s production.tpr -f production.xtc -o rmsf_design10.xvg -res
# Perform Radius of Gyration Analysis
echo "1" | /usr/bin/gmx gyrate -s production.tpr -f production.xtc -o gyrate_design10.xvg
# Exit with success
exit 0
