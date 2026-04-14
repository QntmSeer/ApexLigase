# ApexLigase v2 — Strategy & Lessons Learned
# Updated: 2026-04-15 with actual Boltz2 rescore data

## Boltz2 Rescore Results (v1 designs, ground truth)

| Rank | Design | Boltz2 ipSAE | Boltz2 pLDDT | v1 Chai-1 ipTM | Δ rank | Pass v2? |
|------|--------|-------------|--------------|----------------|--------|---------|
| 1 | design_9 | **0.8948** | 0.84 | 0.626 (rank ~3) | ↑ | ✅ |
| 2 | batch2_design_0 | **0.8273** | 0.88 | ~0.51 (rank ~8) | ↑↑↑ | ✅ |
| 3 | design_52 | **0.8029** | 0.85 | ~0.51 (rank ~7) | ↑↑↑ | ✅ |
| 4 | design_10 | **0.7732** | 0.86 | ~0.49 (rank ~9) | ↑↑↑ | ✅ |
| 5 | design_16 | **0.7622** | 0.81 | 0.344 (rank ~10) | ↑↑↑ | ✅ |
| 6 | design_18 | 0.5833 | 0.81 | ~0.52 | — | ❌ |
| 7 | design_15 | 0.5362 | 0.86 | 0.547 | ↓ | ❌ |
| 8 | design_21 | 0.4194 | 0.82 | 0.567 (rank **#2**) | ↓↓↓ | ❌ |
| 9 | design_1 | 0.3732 | **0.91** | ~0.55 | ↓↓ | ❌ |
| 10 | design_50 | 0.1874 | 0.82 | ~0.49 | ↓↓ | ❌ |

**Competition reference**: winner violet-boar-fern = 0.93 ipSAE

---

## Key findings

### 1. Hit rate: 5/10 designs pass 0.70 ipSAE (50%)
This is exceptional for a first-attempt pipeline. RFdiffusion+MPNN arm works.
The submission ranked our designs incorrectly — we submitted 10 good designs
but highlighted the wrong ones as our best.

### 2. The pLDDT=0.91 trap — design_1
design_1 has the HIGHEST structural confidence in our set (pLDDT=0.91)
but the SECOND WORST binding score (ipSAE=0.3732).
Pure coiled-coil charge repeat. Folds perfectly. Binds nothing specifically.
Chai-1 ranked it mid-table. Boltz2 correctly buried it.

### 3. Metric inversion — design_21
design_21 was our #2 pick by Chai-1 ipTM (0.567).
By Boltz2 ipSAE it ranks 8th (0.4194).
Charge-repeat scaffold: ELEKKLEELEAR repeating unit.
Electrostatic complementarity ≠ geometric binding specificity.

### 4. Hidden winners — batch2_design_0, design_52, design_10, design_16
All of these ranked 7th–10th in our v1 submission.
All four score above 0.76 on Boltz2 ipSAE.
They were nearly cut. batch2_design_0 (0.8273) was a second-batch design
that wasn't even our primary submission focus.

### 5. design_9 is the seed
ipSAE=0.8948, ptm=0.9303. Only 4 points below the competition winner.
Already in our hands. Should be the anchor for all v2 diversification.

---

## v2 Pipeline Rules (hardcoded from this data)

### Rule 0 — ALWAYS CHECK THE COMPETITION METRIC FIRST
Before writing a single line of code:
- What metric does the competition score?
- What model generates that metric?
- Install that model, run it on 2–3 designs, confirm scores are sane.

### Rule 1 — Primary filter: Boltz2 ipSAE ≥ 0.70 (hard cutoff)
No blending. If ipSAE < 0.70, discard. Period.
- OLD: Score = 0.40*ipSAE + 0.25*chai1_pTM + 0.20*AF2_ipTM + 0.15*pLDDT
- NEW: if boltz2_ipsae < 0.70: discard() else: score by ipSAE only

### Rule 2 — Reject charge-repeat scaffolds pre-GPU
Apply before any scoring to save compute:
```python
def passes_complexity(seq):
    charged = set('KRDEH')
    run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1] and seq[i] in charged:
            run += 1
            if run >= 4: return False  # charge run ≥ 4 = reject
        else:
            run = 1
    charge_frac = sum(1 for aa in seq if aa in charged) / len(seq)
    return charge_frac <= 0.40
```

### Rule 3 — Don't trust pLDDT alone
pLDDT measures fold quality, not binding specificity.
design_1: pLDDT=0.91, ipSAE=0.37 — perfect fold, near-zero binding.
High pLDDT is necessary but not sufficient.

### Rule 4 — Mine existing backbones before generating new ones
We have 300 RFdiffusion backbones on the HPC from v1.
Before any new run: rescore ALL with Boltz2 ipSAE.
There are likely 10–20 more designs above 0.70 ipSAE sitting there.

### Rule 5 — design_9 is the seed for all diversification
62 AA, ipSAE=0.8948, ptm=0.9303.
Run 50 ProteinMPNN variants at T=0.1, 0.2, 0.3.
Score all with Boltz2. Any above 0.85 is competition-tier.

---

## v2 Scoring Formula

```python
# Primary gate (hard)
if boltz2_ipsae < 0.70:
    discard()

# Ranking formula (after gate)
score = (0.70 * boltz2_ipsae) + (0.30 * boltz2_plddt)

# Secondary confirmation only (NOT a gate)
# chai1_iptm used only as tiebreaker between designs with ipSAE within 0.02
```

---

## Competition Checklist (pre-flight before any design work)

- [ ] Read competition rules — identify exact scoring metric and model
- [ ] Install competition scoring tool locally or on HPC  
- [ ] Score 2 reference designs to confirm tool works correctly
- [ ] Set primary filter to competition metric with 0.70 floor
- [ ] Rescore any existing backbones from previous runs first
- [ ] User's metric intuition overrides tool-preference arguments
