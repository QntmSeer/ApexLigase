# ApexLigase v2 — Next Generation Strategy
## Derived from: GEM x Adaptyv RBX1 Binder Design Competition Full Analysis

**Date**: 2026-04-15  
**Basis**: Complete analysis of all 322 selected submissions  
**Status**: APPROVED FOR NEXT ITERATION

---

## Core Strategy Shifts

### What We Stop Doing
- ❌ Using Chai-1 ipTM as primary filter
- ❌ Generating charge-repeat coiled-coil scaffolds
- ❌ Running RFdiffusion without hotspot conditioning
- ❌ Single-pass design (generate → filter → submit)

### What We Start Doing
- ✅ Boltz2 ipSAE as **primary** computational filter (threshold: ≥0.70)
- ✅ PDB mining with Foldseek/ESMFold to find natural RBX1-complementary folds
- ✅ RFdiffusion with explicit RING domain hotspots: `C53,H57,C74,C77,W79`
- ✅ Iterative refinement: BoltzGen → MPNN → Boltz2 (2–3 cycles)
- ✅ Sequence complexity filter before selection

---

## RBX1 Interface Definition (Critical Knowledge)

**Target site**: RING domain Zn²⁺-binding loop  
**Key residues** (from PDB: 1FBV / 4AP4):  
- Cys53, His57 (Zn1 coordination)  
- Cys74, Cys77 (Zn2 coordination)  
- Trp79 (hydrophobic anchor)  
- Pro49, Leu52, Leu71 (hydrophobic groove)

**Optimal binder geometry**:
- Engages the Zn²⁺ coordinating loop from the exposed face
- Makes contacts with Trp79/Leu71 hydrophobic groove
- Does NOT rely on electrostatic complementarity of full surface

---

## Pipeline v2 Specification

### ARM A: Natural Scaffold Mining (NEW)
```bash
# Foldseek search against PDB for RBX1-binding-like folds
foldseek easy-search rbx1_ring.pdb pdb foldseek_hits.tsv tmp \
  --alignment-type 1 \
  --tmscore-threshold 0.3
# Extract top-100 hits → PDB mining → Caliby refinement
```

### ARM B: Hotspot-Conditioned RFdiffusion (REVISED)
```bash
python run_inference.py \
  --config-name "base_ij" \
  inference.input_pdb="rbx1_binding_site.pdb" \
  inference.num_designs=500 \
  contigmap.contigs=["A53-79/0 60-100"] \
  ppi.hotspot_res=["A53","A57","A74","A77","A79"] \
  inference.output_prefix="arm_b_hotspot_designs"
```

### ARM C: BoltzGen Iterative (NEW)
```python
# Cycle: BoltzGen backbone → ProteinMPNN sequence → Boltz2 score → repeat
for cycle in range(3):
    backbone = boltzgen.sample(target=rbx1_ring, n_samples=200)
    sequences = proteinmpnn.design(backbone, temperature=0.1, n_seq=4)
    scores = boltz2.score(sequences, target=rbx1_ring)  # primary metric: ipSAE
    top_seqs = scores[scores['ipSAE'] > 0.70]
    # Feed back into next cycle
```

---

## Filter Stack (In Order)

1. **Sequence complexity** (reject charge repeats): `max_charge_run < 4`, `charge_frac < 0.45`
2. **Boltz2 ipSAE** ≥ 0.70 (primary gate, replaces Chai-1 ipTM)  
3. **pLDDT** ≥ 80 (structural confidence)
4. **Grounding ipTM** ≥ 0.50 (must match known RBX1 interface geometry)
5. **MD 50ns** (GROMACS, OPLS-AA, TIP3P): RMSD < 0.3 nm, persistent interface H-bonds

---

## Targets for v2

| Metric | v1 (best) | v2 Target |
|---|---|---|
| Boltz2 ipSAE | ~0.63 est. | ≥ 0.80 |
| pLDDT | 88.95 | ≥ 85 |
| Grounding ipTM | 0.76 | ≥ 0.70 |
| Sequence length | 60–100 AA | 80–120 AA |
| Charge repeat fraction | High | < 10% |

---

## Seed for Iteration

**design_9** (`AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRLLESAERRAETRAALIARVLAA`)  
- Grounding ipTM: 0.76 (best in our pool)  
- Chai-1 ipTM: 0.626  
- Length: 60 AA  
- Action: ProteinMPNN diversification (50 variants, T=0.2, fix hydrophobic core positions), evaluate with Boltz2

---

## References

- Full competition analysis: `COMPETITION_ANALYSIS.md`
- Submission data: `submission/FINAL_SUBMISSION_TOP_10_GROUNDED.csv`
- MD results: `results/manifest.json`, `assets/`
- Competition URL: https://proteinbase.com/collections/gem-x-adaptyv-rbx1-binder-design-competition-selected-submissions
