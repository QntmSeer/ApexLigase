import os
import sys
import math

def calculate_distance(c1, c2):
    return math.sqrt(sum((a - b)**2 for a, b in zip(c1, c2)))

def parse_pdb_coords(pdb_path):
    """
    Parses ATOM lines and returns a dictionary mapping (chain, res_num, atom_name) -> coords.
    """
    atoms = []
    with open(pdb_path, 'r') as f:
        for line in f:
            if line.startswith("ATOM"):
                try:
                    chain = line[21].strip()
                    res_num = int(line[22:26].strip())
                    atom_name = line[12:16].strip()
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    atoms.append({
                        'chain': chain,
                        'res_num': res_num,
                        'atom_name': atom_name,
                        'coords': (x, y, z),
                        'line': line
                    })
                except (ValueError, IndexError):
                    continue
    return atoms

def extract_interface(pdb_path, target_chain, binder_chain, distance_cutoff=5.0):
    """
    Finds residues in binder_chain that are within distance_cutoff of any atom in target_chain.
    """
    atoms = parse_pdb_coords(pdb_path)
    target_atoms = [a for a in atoms if a['chain'] == target_chain]
    binder_atoms = [a for a in atoms if a['chain'] == binder_chain]

    if not target_atoms:
        print(f"Error: Target chain {target_chain} not found in {pdb_path}")
        return []
    if not binder_atoms:
        print(f"Error: Binder chain {binder_chain} not found in {pdb_path}")
        return []

    print(f"Checking interface between {target_chain} and {binder_chain} (cutoff={distance_cutoff}A)...")
    
    interface_res_nums = set()
    for b_atom in binder_atoms:
        for t_atom in target_atoms:
            if calculate_distance(b_atom['coords'], t_atom['coords']) <= distance_cutoff:
                interface_res_nums.add(b_atom['res_num'])
                break # Found a contact for this binder atom, move to next

    interface_lines = [a['line'] for a in binder_atoms if a['res_num'] in interface_res_nums]
    print(f"  Found {len(interface_res_nums)} residues in binder interface.")
    return interface_lines

def save_motif(lines, output_path):
    with open(output_path, 'w') as f:
        f.writelines(lines)
        f.write("END\n")
    print(f"  Saved motif to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python motif_extraction.py <pdb_path> <target_chain> <binder_chain> <output_path> [cutoff]")
        sys.exit(1)

    pdb_path = sys.argv[1]
    target_ch = sys.argv[2]
    binder_ch = sys.argv[3]
    out_path = sys.argv[4]
    cutoff = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0

    lines = extract_interface(pdb_path, target_ch, binder_ch, cutoff)
    if lines:
        save_motif(lines, out_path)
    else:
        print("No interface residues found.")
