# LinkedIn Post Draft: Project ApexLigase — De Novo Discovery for RBX1 🧬

Spent some time recently working on a de novo binder design submission for RBX1 as part of the GEM x Adaptyv RBX1 Binder Design Competition.

Did I choose the target? Not exactly 😄

RBX1 came with the challenge, and it turned out to be a genuinely interesting protein design problem. Competition link here: https://proteinbase.com/competitions/gem-adaptyv-rbx1

This project became a good exercise in stitching together RFdiffusion, ProteinMPNN, and GROMACS into one focused computational workflow for binder generation, prioritization, and structural evaluation.


🔬 A few highlights from the work

De novo at scale: Explored a design space of 879 candidates generated with RFdiffusion and ProteinMPNN

Candidate prioritization: Narrowed the pool through computational screening to a smaller set of designs for deeper structural assessment

Simulation in progress: Multiple top candidates are currently being evaluated through 100 ns GROMACS production runs, with early trajectory analysis already giving useful signals on stability and interface behavior

Lean compute, real output: The workflow has been running on a single NVIDIA L4 on GCP, which has been a nice reminder that meaningful structural biology work does not always require oversized infrastructure when the pipeline is optimized and containerized

Sharing one early MD visualization below from a computationally prioritized candidate.

Big thanks to Adaptyv Bio and the GEM Workshop for putting together the challenge.

And yes, before anyone asks why this ran on an L4 on GCP instead of some extravagant AWS setup, let’s just say the green Open to Work badge is still playing a quiet role in infrastructure decisions 😄

Fun challenge, difficult target, and a solid reminder that constrained setups can still produce serious work.

#ProteinDesign #DeNovoDesign #StructuralBiology #ProteinEngineering #GROMACS #AI #Biotech #DrugDiscovery #OpenToWork
