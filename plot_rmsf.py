import matplotlib.pyplot as plt
import pandas as pd
import os

def parse_rmsf(filename):
    rbx1_data = [] # Chain A
    binder_data = [] # Chain B
    is_binder = False
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith(('@', '#')):
                continue
            parts = line.split()
            if len(parts) >= 2:
                res = int(parts[0])
                val = float(parts[1])
                if res == 1 and len(rbx1_data) > 0:
                    is_binder = True
                
                if not is_binder:
                    rbx1_data.append([res, val])
                else:
                    binder_data.append([res, val])
    return pd.DataFrame(rbx1_data, columns=['Residue', 'RMSF']), pd.DataFrame(binder_data, columns=['Residue', 'RMSF'])

def plot_rmsf():
    os.makedirs('plots', exist_ok=True)
    rbx1_df, binder_df = parse_rmsf('rmsf.xvg')
    
    plt.figure(figsize=(12, 6))
    plt.plot(rbx1_df['Residue'], rbx1_df['RMSF'], color='#00f2ff', label='RBX1 (Target)', alpha=0.7)
    plt.plot(binder_df['Residue'], binder_df['RMSF'], color='#ff9100', label='Design_9 (Binder)', linewidth=2)
    
    plt.title('Residue-Level Stability: RMSF (Design_9)', fontsize=14, fontweight='bold')
    plt.xlabel('Residue Number', fontsize=12)
    plt.ylabel('RMSF (nm)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    
    # Highlight flexible regions in binder
    flexible_binder = binder_df[binder_df['RMSF'] > 0.15]
    if not flexible_binder.empty:
        plt.fill_between(binder_df['Residue'], 0, binder_df['RMSF'], 
                         where=(binder_df['RMSF'] > 0.15), color='#ff9100', alpha=0.2, label='Flexible Zones')

    plt.savefig('plots/rmsf_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Success: RMSF plot generated in 'plots/rmsf_analysis.png'")

if __name__ == "__main__":
    plot_rmsf()
