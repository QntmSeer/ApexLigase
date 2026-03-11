from Bio.PDB import MMCIFParser, PDBIO

parser = MMCIFParser()
structure = parser.get_structure("b2d3", "/home/qntmqrks/rbx1_design/Phase15_MassGeneration/Phase23_Validation/batch2_design_3/pred.model_idx_0.cif")
io = PDBIO()
io.set_structure(structure)
io.save("/home/qntmqrks/rbx1_design/Phase16_SuperBinderMD/batch2_design_3.pdb")
print("Converted CIF to PDB")
