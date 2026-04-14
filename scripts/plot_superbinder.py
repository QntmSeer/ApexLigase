import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import os

plt.style.use('seaborn-v0_8-whitegrid')

def parse_xvg(filename):
    data = []
    if not os.path.exists(filename):
        return pd.DataFrame(columns=['Time', 'Value'])
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith(('@', '#')):
                continue
            parts = line.split()
            if len(parts) >= 2:
                data.append([float(parts[0]), float(parts[1])])
    return pd.DataFrame(data, columns=['Time', 'Value'])

def moving_average(y, window=50):
    if len(y) == 0: return y
    return np.convolve(y, np.ones(window)/window, mode='same')

# Load superbinder data
dir_sb = 'data/superbinder/'
dir_base = 'data/'
rmsd_sb = parse_xvg(os.path.join(dir_sb, 'rmsd_superbinder_final.xvg'))
rg_sb = parse_xvg(os.path.join(dir_sb, 'rg_superbinder_final.xvg'))
hb_sb = parse_xvg(os.path.join(dir_sb, 'hbnum_superbinder_final.xvg'))

rmsd_base = parse_xvg(os.path.join(dir_base, 'rmsd_baseline.xvg'))

if not os.path.exists('assets'):
    os.makedirs('assets')

# Plot RMSD 
plt.figure(figsize=(10, 6))
if not rmsd_base.empty:
    t_base_rmsd = rmsd_base['Time'] / 1000 if rmsd_base['Time'].max() > 1000 else rmsd_base['Time']
    plt.plot(t_base_rmsd, rmsd_base['Value'], color='#3182bd', alpha=0.2)
    plt.plot(t_base_rmsd, moving_average(rmsd_base['Value']), color='#1f77b4', linewidth=2, label='Baseline (Design_9)')

if not rmsd_sb.empty:
    t_sb_rmsd = rmsd_sb['Time'] / 1000 if rmsd_sb['Time'].max() > 1000 else rmsd_sb['Time']
    plt.plot(t_sb_rmsd, rmsd_sb['Value'], color='#de2d26', alpha=0.2)
    plt.plot(t_sb_rmsd, moving_average(rmsd_sb['Value']), color='#b2182b', linewidth=3, label='Super-Binder (batch2_design_3)')

plt.title('Interface Stability: Super-Binder vs Baseline', fontsize=15, fontweight='bold')
plt.xlabel('Time (ns)')
plt.ylabel('Backbone RMSD (nm)')
plt.legend()
plt.tight_layout()
plt.savefig('assets/superbinder_rmsd_final.png', dpi=300)
plt.close()

# Plot H-Bonds (Interface Persistence)
plt.figure(figsize=(10, 6))
if not hb_sb.empty:
    t_sb_hb = hb_sb['Time'] / 1000 if hb_sb['Time'].max() > 1000 else hb_sb['Time']
    plt.plot(t_sb_hb, hb_sb['Value'], color='#31a354', alpha=0.3)
    plt.plot(t_sb_hb, moving_average(hb_sb['Value']), color='#006d2c', linewidth=3, label='Super-Binder H-Bonds')
plt.axhline(y=5, color='#1f77b4', linestyle='--', linewidth=2, label='Baseline Average (~5 H-Bonds)')
plt.title('Interface Persistence: Hydrogen Bond Network', fontsize=15, fontweight='bold')
plt.xlabel('Time (ns)')
plt.ylabel('Number of Hydrogen Bonds')
plt.legend()
plt.tight_layout()
plt.savefig('assets/superbinder_hbonds_final.png', dpi=300)
plt.close()

print("Final plots generated in assets/")
