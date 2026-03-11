import sys
import warnings
from Bio.PDB import MMCIFParser, PDBIO

def convert_cif_to_pdb(cif_path, pdb_path):
    print(f"Loading {cif_path}...")
    parser = MMCIFParser(QUIET=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        structure = parser.get_structure('complex', cif_path)
    
    print(f"Saving to {pdb_path}...")
    io = PDBIO()
    io.set_structure(structure)
    io.save(pdb_path)
    print("Conversion complete.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        input_cif = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/folding/design_9/pred.model_idx_0.cif"
        output_pdb = "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/design_9_complex.pdb"
    else:
        input_cif = sys.argv[1]
        output_pdb = sys.argv[2]
        
    convert_cif_to_pdb(input_cif, output_pdb)
