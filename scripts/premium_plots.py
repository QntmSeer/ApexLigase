import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import os

# Set a professional style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("colorblind")

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

def moving_average(y, window=20):
    return np.convolve(y, np.ones(window)/window, mode='same')

def plot_premium_rg():
    print("Generating premium Radius of Gyration plot...")
    rg_df = parse_xvg('gyrate.xvg' if os.path.exists('gyrate.xvg') else 'assets/gyrate.xvg')
    
    plt.figure(figsize=(10, 6))
    plt.plot(rg_df['Time'], rg_df['Value'], color='#d62728', alpha=0.3, label='Raw Data')
    plt.plot(rg_df['Time'], moving_average(rg_df['Value'], window=50), color='#b2182b', linewidth=2.5, label='Moving Average (1ns)')
    
    plt.title('Protein Compactness over 100ns (Design_9)', fontsize=15, fontweight='bold', pad=20)
    plt.xlabel('Time (ns)', fontsize=12)
    plt.ylabel('Radius of Gyration (nm)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig('assets/rg_compactness_premium.png', dpi=300)
    plt.close()

def plot_premium_rmsd_comparison():
    print("Generating premium RMSD Comparison plot...")
    
    def try_open(f):
        if os.path.exists(f): return f
        if os.path.exists(f'assets/{f}'): return f'assets/{f}'
        return None

    f9 = try_open('rmsd.xvg')
    fsb = try_open('rmsd_superbinder.xvg')
    
    if not f9 or not fsb:
        print(f"Skipping comparison: {f9}, {fsb}")
        return

    time_9, rmsd_9 = [], []
    with open(f9, 'r') as f:
        for line in f:
            if not line.startswith(('@', '#')):
                p = line.split()
                if len(p) >= 2:
                    time_9.append(float(p[0]))
                    rmsd_9.append(float(p[1]))
    
    time_sb, rmsd_sb = [], []
    with open(fsb, 'r') as f:
        for line in f:
            if not line.startswith(('@', '#')):
                p = line.split()
                if len(p) >= 2:
                    time_sb.append(float(p[0]))
                    rmsd_sb.append(float(p[1]))

    plt.figure(figsize=(10, 6))
    
    # Design 9 - Baseline
    plt.plot(time_9, rmsd_9, color='#3182bd', alpha=0.2)
    plt.plot(time_9, moving_average(rmsd_9, window=50), color='#1f77b4', linewidth=2, label='Design_9 (Baseline)')
    
    # Super Binder - Candidate
    plt.plot(time_sb, rmsd_sb, color='#de2d26', alpha=0.2)
    plt.plot(time_sb, moving_average(rmsd_sb, window=50), color='#b2182b', linewidth=3, label='batch2_design_3 (Super-Binder)')
    
    plt.title('Interface Stability: Baseline vs Super-Binder', fontsize=15, fontweight='bold', pad=20)
    plt.xlabel('Time (ns)', fontsize=12)
    plt.ylabel('Backbone RMSD (nm)', fontsize=12)
    plt.ylim(0, 0.45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, loc='upper left')
    plt.tight_layout()
    plt.savefig('assets/rmsd_comparison_premium.png', dpi=300)
    plt.close()

def plot_premium_rmsf_comparison():
    print("Generating premium RMSF Comparison plot...")
    
    def try_open(f):
        if os.path.exists(f): return f
        if os.path.exists(f'assets/{f}'): return f'assets/{f}'
        return None

    f9 = try_open('rmsf.xvg')
    fsb = try_open('rmsf_superbinder.xvg')
    
    if not f9 or not fsb:
        print(f"Skipping RMSF comparison: {f9}, {fsb}")
        return

    res_9, rmsf_9 = [], []
    with open(f9, 'r') as f:
        for line in f:
            if not line.startswith(('@', '#')):
                p = line.split()
                if len(p) >= 2:
                    res_9.append(float(p[0]))
                    rmsf_9.append(float(p[1]))
    
    res_sb, rmsf_sb = [], []
    with open(fsb, 'r') as f:
        for line in f:
            if not line.startswith(('@', '#')):
                p = line.split()
                if len(p) >= 2:
                    res_sb.append(float(p[0]))
                    rmsf_sb.append(float(p[1]))

    plt.figure(figsize=(10, 6))
    
    plt.plot(res_9, rmsf_9, color='#1f77b4', linewidth=2, label='Design_9 (Baseline)', alpha=0.8)
    plt.plot(res_sb, rmsf_sb, color='#b2182b', linewidth=2.5, label='batch2_design_3 (Super-Binder)', alpha=0.9)
    
    plt.title('Residue Fluctuation (RMSF): Baseline vs Super-Binder', fontsize=15, fontweight='bold', pad=20)
    plt.xlabel('Residue Number', fontsize=12)
    plt.ylabel('RMSF (nm)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig('assets/rmsf_comparison_premium.png', dpi=300)
    plt.close()

if __name__ == "__main__":
    if not os.path.exists('assets'):
        os.makedirs('assets')
    plot_premium_rg()
    plot_premium_rmsd_comparison()
    plot_premium_rmsf_comparison()
    print("Done!")
