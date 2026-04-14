# ── CELL 7: design_9 ProteinMPNN diversification + Boltz2 scoring ─────────
# Runs directly in the existing Colab session (T4 GPU still active).
# Generates 50 sequence variants of design_9 backbone, scores all with Boltz2.
# ETA: ~5 min for MPNN setup + ~25 min for Boltz2 scoring (50 variants x ~30s)

import subprocess, sys, os, json, time, csv, shutil
from pathlib import Path
import numpy as np

# ── Step A: Install ProteinMPNN ───────────────────────────────────────────
MPNN_DIR = Path('/content/ProteinMPNN')
if not MPNN_DIR.exists():
    print("Cloning ProteinMPNN...")
    subprocess.run(['git', 'clone', 'https://github.com/dauparas/ProteinMPNN.git',
                    str(MPNN_DIR)], check=True)
    print("ProteinMPNN cloned.")
else:
    print("ProteinMPNN already present.")

# ── Step B: Upload design_9 PDB ──────────────────────────────────────────
# design_9_complex.pdb contains both the binder (chain A) and RBX1 (chain B)
# Upload it from: c:\Users\Gebruiker\Documents\Computational Bio\MD\data\candidates\design_9\design_9_complex.pdb

from google.colab import files
print("\nUpload design_9_complex.pdb from your local machine:")
print("Path: c:\\Users\\Gebruiker\\Documents\\Computational Bio\\MD\\data\\candidates\\design_9\\design_9_complex.pdb")
uploaded = files.upload()   # opens file picker

pdb_path = list(uploaded.keys())[0]
design9_pdb = Path('/content') / pdb_path
print(f"Uploaded: {design9_pdb}  ({design9_pdb.stat().st_size} bytes)")

# ── Step C: Run ProteinMPNN — 17 sequences × 3 temperatures = 51 variants ─
MPNN_OUT = Path('/content/mpnn_design9')
MPNN_OUT.mkdir(exist_ok=True)

print("\nRunning ProteinMPNN on design_9 backbone...")
all_variants = []

for temp in [0.1, 0.2, 0.3]:
    out_t = MPNN_OUT / f'temp_{temp}'
    out_t.mkdir(exist_ok=True)

    proc = subprocess.run(
        [
            sys.executable,
            str(MPNN_DIR / 'protein_mpnn_run.py'),
            '--pdb_path',          str(design9_pdb),
            '--out_folder',        str(out_t),
            '--num_seq_per_target','17',
            '--sampling_temp',     str(temp),
            '--seed',              '42',
            '--batch_size',        '1',
            '--chain_id_jsonl',    '/dev/null',    # use all chains
        ],
        capture_output=True, text=True, cwd=str(MPNN_DIR)
    )

    if proc.returncode != 0:
        print(f"  MPNN error at T={temp}:\n{proc.stderr[-400:]}")
        continue

    # Parse MPNN FASTA output
    for fa in out_t.glob('**/*.fa'):
        lines = open(fa).readlines()
        for i in range(0, len(lines)-1, 2):
            hdr = lines[i].strip().lstrip('>')
            seq = lines[i+1].strip()
            if 40 <= len(seq) <= 150:
                all_variants.append({'name': f'd9_T{temp}_{i//2:03d}',
                                     'seq': seq, 'temp': temp})

    print(f"  T={temp}: collected {len(all_variants)} variants so far")

# Deduplicate
seen = set()
unique_variants = []
for v in all_variants:
    if v['seq'] not in seen:
        seen.add(v['seq'])
        unique_variants.append(v)

# Add design_9 itself as reference
DESIGN9_SEQ = 'AAALAAAVAAARAAAAAELAEARARAEALAAEGREEEGRRLLESAERRAETRAALIARVLAA'
unique_variants.insert(0, {'name': 'design_9_original', 'seq': DESIGN9_SEQ, 'temp': 0.0})

print(f"\nTotal unique variants to score: {len(unique_variants)}")
print(f"(Including design_9 original as reference)")


# ── Step D: Boltz2 score all variants ────────────────────────────────────
RBX1_SEQ = 'VDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH'
BOLTZ_CMD = shutil.which('boltz')
SCORE_OUT = Path('/content/boltz2_mpnn_variants')
SCORE_OUT.mkdir(exist_ok=True)

def write_fasta_boltz(name, binder_seq, out_path):
    with open(out_path, 'w') as f:
        f.write(f'>A|protein\n{binder_seq}\n')
        f.write(f'>B|protein\n{RBX1_SEQ}\n')

def compute_ipsae(pae, n_binder):
    m = np.array(pae)
    return float(max(0.0, 1.0 - ((m[:n_binder, n_binder:].mean() + m[n_binder:, :n_binder].mean()) / 2.0) / 31.75))

def score_variant(v):
    name = v['name']
    seq  = v['seq']
    safe = name.replace('|','_')
    sdir = SCORE_OUT / safe
    sdir.mkdir(exist_ok=True)
    fasta = sdir / 'input.fasta'
    write_fasta_boltz(name, seq, fasta)

    t0 = time.time()
    proc = subprocess.run(
        [BOLTZ_CMD, 'predict', str(fasta),
         '--out_dir', str(sdir),
         '--accelerator', 'gpu', '--devices', '1',
         '--recycling_steps', '3', '--sampling_steps', '200',
         '--diffusion_samples', '1', '--output_format', 'pdb',
         '--model', 'boltz2', '--write_full_pae', '--override'],
        capture_output=True, text=True
    )
    elapsed = round(time.time() - t0)

    if 'Failed to process' in proc.stdout:
        return None

    confs = sorted(sdir.rglob('confidence_*.json'))
    if not confs:
        return None

    conf  = json.load(open(confs[0]))
    pae   = conf.get('pae')
    iptm  = conf.get('iptm')
    plddt = conf.get('complex_plddt')
    ptm   = conf.get('ptm')
    ipsae = compute_ipsae(pae, len(seq)) if pae else iptm

    return {
        'name':    name, 'sequence': seq, 'length': len(seq),
        'temp':    v['temp'],
        'ipsae':   round(ipsae, 4) if ipsae else None,
        'plddt':   round(plddt, 2) if plddt else None,
        'ptm':     round(ptm,   4) if ptm else None,
        'iptm':    round(iptm,  4) if iptm else None,
        'pass_v2': ipsae is not None and ipsae >= 0.70,
        'elapsed': elapsed,
    }

print(f"\nScoring {len(unique_variants)} variants with Boltz2...")
print(f"ETA: ~{len(unique_variants) * 2.5 / 60:.0f} min")
print("=" * 70)

results = []
best_so_far = 0.8948  # design_9 original

for i, v in enumerate(unique_variants):
    print(f"[{i+1}/{len(unique_variants)}] {v['name']}  T={v['temp']}  ({len(v['seq'])} AA)")
    r = score_variant(v)
    if r:
        results.append(r)
        badge = '🔥' if r['ipsae'] and r['ipsae'] > best_so_far else ('✅' if r['pass_v2'] else '❌')
        if r['ipsae'] and r['ipsae'] > best_so_far:
            best_so_far = r['ipsae']
            print(f"  {badge} NEW BEST! ipSAE={r['ipsae']}  pLDDT={r['plddt']}  ({r['elapsed']}s)")
        else:
            print(f"  {badge}  ipSAE={r['ipsae']}  pLDDT={r['plddt']}  ({r['elapsed']}s)")

# ── Step E: Results summary ───────────────────────────────────────────────
results.sort(key=lambda r: r.get('ipsae') or 0, reverse=True)
passed = [r for r in results if r.get('pass_v2')]

print(f"\n{'='*70}")
print(f"design_9 Diversification — Boltz2 Results")
print(f"  Scored:   {len(results)}")
print(f"  Passed:   {len(passed)}  (ipSAE ≥ 0.70)")
print(f"  Best:     ipSAE={results[0]['ipsae'] if results else 'N/A'}")
print(f"\nTop 10:")
for r in results[:10]:
    badge = '🔥' if r['ipsae'] and r['ipsae'] > 0.90 else ('✅' if r['pass_v2'] else '❌')
    print(f"  {badge}  ipSAE={r['ipsae']}  pLDDT={r['plddt']}  T={r['temp']}  {r['sequence'][:40]}...")

# Save CSV
csv_path = '/content/design9_variants_boltz2.csv'
with open(csv_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['name','sequence','length','temp',
                                            'ipsae','plddt','ptm','iptm','pass_v2','elapsed'])
    writer.writeheader()
    writer.writerows(results)
print(f"\nSaved: {csv_path}")
files.download(csv_path)
