import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from premium_plots import plot_premium_rg, plot_premium_rmsd_comparison, plot_premium_rmsf_comparison

def main():
    parser = argparse.ArgumentParser(description="ApexLigase: High-Resolution MD Analysis Pipeline")
    parser.add_argument("--mode", choices=["visualize", "analyze"], default="visualize", help="Operational mode")
    args = parser.parse_args()

    if not os.path.exists("assets"):
        os.makedirs("assets")

    print(f"--- ApexLigase Pipeline: {args.mode.upper()} ---")
    
    if args.mode == "visualize":
        # Generate the high-fidelity plots used in the technical report
        plot_premium_rg()
        plot_premium_rmsd_comparison()
        plot_premium_rmsf_comparison()
        print("Success: Research-grade visuals updated in assets/")
    
    elif args.mode == "analyze":
        # Placeholder for deeper trajectory quantification
        print("Feature coming soon: Per-residue energy decomposition.")

if __name__ == "__main__":
    main()
