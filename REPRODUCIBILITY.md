# ApexLigase: Pipeline Reproducibility Guide

All steps of the binder design and validation pipeline have been archived to ensure reproducibility.

## 1. Quick Start (Containerized)
To run the full validation suite (CABS-flex + GROMACS + Dyno Psi-Phi), use the provided `docker-compose`:

```bash
cd deploy/
export DYNO_API_KEY="your_api_key_here"
docker-compose up cabs-flex  # For rapid screening
docker-compose up gromacs-gpu # For 100ns MD (requires NVIDIA Docker)
```

## 2. Key Components Archived
- **Scripts**: Located in `/scripts/`
  - `launch_design10_md.sh`: Full GROMACS workflow with embedded `.mdp` configs.
  - `cabs_batch_screen.sh`: Automated parallel screening of PDB candidates.
  - `dyno_phi_score.py`: Experimental success probability ranking.
- **Data**: Initial PDBs and baseline trajectories are in `/data/`.

## 3. HPC Summary (Phase 21-22)
- **Instance**: `crunchy-peptides-v3` (NVIDIA L4)
- **Status**: Successfully terminated after verifying Design_10 Maryland completion.
- **Note**: Disk saturation was resolved by vacuuming journals, and the pipeline was recovered in its entirety.

The designs are ready for wet-lab synthesis at **Adaptyv Bio**.
