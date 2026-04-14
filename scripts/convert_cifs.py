import glob
import os
from pymol import cmd

# Convert all .cif in data/candidates/ to .pdb
for cif in glob.glob("data/candidates/*.cif"):
    name = os.path.basename(cif).replace(".cif", "")
    out = os.path.join("data/candidates", f"{name}.pdb")
    print(f"Converting {cif} -> {out}")
    cmd.load(cif, "tmp")
    cmd.save(out, "tmp")
    cmd.delete("tmp")
cmd.quit()
