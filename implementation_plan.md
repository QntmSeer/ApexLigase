## Phase 23 - Affinity Maturation & High-Resolution Validation

Dual-track processing of optimized `design_9` and the highest-potential new leads.

### [Design_9 Hardening]
- **Sequence Engineering**: Apply `P1P2W3` N-terminal cap and `W59W60` C-terminal hydrophobic anchor to `design_9`.
- **Folding Check**: Run ESMFold on the hardened sequence to ensure the core helical bundle is maintained.

### [Competitive Ranking]
- **Target Selection**: Pick top 5 candidates from the 879nd batch (Score < 1.9).
- **ESMFold Validation**: Predict 3D structures and verify pLDDT > 80 and RMSD < 2.0Å to original backbones.
- **Leaderboard Alpha**: Identify the first "Super-Binder" candidate that outperforms Design_9 in both sequence energy and folding confidence.

## Phase 24 - ApexLigase Finalization & Presentation
Consolidating high-fidelity results and hardening the public-facing repository.

### [Branding & UX]
- **Documentation**: Standardize all visual assets (GIFs/Plots) for GitHub rendering.
- **Visuals**: Deploy moving-average-stabilized stability plots for professional presentation.

### [Data Stewardship]
- **Repo Cleanup**: Remove legacy/redundant scripts and CSV iterations.
- **Cloud Archiving**: Implement selective sync to GS bucket for final validation data.

## Verification Plan

### Automated Tests
- `esmfold_bench.sh`: Launch a batch job on the GCP L4 GPU to fold the 6 target sequences.
- `compare_leads.py`: Script to parse pLDDT and generate a comparative leaderboard.
- `premium_plots.py`: Generate research-grade stability visuals.
- `gsutil rsync`: Mirror final validated results to GCP Cloud Storage.

### Manual Verification
- Visual inspection of the `design_9_hardened` vs `design_9` interface in PyMOL/NGLview if possible.
- Verify visibility of all GIFs and plots on the GitHub Repo URL.
