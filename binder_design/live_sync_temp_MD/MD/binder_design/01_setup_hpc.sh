#!/bin/bash
# ================================================================
# HPC Setup Script — RBX1 Binder Design Competition
# Installs: BindCraft, RFdiffusion, ProteinMPNN, Chai-1, ESM3
# Run once on a fresh Ubuntu H100 node (80GB VRAM)
# ================================================================
set -e
WORKDIR="$HOME/rbx1_binder_design"
mkdir -p "$WORKDIR" && cd "$WORKDIR"

echo "================================================================"
echo "STEP 1: Install Miniconda (if not present)"
echo "================================================================"
if [ -d "$HOME/miniconda3" ]; then
    echo "Miniconda directory already exists. Activating..."
    eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
    conda init bash || true
elif ! command -v conda &>/dev/null; then
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p "$HOME/miniconda3"
    eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
    conda init bash
else
    eval "$(conda shell.bash hook)"
    echo "Conda already installed and in PATH."
fi

echo "================================================================"
echo "STEP 2: Install BindCraft (Primary Design Engine)"
echo "================================================================"
if [ ! -d "BindCraft" ]; then
    git clone https://github.com/martinpacesa/BindCraft.git
fi
cd BindCraft
conda env create -f environment.yml -n bindcraft --quiet || echo "BindCraft env may already exist"
conda run -n bindcraft pip install -q --upgrade pip
# Download AF2 weights for BindCraft
mkdir -p params
if [ ! -f "params/params_model_1_multimer_v3.npz" ]; then
    echo "Downloading AlphaFold2 multimer weights..."
    wget -q "https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar" -O af2_params.tar
    tar xf af2_params.tar -C params/ && rm af2_params.tar
fi
cd "$WORKDIR"

echo "================================================================"
echo "STEP 3: Install RFdiffusion"
echo "================================================================"
if [ ! -d "RFdiffusion" ]; then
    git clone https://github.com/RosettaCommons/RFdiffusion.git
fi
cd RFdiffusion
conda env create -f env/SE3nv.yml -n rfdiffusion --quiet || echo "RFdiffusion env may already exist"
# Download binder design model weights
mkdir -p models
if [ ! -f "models/RFdiffusion_ActiveSite_ckpt.pt" ]; then
    wget -q "http://files.ipd.uw.edu/pub/RFdiffusion/6f5902ac237024bdd0c176cb93063dc/Base_ckpt.pt" -O models/Base_ckpt.pt
    wget -q "http://files.ipd.uw.edu/pub/RFdiffusion/e29311f6f1bf1af907f9ef9f44b8328b/ActiveSite_ckpt.pt" -O models/RFdiffusion_ActiveSite_ckpt.pt
fi
cd "$WORKDIR"

echo "================================================================"
echo "STEP 4: Install ProteinMPNN"
echo "================================================================"
if [ ! -d "ProteinMPNN" ]; then
    git clone https://github.com/dauparas/ProteinMPNN.git
fi
# ProteinMPNN uses the rfdiffusion env or base conda
conda run -n rfdiffusion pip install -q biopython

echo "================================================================"
echo "STEP 5: Install Chai-1"
echo "================================================================"
conda create -n chai1 python=3.10 -y --quiet || echo "chai1 env may exist"
conda run -n chai1 pip install -q chai_lab torch --index-url https://download.pytorch.org/whl/cu121

echo "================================================================"
echo "STEP 6: Install ESM3"
echo "================================================================"
conda create -n esm3 python=3.10 -y --quiet || echo "esm3 env may exist"
conda run -n esm3 pip install -q esm huggingface_hub

echo "================================================================"
echo "STEP 7: Setup utility packages (for filter/rank scripts)"
echo "================================================================"
conda create -n bioutils python=3.10 -y --quiet || echo "bioutils env may exist"
conda run -n bioutils pip install -q biopython numpy pandas requests editdistance tqdm

echo "================================================================"
echo "STEP 8: Copy pipeline scripts to workdir"
echo "================================================================"
cp -r ~/binder_design/* "$WORKDIR/" 2>/dev/null || true

echo ""
echo "================================================================"
echo "ALL TOOLS INSTALLED SUCCESSFULLY!"
echo "Working directory: $WORKDIR"
echo "Next step: run 02_prep_target.py, then run_all.sh"
echo "================================================================"
