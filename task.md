# Optimization & Batch Processing Task List

- [x] Analyze `design_9` residue-level stability (RMSF)
- [x] Fix PBC "repelling" artifact in animation (`trjconv -pbc cluster`)
- [x] Identify flexible loops for potential Mutational Scanning
- [x] Process remaining 879 backbones through ProteinMPNN sequence design
- [x] Filter top 10% from new batch for ESMFold validation
- [x] Harden `design_9` with terminal anchors (`PPW` cap and `WW` tail)
- [x] ESMFold/Chai-1 validation of `design_9_hardened` (Regressed: 0.14 vs 0.62)
- [x] ESMFold/Chai-1 validation of expanded Top 10 leads from 879nd batch
- [x] Generate comparative leaderboard vs `design_9` baseline
- [x] Shutdown GCP instances to save costs

### Phase 16: MD Validation of Super-Binder
- [x] Spin up GCP instance `crunchy-peptides-v3`
- [x] Prepare `batch2_design_3` topology and solvate
- [x] Run NVT/NPT equilibration
- [/] Run 100ns Production MD Simulation (Active: 18ns+)
- [/] Analyze RMSD/RMSF for `batch2_design_3` (Partial 17ns verified)
- [x] Compare MD stability against `design_9` baseline (Super-Binder dominance confirmed)

### Phase 17: Project Finalization & Presentation
- [x] Adopt **ApexLigase** project branding and tagline
- [x] Initialize Git repository and push to GitHub (`QntmSeer/ApexLigase`)
- [x] Refactor README and Walkthrough with standard Markdown for full rendering
- [x] Deploy Research-Grade "Premium" Stability Plots (Moving Average filtered)
- [x] Execute surgical cleanup of redundant scripts and temporary data
- [x] Configure selective surgical cloud archiving on GCP
- [/] Complete full 100ns trajectory for `batch2_design_3` (Ongoing)
