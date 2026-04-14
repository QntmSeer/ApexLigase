"""
CABS-flex per-residue RMSF comparison: Design_9 vs Super-Binder.
Correctly reads plots/RMSF.csv with matched axes between panels.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ARTIFACTS = "/mnt/c/Users/Gebruiker/.gemini/antigravity/brain/6d7c4b60-669a-4a05-ab38-a1dead1613d0"

def load_rmsf_csv(path):
    labels, vals = [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                labels.append(parts[0])
                vals.append(float(parts[1]))
    return np.array(labels), np.array(vals)

def split_chains(labels, vals):
    a_idx = [i for i, l in enumerate(labels) if l.startswith('A')]
    b_idx = [i for i, l in enumerate(labels) if l.startswith('B')]
    return (labels[a_idx], vals[a_idx]), (labels[b_idx], vals[b_idx])

d9_labels, d9_rmsf = load_rmsf_csv("data/cabs_output_d9/plots/RMSF.csv")
sb_labels, sb_rmsf = load_rmsf_csv("data/cabs_output_superbinder/plots/RMSF.csv")

d9_a, d9_b = split_chains(d9_labels, d9_rmsf)
sb_a, sb_b = split_chains(sb_labels, sb_rmsf)

# Compute shared axis limits
max_rmsf = max(
    d9_a[1].max(), d9_b[1].max(),
    sb_a[1].max(), sb_b[1].max()
) * 1.1

max_res_target = max(len(d9_a[1]), len(sb_a[1]))
max_res_binder = max(len(d9_b[1]), len(sb_b[1]))

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(15, 5), facecolor="#0d1117")
fig.suptitle("CABS-flex Per-Residue RMSF: Design_9 vs Super-Binder",
             color="white", fontsize=13, y=1.02)

panels = [
    (axes[0], (d9_a[0], d9_a[1]), (sb_a[0], sb_a[1]),
     "Chain A — RBX1 Target (shared)", max_res_target),
    (axes[1], (d9_b[0], d9_b[1]), (sb_b[0], sb_b[1]),
     "Chain B — Binder", max_res_binder),
]

for ax, (d9_lbl, d9_v), (sb_lbl, sb_v), title, max_x in panels:
    ax.set_facecolor("#0d1117")

    x_d9 = np.arange(1, len(d9_v) + 1)
    x_sb = np.arange(1, len(sb_v) + 1)

    ax.plot(x_d9, d9_v, color="#9b59b6", lw=1.8, alpha=0.9,
            label=f"Design_9 ({len(d9_v)} res)")
    ax.fill_between(x_d9, d9_v, alpha=0.15, color="#9b59b6")

    ax.plot(x_sb, sb_v, color="#00e5ff", lw=1.8, alpha=0.9,
            label=f"Super-Binder ({len(sb_v)} res)")
    ax.fill_between(x_sb, sb_v, alpha=0.15, color="#00e5ff")

    # Enforce matched axes
    ax.set_xlim(0, max_x + 1)
    ax.set_ylim(0, max_rmsf)

    ax.set_title(title, color="#cccccc", fontsize=11, pad=8)
    ax.set_xlabel("Residue index", color="#aaaaaa", fontsize=10)
    ax.set_ylabel("RMSF (Å)", color="#aaaaaa", fontsize=10)

    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")
    ax.tick_params(colors="#aaaaaa")
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(True, which='major', color='#1e2530', lw=0.6)
    ax.grid(True, which='minor', color='#161c24', lw=0.3)
    ax.legend(facecolor="#1a1f2e", edgecolor="#333333", labelcolor="white", fontsize=9)

plt.tight_layout()
out = f"{ARTIFACTS}/cabs_flex_comparison.png"
plt.savefig(out, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved → {out}")
print(f"D9 chain B: {len(d9_b[1])} residues | Super-Binder chain B: {len(sb_b[1])} residues")
print(f"Max RMSF D9: {d9_b[1].max():.2f} Å | Max RMSF SB: {sb_b[1].max():.2f} Å")
