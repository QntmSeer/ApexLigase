#!/bin/bash
gcloud compute ssh qntmqrks@crunchy-peptides --zone=us-central1-a --command="sed -i 's|return lines\[3\].strip()|return lines[3].strip().split(\"/\")[-1]|' /home/qntmqrks/rbx1_design/Phase15_MassGeneration/HARDENED_v1/bin/validator.py"
