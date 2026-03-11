# LinkedIn Post Draft: Project NeatLigase — AI-Driven Binder Discovery for RBX1

I’m excited to share a significant milestone in my latest protein design project: the discovery of **Design_9**, a high-affinity synthetic binder for the **RBX1** (RING-box protein 1) subunit of the SCF E3 ubiquitin ligase complex.

RBX1 is a critical component in cellular protein degradation, and targeting its interface opens new possibilities for therapeutic intervention in oncology and beyond.

### Key Technical Achievements:
- **Computational Pipeline**: Leveraged RFdiffusion for backbone scaffolding and ProteinMPNN for sequence optimization. 
- **Scale**: Generated and screened over 879 candidate backbones to identify the top-performing scaffolds.
- **Super-Binder Discovery**: Discovered a next-generation lead (`batch2_design_3`) exhibiting a **60% improvement** in ChAI-1 predicted binding affinity (`ipTM` = 0.266 vs 0.165 for the baseline).
- **Validation**: Conducted a 100ns GPU-accelerated GROMACS molecular dynamics simulation on an NVIDIA L4 to verify structural stability of the baseline and launched production MD for the super-binder.

This project was a deep dive into the intersection of generative AI and structural biology, proving that combining structure-based generation with sequence optimization can consistently yield higher-affinity protein-protein interactions.

Next stop: sending these validated sequences off to Adaptyv Bio for automated wet-lab synthesis and SPR affinity testing!

Check out the full repository and simulation data here: [Link to Repository]

#ProteinDesign #AI #StructuralBiology #DrugDiscovery #GROMACS #RFdiffusion #Biotech
