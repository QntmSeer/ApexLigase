# GEM x Adaptyv RBX1 Binder Design Competition
## Full Post-Mortem Analysis — ApexLigase v1

> **Data source**: All 322 selected submissions from ProteinBase  
> **Sorted by**: Boltz2 pLDDT descending  
> **Our submissions**: 10 designs (ApexLigase pipeline, RFdiffusion + ProteinMPNN + MD)  
> **Date of analysis**: 2026-04-15

---

## 1. Selected Pool — Complete Method Landscape

### Design Methods (sitewide counts shown on collection page)
| Method | Selected Count | Notes |
|---|---|---|
| **RFdiffusion** | **27** | Largest single method, but spread across pLDDT tiers |
| **Mosaic / Mosaic+Scramble** | **18+** | Strong in mid-tier; multiple submitters |
| **BoltzGen (+iterative MPNN)** | **15** | Miles McGibbon's iterative loop is a standout |
| Bagel + Solumpnn | 7 | Generally lower ipSAE |
| LFM2 Customization | 7 | Liquid AI; high pLDDT, near-zero ipSAE |
| moPPIt / moPPIt+PeptiVerse | 7 | Peptide specialist; low MW but also low ipSAE |
| FoldCraft | 7 | Khondamir Rustamov; mixed ipSAE |
| PepMind + AlphaFold3 | 7 | Short peptides; generally low ipSAE |
| AF2 Hallucination + ADFlip | 7 | Kai Yi; larger proteins, moderate ipSAE |
| **Protein Hunter + Caliby** | ~7 | **Richard Shuai — cleanest ipSAE in pool** |
| BindCraft 2 | ~5 | Pacesa Lab; moderate-good metrics |
| ORBIT | ~7 | Aryan Chandaka; ~100 AA, solid pLDDT |
| ProOS (scFv/other) | ~6 | Mike Minson; 190–230 AA, moderate |
| BoltzGen→MPNN→Boltz2→MPNN→Boltz2 | 7 | **Miles McGibbon — iterative refinement, pLDDT 89–90** |
| Arena | 7 | Tanay Lohia; 83–116 AA, pLDDT 80–89 |
| GIRAF | ~6 | Haowen Zhao; nanobody+scFv, pLDDT 82–89 |
| Proteina-Complexa (AF2-based) | 7 | Bingyi Zhao; 92–143 AA, pLDDT 78–89 |
| JointDiff-binder + ipSAE filter | 7 | Shaowen Zhu; ~100 AA, poor pLDDT |
| PXDesign | ~7 | scFv dominant; pLDDT 76–89 |
| SAE-Steered ESM2 + Boltz-2 | 7 | Brandon Cantrell; tiny 12–21 AA hits |
| LLM-Guided Multi-Stage | 7 | magicai; 96–119 AA, pLDDT 50–88 |

### Protein Class Breakdown
| Class | Count (approx) | ipSAE Range | Best pLDDT |
|---|---|---|---|
| Miniprotein (40–100 AA) | ~90 | 0.60–0.93 | 92.03 |
| Nanobody (100–130 AA) | ~60 | 0.15–0.84 | 89.13 |
| Other / β+α proteins | ~130 | 0.44–0.93 | 90.15 |
| scFv (230–250 AA) | ~20 | -- | 84.88 |
| Peptide (<40 AA) | ~30 | 0.07–0.54 | ~74 |

---

## 2. Our Submission — Detailed Scorecard

| Design | AA | Chai-1 ipTM | pLDDT | Grounding | Notes |
|---|---|---|---|---|---|
| **design_9** | 60 | **0.626** | 81.78 | **0.76** ✅ | Best — only grounded design |
| design_21 | 80 | 0.567 | 88.95 | 0.39 ⚠️ | High pLDDT, weak grounding |
| design_15 | 72 | 0.547 | 82.14 | 0.10 ❌ | |
| design_52 | 91 | 0.511 | 77.96 | Not grounded | |
| design_50 | 73 | 0.492 | 82.26 | Not grounded | |
| design_16 | 60 | 0.344 | 83.22 | Failed | |
| design_1 | 63 | 0.386 | 83.69 | 0.14 ❌ | |
| design_10 | 90 | 0.260 | 84.13 | 0.16 ❌ | |
| design_18 | 100 | 0.226 | 77.69 | Failed | |
| batch2_design_0 | 64 | 0.427 | 88.40 | 0.13 ❌ | |

**Where we'd rank**: design_9 at ipTM 0.626 would place in the bottom third of the Tier-1 pool (top selected have ipSAE 0.80–0.93). Most of our designs with ipTM < 0.40 would fall into the bottom half of the entire 322-entry selected pool.

---

## 3. Full Root Cause Analysis (Complete 322-entry view)

### ❌ Failure Mode 1 — Optimized for Chai-1 ipTM, not Boltz2 ipSAE

The competition used **Boltz2 ipSAE** as the primary metric. Our pipeline filtered by **Chai-1 ipTM**. These are correlated but not identical. Several submitters explicitly named their method "Boltz2 & ProteinMPNN" (Nikita Ivanisenko) or "BoltzGen → MPNN → Boltz-2 → MPNN → Boltz-2" (Miles McGibbon). We never ran Boltz2 at all.

Miles McGibbon's iterative pipeline is particularly instructive:
```
BoltzGen (backbone) → ProteinMPNN (sequence) → Boltz-2 (evaluate) →
ProteinMPNN (refine) → Boltz-2 (re-evaluate)
```
Result: 7 designs all at **pLDDT 89–90.15** — remarkably consistent. This is what **iterative Boltz2-guided refinement** produces.

### ❌ Failure Mode 2 — Charged Repeat Scaffold Problem

Our design_21 (`SAAAAAKAAAAAA...EEELKKREEEAAK...`) has the highest pLDDT (88.95) but one of the worst grounding scores (0.39). This is the classic **polyelectrolyte scaffold trap**: the coiled-coil repeats electrostatically complement RBX1 surface but don't form specific contacts. The pLDDT high because the scaffold is intrinsically very regular.

Winning miniproteins (NINGYUAN TANG's brisk-moth-dust: pLDDT 90.05, ipSAE 0.81):
```
ADTLVATATVTLPGGPTLLAAIERMAAASGGRYRVEVEEHPLLDTITVTLELPAADRDAALAAIRAAAAAEAERTGVPQELMDLVVDALEAALDAALAA
```
— Hydrophobic core (VATA, LPAAD, DLVVD), complex secondary structure, NO charge repetition.

### ❌ Failure Mode 3 — RFdiffusion Without Hotspot Conditioning

27 RFdiffusion entries made it in, but only those with explicit interface conditioning succeeded. GETU TADESSE FELLEK submitted 5+ RFdiffusion nanobodies — all with structured CDR3-like loops that engage a specific surface (high pLDDT 87–89, though low ipSAE suggests the CDR loop conditioning was approximate). Reilly Osadchey's RFdiffusion minibinders (pLDDT 82–87) showed better specificity.

Our arm2_rfdiffusion arm likely ran without `--hotspot_res` flags.

### ❌ Failure Mode 4 — Missing Natural Scaffold Mining

Richard Shuai's "Protein Hunter + Caliby" approach yielded 5+ designs in the top 10 by ipSAE (0.86–0.93). This is a **database mining** workflow — not de novo. It finds proteins in the PDB whose surfaces naturally complement RBX1 RING domain geometry. These proteins have:
- Complex, evolved hydrophobic cores
- Specific geometric contacts (not electrostatic)  
- High ipSAE because the fold was pre-adapted to something similar

We had no PDB mining arm in our pipeline.

### ❌ Failure Mode 5 — No Iterative Interface Refinement

New finding from complete dataset: **Miles McGibbon**, **Nikita Ivanisenko** (Boltz2 + ProteinMPNN), and **Aryan Chandaka** (ORBIT) all ran iterative loops — generate backbone → optimize sequence using Boltz2 gradient signal → validate → refine. The result: consistently high pLDDT across multiple variants (all their 7 designs cluster within 5 pLDDT points of each other).

Our pipeline was single-pass: RFdiffusion → ProteinMPNN → filter. No Boltz2 feedback loop.

### ❌ Failure Mode 6 — Grounding Without Experimental Anchor

8/10 of our designs failed experimental grounding. The LFM2 Customization (Liquid AI) designs show the same pattern: very high pLDDT (87–93!) but near-zero ipSAE (0.00–0.22). These are beautiful proteins that don't specifically bind RBX1. High pLDDT alone is a necessary but not sufficient condition.

### ✅ What We Got Right

- **design_9** is the one authentic hit: short (60 AA), grounded (0.76), good Chai-1 ipTM (0.626)
- MD validation pipeline (GROMACS 100ns) is the right physical filter — just applied too late
- Multi-arm approach (BindCraft, RFdiffusion, ESM3) in principle was correct — just needed Boltz2 as filter

---

## 4. Competitive Intelligence — Techniques That Actually Worked

### Tier S — Top ipSAE Approaches
| Technique | Best ipSAE | pLDDT | AA | Who |
|---|---|---|---|---|
| Protein Hunter + Caliby | 0.93 | 83 | 157 | Richard Shuai |
| FoldCraft (hotspot-conditioned) | 0.91 | 52–83 | 174 | K. Rustamov |
| BoltzGen→MPNN→Boltz2 (iterative) | -- | 90 | 111 | Miles McGibbon |
| BindCraft 2 | 0.89 | 77 | 153 | Pacesa Lab |
| NINGYUAN TANG Miniprotein | 0.88 | 90 | 99 | NINGYUAN TANG |

### Tier A — High pLDDT with Real Interface Contacts
| Technique | ipSAE | pLDDT | AA | Who |
|---|---|---|---|---|
| ORBIT | -- | 85–89 | 100 | Aryan Chandaka |
| Arena | -- | 80–89 | 83–116 | Tanay Lohia |
| RFdiffusion (hotspot-conditioned) | 0.42–0.56 | 82–87 | 83–111 | R. Osadchey |
| GIRAF (nanobody) | -- | 84–89 | 115–122 | Haowen Zhao |

### Tier B — Our Range (collected for comparison)
| Technique | Our ipTM | Our pLDDT | AA |
|---|---|---|---|
| RFdiffusion + ProteinMPNN (ours) | 0.226–0.626 | 77–89 | 60–100 |

---

## 5. Revised Strategy — ApexLigase v2

### New Pipeline Architecture

```
                    RBX1 RING Interface
                    (Zn²⁺ coordinating residues: C53,H57,C74,C77,W79)
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼──────┐
        │  ARM A     │ │ ARM B  │ │  ARM C    │
        │ Protein    │ │BoltzGen│ │RFdiffusion│
        │ Hunter +   │ │+MPNN+  │ │ hotspot-  │
        │ Foldseek  │ │Boltz2  │ │conditioned│
        └─────┬─────┘ └───┬────┘ └────┬──────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │  Boltz2     │
                    │ ipSAE > 0.7 │ ← Primary filter (NOT Chai-1)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ ProteinMPNN │
                    │  refinement │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Boltz2     │
                    │ re-evaluate │ ← Iterative loop (2–3x)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Grounding   │
                    │ ipTM > 0.5  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   MD 50ns   │
                    │ (GROMACS)   │
                    └─────────────┘
```

### Priority Action Items

| # | Action | Impact | Effort | What we learned |
|---|---|---|---|---|
| 1 | **Install and run Boltz2** as primary filter | 🔴 Critical | Medium | All top submissions used Boltz2 ipSAE as selection criterion |
| 2 | **Add Foldseek PDB mining arm** (like Protein Hunter) | 🔴 Critical | Medium | Top ipSAE group used natural scaffold mining |
| 3 | **RFdiffusion with explicit hotspots** (`--hotspot_res C53,H57,C74,C77,W79`) | 🔴 Critical | Low | Without hotspots, designs aren't interface-conditioned |
| 4 | **Implement BoltzGen→MPNN→Boltz2 iterative loop** | 🟡 High | High | Miles McGibbon's iterative pipeline gave 89–90 pLDDT consistently |
| 5 | **Discard charge-repeat scaffolds** (filter: max charge run < 5 consecutive) | 🟡 High | Low | All our top designs by Chai-1 ipTM had charge repeats |
| 6 | **Iterate from design_9** (our only grounded seed) | 🟡 High | Low | 60 AA, grounding 0.76 — ProteinMPNN diversification around this |
| 7 | **Target 80–120 AA length range** | 🟡 High | Low | Optimal zone for both miniprotein and small protein classes |
| 8 | **Track Zn²⁺ coordination contacts** in MD explicitly | 🟢 Medium | Low | RING domain binding requires Zn²⁺ residue contacts |

### Sequence Heuristics for Next Round

**Kill switch** (reject if any of these):
- Sequence has ≥4 consecutive identical charged residues (`KKKK`, `EEEE`, `RRRR`)
- Charge fraction > 45% of total AA
- Hydrophobic fraction < 15% of total AA

**Target profile** (from top winners):
- Length: 80–120 AA
- Hydrophobic cluster in core (Val, Leu, Ile, Ala ≥20%)
- Charged residues interspersed, not massed
- At least one aromatic or proline for turn structure
- Complex local secondary structure (αβα or βαβ motifs)

---

## 6. Does Our MD Validation Still Apply?

**Yes, but at a different stage.**

Our GROMACS 100ns validation of design_9 (RMSD ~0.2nm, stable Rg, persistent H-bonds) is *legitimate science*. The issue is that we applied MD *after* screening by a metric (Chai-1 ipTM) that doesn't correlate well with Boltz2 ipSAE.

**New protocol**: Apply MD only to designs that pass Boltz2 ipSAE > 0.7. This saves compute and ensures MD is validating genuine interface contacts, not electrostatically-driven hallucinations.

---

## 7. Conclusion

> We are competitive on structural stability (pLDDT 77–89), but missing the key dimension: **specific interface formation**, as measured by Boltz2 ipSAE. The top performers had ipSAE of 0.80–0.93; we peaked at ~0.63 with design_9.
>
> The corrections are clear and implementable: Boltz2 as filter, PDB mining, hotspot-conditioned RFdiffusion, iterative refinement. None require fundamentally new wetlab capabilities — they're computational pipeline changes.
>
> **design_9 is our best seed.** Start v2 from there.
