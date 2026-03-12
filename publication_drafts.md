# LinkedIn Post Draft: Project ApexLigase — De Novo Discovery for RBX1 🧬

Spent some time recently working on a de novo binder design submission for RBX1 as part of the GEM x Adaptyv RBX1 Binder Design Competition.

Did I choose the target? Not exactly 😄

RBX1 came with the challenge, and it turned out to be a genuinely interesting protein design problem. Competition link here: https://proteinbase.com/competitions/gem-adaptyv-rbx1

This project became a good exercise in stitching together RFdiffusion, ProteinMPNN, and GROMACS into one focused computational workflow for binder generation, prioritization, and structural evaluation.


### 🔬 Some highlights from the work:
- **De novo at scale**: Explored a design space of 879 candidates generated with **RFdiffusion** and **ProteinMPNN**.
- **The "Super-Binder"**: Found a lead (`batch2_design_3`) that’s looking sharp—hits a **60% affinity bump** over the validated baseline (`ipTM` = 0.266).
- **Physical Validation**: We know static $ipTM$ and $pLDDT$ scores can be deceptive—high confidence doesn't always mean binding or stability. I used 100ns GROMACS production runs to confirm the actual dynamics of the interface.
- **Validation Status**: About **24ns** into the run now. Interface is rock solid.

Lean compute, real output: The workflow has been running on a single NVIDIA L4 on GCP, which has been a nice reminder that meaningful structural biology work does not always require oversized infrastructure when the pipeline is optimized and containerized

Sharing one early MD visualization below from a computationally prioritized candidate.

Big thanks to Adaptyv Bio and the GEM Workshop for putting together the challenge.

And yes, before anyone asks why this ran on an L4 on GCP instead of some extravagant AWS setup, let’s just say the green Open to Work badge is still playing a quiet role in infrastructure decisions 😄

Fun challenge, difficult target, and a solid reminder that constrained setups can still produce serious work.

#ProteinDesign #DeNovoDesign #StructuralBiology #ProteinEngineering #GROMACS #AI #Biotech #DrugDiscovery #OpenToWork
