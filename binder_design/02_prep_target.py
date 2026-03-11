"""
02_prep_target.py — RBX1 Target Preparation
==========================================
- Downloads 2LGV from RCSB
- Extracts RING domain (chain A, residues 40-108)
- Locates Zn2+ ion positions (exclusion zones for binder design)
- Writes hotspot residue list for BindCraft / RFdiffusion
- Outputs: rbx1_ring.pdb, hotspots.json, zinc_positions.json
"""

import os
import json
import requests
import sys

# ----------------------------------------------------------------
# RBX1 RING domain hotspot residues (E2/Glomulin binding surface)
# From literature: Trp87, Arg91, Glu55, Gln57, Ile44, Ile54, Ala58, Pro95, Leu96
# Numbering in PDB 2LGV (full protein numbering)
# ----------------------------------------------------------------
HOTSPOT_RESIDUES = [43, 44, 46, 54, 55, 57, 58, 87, 91, 95, 96]
RING_START = 38   # 2LGV NMR structure covers residues 38-108 (not 40)
RING_END = 108
RBX1_CHAIN = "A"
PDB_ID = "2LGV"

def download_pdb(pdb_id, out_path):
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    print(f"Downloading {pdb_id} from RCSB...")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(out_path, "w") as f:
        f.write(r.text)
    print(f"  Saved to {out_path}")

def extract_ring_domain(full_pdb_path, ring_pdb_path, chain=RBX1_CHAIN,
                         start=RING_START, end=RING_END):
    """
    Extract RING domain residues + HETATM Zn2+ lines from the PDB.
    For NMR structures (2LGV), take only MODEL 1.
    """
    print(f"Extracting RING domain (chain {chain}, res {start}-{end})...")
    zinc_positions = []
    kept_lines = []
    in_model1 = False
    model_count = 0

    with open(full_pdb_path) as f:
        lines = f.readlines()

    for line in lines:
        record = line[:6].strip()

        if record == "MODEL":
            model_count += 1
            in_model1 = (model_count == 1)
            if model_count > 1:
                break
            continue
        if record == "ENDMDL":
            break

        # For NMR structures without MODEL records (shouldn't happen for 2LGV)
        if model_count == 0:
            in_model1 = True

        if not in_model1:
            continue

        if record in ("ATOM", "HETATM"):
            try:
                res_chain = line[21]
                res_num = int(line[22:26].strip())
            except (ValueError, IndexError):
                continue

            if res_chain != chain:
                continue

            # Keep protein ATOM records in range
            if record == "ATOM" and start <= res_num <= end:
                kept_lines.append(line)

            # Keep Zinc ions (ZN) regardless of residue number
            if record == "HETATM" and line[17:20].strip() == "ZN":
                kept_lines.append(line)
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    zinc_positions.append({
                        "atom": line[12:16].strip(),
                        "resnum": res_num,
                        "x": x, "y": y, "z": z
                    })
                except ValueError:
                    pass

    kept_lines.append("END\n")

    with open(ring_pdb_path, "w") as f:
        f.writelines(kept_lines)

    print(f"  Extracted {len(kept_lines)-1} atoms to {ring_pdb_path}")
    print(f"  Found {len(zinc_positions)} Zn2+ ions")
    return zinc_positions

def write_configs(hotspot_residues, zinc_positions, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # RFdiffusion hotspot format: "A43,A44,A46,..."
    rfdiff_hotspots = ",".join([f"{RBX1_CHAIN}{r}" for r in hotspot_residues])

    config = {
        "target_pdb": "rbx1_ring.pdb",
        "target_chain": RBX1_CHAIN,
        "ring_domain": {"start": RING_START, "end": RING_END},
        "hotspot_residues": hotspot_residues,
        "rfdiffusion_hotspot_string": rfdiff_hotspots,
        "zinc_positions": zinc_positions,
        "zinc_exclusion_radius_angstrom": 4.0,
        "notes": (
            "Hotspots = E2/Glomulin binding surface. "
            "Zn2+ exclusion zone prevents backbone clashes with coordination shell."
        )
    }

    hotspot_path = os.path.join(out_dir, "hotspots.json")
    with open(hotspot_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Hotspot config written to {hotspot_path}")
    print(f"  RFdiffusion hotspot string: {rfdiff_hotspots}")
    return config

def main():
    out_dir = os.path.join(os.path.dirname(__file__), "target")
    os.makedirs(out_dir, exist_ok=True)

    full_pdb = os.path.join(out_dir, f"{PDB_ID}.pdb")
    ring_pdb = os.path.join(out_dir, "rbx1_ring.pdb")

    download_pdb(PDB_ID, full_pdb)
    zinc_positions = extract_ring_domain(full_pdb, ring_pdb)
    config = write_configs(HOTSPOT_RESIDUES, zinc_positions, out_dir)

    print("\n=== Target Preparation Complete ===")
    print(f"  RING domain PDB : {ring_pdb}")
    print(f"  Hotspot config  : {os.path.join(out_dir, 'hotspots.json')}")
    print(f"  Zn2+ ions found : {len(zinc_positions)}")
    print(f"  Hotspot string  : {config['rfdiffusion_hotspot_string']}")

if __name__ == "__main__":
    main()
