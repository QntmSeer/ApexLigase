import sys

def get_seq_from_pdb(pdb_file):
    three_to_one = {
        'ALA':'A', 'CYS':'C', 'ASP':'D', 'GLU':'E', 'PHE':'F',
        'GLY':'G', 'HIS':'H', 'ILE':'I', 'LYS':'K', 'LEU':'L',
        'MET':'M', 'ASN':'N', 'PRO':'P', 'GLN':'Q', 'ARG':'R',
        'SER':'S', 'THR':'T', 'VAL':'V', 'TRP':'W', 'TYR':'Y'
    }
    
    current_chain = None
    sequences = {}
    
    try:
        with open(pdb_file, 'r') as f:
            for line in f:
                if line.startswith('ATOM') and line[12:16].strip() == 'CA':
                    res_name = line[17:20].strip()
                    chain_id = line[21:22].strip()
                    res_one = three_to_one.get(res_name, 'X')
                    
                    if chain_id not in sequences:
                        sequences[chain_id] = []
                    sequences[chain_id].append(res_one)
                    
        return {cid: "".join(seq) for cid, seq in sequences.items()}
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"File: {arg}")
        seqs = get_seq_from_pdb(arg)
        for cid, seq in seqs.items():
            print(f"  Chain {cid}: {seq}")
