import sys
from filter_and_rank import passes_complexity

def test_complexity_filters():
    # 1. The winning sequence (small-vole-maple)
    # Charge fraction: 50% (50/100)
    # Hydrophobic fraction: 30% (30/100)
    # Longest run of consecutive identical charged residues is 3 (e.g. EEE)
    winner_seq = "SAEEEVEEKAKEIEEEANSEETKERLKKLKEGKSKDPEDKKERKELEEDLEKYKNADLDLLKEKLKEAAIENLELGLYEIAEFNLEELYEVLLLEVYKEV"
    assert passes_complexity(winner_seq) is True, "Winner sequence should pass v2 complexity filter!"

    # 2. Polyelectrolyte Trap sequence (design_1)
    # Highly repetitive, charge fraction > 55%
    trap_seq = "EELEKKLEELRKKLEELRKKLEELRKKLEELRKKLEELRKKLEELRKKLEELRKK"
    assert passes_complexity(trap_seq) is False, "Polyelectrolyte trap should be rejected!"

    # 3. Excessive consecutive charged run (e.g. KKKK)
    run_seq = "SAAAAAKAAAAAARAAAAAELEKKKKEELEARAELEKKLEELEARAELAEARARAEALKLKL"
    assert passes_complexity(run_seq) is False, "Sequence with KKKK run should be rejected!"

    print("[SUCCESS] All complexity filter tests passed successfully!")

if __name__ == "__main__":
    test_complexity_filters()
