import MDAnalysis as mda
from MDAnalysis.analysis import distances
import numpy as np
import pandas as pd
import os

def parse_rmsf(filename):
    rbx1 = []
    binder = []
    current_list = rbx1
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith(('@', '#')):
                continue
            parts = line.split()
            if len(parts) >= 2:
                res = int(parts[0])
                val = float(parts[1])
                if res == 1 and len(rbx1) > 0:
                    current_list = binder
                current_list.append({'Residue': res, 'RMSF': val})
    return pd.DataFrame(rbx1), pd.DataFrame(binder)

def analyze_interface(pdb_file, rmsf_file):
    print(f"Analyzing interface for {pdb_file}...")
    u = mda.Universe(pdb_file)
    
    # Selection based on Atom indices for reliability
    target = u.atoms[:1023]
    binder = u.atoms[1023:1924]
    
    # Distance calculation WITH PBC
    dist_matrix = distances.distance_array(binder.positions, target.positions, box=u.dimensions)
    min_dists = np.min(dist_matrix, axis=1)
    
    # Get binder atoms within 5.0 A of target
    contact_mask = min_dists < 5.0
    interface_atoms = binder[contact_mask]
    
    # Parse RMSF
    rbx1_rmsf, binder_rmsf = parse_rmsf(rmsf_file)

    print("\n--- DESIGN_9 INTERFACE ANALYSIS ---")
    results = []
    for atom in interface_atoms:
        res = atom.residue
        rid = res.resid
        name = res.resname
        # The resid for the binder starts at 1 in the RMSF second set
        if rid <= len(binder_rmsf):
            rmsf_val = binder_rmsf.iloc[rid-1]['RMSF']
            results.append({'Residue': rid, 'Name': name, 'RMSF': rmsf_val})
    
    if not results:
        print("Error: No interface residues detected or mapped.")
        return None

    df = pd.DataFrame(results).drop_duplicates()
    
    # Identify flexible interface residues (RMSF > 0.15 nm)
    hotspots = df[df['RMSF'] > 0.15]
    
    print(f"Total Interface Residues: {len(df)}")
    if not hotspots.empty:
        print("\n--- CRITICAL OPTIMIZATION TARGETS (Flexible Interface) ---")
        print(hotspots[['Residue', 'Name', 'RMSF']].sort_values(by='RMSF', ascending=False))
    else:
        print("All interface residues are relatively stable (< 0.15 nm fluctuation).")
    
    # Save results
    df.to_csv('interface_analysis.csv', index=False)
    print("Success: Analysis saved to 'interface_analysis.csv'")
    return df

if __name__ == "__main__":
    if os.path.exists('design_9_viz.pdb') and os.path.exists('rmsf.xvg'):
        analyze_interface('design_9_viz.pdb', 'rmsf.xvg')
    else:
        print("Error: Missing analysis files.")
