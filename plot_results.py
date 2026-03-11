import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def parse_xvg(filename):
    data = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith(('@', '#')):
                continue
            parts = line.split()
            if len(parts) >= 2:
                data.append([float(parts[0]), float(parts[1])])
    return pd.DataFrame(data, columns=['Time', 'Value'])

def plot_stability():
    os.makedirs('plots', exist_ok=True)
    
    rmsd_df = parse_xvg('rmsd.xvg')
    plt.figure(figsize=(10, 6))
    plt.plot(rmsd_df['Time'], rmsd_df['Value'], color='#1f77b4', linewidth=1.5, alpha=0.8)
    plt.title('Structural Stability: Backbone RMSD (Design_9)', fontsize=14, fontweight='bold')
    plt.xlabel('Time (ns)', fontsize=12)
    plt.ylabel('RMSD (nm)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.ylim(0, max(rmsd_df['Value']) * 1.2)
    plt.savefig('plots/rmsd_stability.png', dpi=300, bbox_inches='tight')
    plt.close()

    rg_df = parse_xvg('gyrate.xvg')
    plt.figure(figsize=(10, 6))
    plt.plot(rg_df['Time'], rg_df['Value'], color='#d62728', linewidth=1.5, alpha=0.8)
    plt.title('Protein Compactness: Radius of Gyration (Design_9)', fontsize=14, fontweight='bold')
    plt.xlabel('Time (ns)', fontsize=12)
    plt.ylabel('Rg (nm)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig('plots/rg_compactness.png', dpi=300, bbox_inches='tight')
    plt.close()

    hb_df = parse_xvg('hbonds.xvg')
    plt.figure(figsize=(10, 6))
    plt.plot(hb_df['Time'], hb_df['Value'], color='#2ca02c', linewidth=1.5, alpha=0.8)
    plt.title('Interface Persistence: Hydrogen Bonds (Design_9)', fontsize=14, fontweight='bold')
    plt.xlabel('Time (ns)', fontsize=12)
    plt.ylabel('Number of HBonds', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig('plots/hbonds_interface.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Success: Stability plots generated in the 'plots/' directory.")

if __name__ == "__main__":
    plot_stability()
