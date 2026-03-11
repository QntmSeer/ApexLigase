import matplotlib.pyplot as plt
import numpy as np

def read_xvg(filename):
    x, y = [], []
    with open(filename, 'r') as f:
        for line in f:
            if not line.startswith(('@', '#')):
                parts = line.split()
                if len(parts) >= 2:
                    x.append(float(parts[0]))
                    y.append(float(parts[1]))
    return np.array(x), np.array(y)

# Plot RMSD
plt.figure(figsize=(10, 6))
time_9, rmsd_9 = read_xvg('rmsd.xvg')
time_sb, rmsd_sb = read_xvg('rmsd_superbinder.xvg')

plt.plot(time_9, rmsd_9, label='Design_9 Baseline', color='blue', alpha=0.7)
plt.plot(time_sb, rmsd_sb, label='batch2_design_3 (Super-Binder)', color='red', linewidth=2)
plt.xlabel('Time (ns)')
plt.ylabel('RMSD (nm)')
plt.title('Backbone RMSD: Baseline vs Super-Binder')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.ylim(0, 0.5)
plt.savefig('C:/Users/Gebruiker/.gemini/antigravity/brain/6d7c4b60-669a-4a05-ab38-a1dead1613d0/rmsd_comparison.png')
plt.close()

# Plot RMSF
plt.figure(figsize=(10, 6))
res_9, rmsf_9 = read_xvg('rmsf.xvg')
res_sb, rmsf_sb = read_xvg('rmsf_superbinder.xvg')

plt.plot(res_9, rmsf_9, label='Design_9 Baseline', color='blue', alpha=0.7)
plt.plot(res_sb, rmsf_sb, label='batch2_design_3 (Super-Binder)', color='red', linewidth=2)
plt.xlabel('Residue Index')
plt.ylabel('RMSF (nm)')
plt.title('Residue Fluctuation: Baseline vs Super-Binder')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig('C:/Users/Gebruiker/.gemini/antigravity/brain/6d7c4b60-669a-4a05-ab38-a1dead1613d0/rmsf_comparison.png')
plt.close()

print("Saved rmsd_comparison.png and rmsf_comparison.png to artifacts!")
