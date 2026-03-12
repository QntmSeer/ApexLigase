# LinkedIn Post Draft: Project ApexLigase — De Novo Discovery for RBX1 🧬

Spent some time recently working on a de novo binder design submission for RBX1 as part of the GEM x Adaptyv RBX1 Binder Design Competition.

Did I choose the target? Not exactly 😄

RBX1 came with the challenge, and it turned out to be a genuinely interesting protein design problem. Competition link here: https://proteinbase.com/competitions/gem-adaptyv-rbx1

This project became a good exercise in stitching together RFdiffusion, ProteinMPNN, and GROMACS into one focused computational workflow for binder generation, prioritization, and structural evaluation.


🔬 Some highlights:
- **De Novo Scale**: Navigated the design space with 879 candidates via **RFdiffusion** & **ProteinMPNN**.
- **The "Super-Binder"**: Found a lead (`batch2_design_3`) that’s looking sharp—hits a **60% affinity bump** over the validated baseline (`ipTM` = 0.266).
- **Physical Validation**: Static $ipTM$ scores can be deceptive (the "plausibility trap"). To ensure we weren't just looking at a pretty decoy, I launched a 100ns GROMACS production run to confirm thermodynamic stability under thermal noise.
- **Validation Status**: About **22ns** into the run now. Interface is rock solid.

Lean compute, real output: The workflow has been running on a single NVIDIA L4 on GCP, which has been a nice reminder that meaningful structural biology work does not always require oversized infrastructure when the pipeline is optimized and containerized

Sharing one early MD visualization below from a computationally prioritized candidate.

Big thanks to Adaptyv Bio and the GEM Workshop for putting together the challenge.

And yes, before anyone asks why this ran on an L4 on GCP instead of some extravagant AWS setup, let’s just say the green Open to Work badge is still playing a quiet role in infrastructure decisions 😄

Fun challenge, difficult target, and a solid reminder that constrained setups can still produce serious work.

#ProteinDesign #DeNovoDesign #StructuralBiology #ProteinEngineering #GROMACS #AI #Biotech #DrugDiscovery #OpenToWork
