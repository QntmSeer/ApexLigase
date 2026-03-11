import os

path = '/home/qntmqrks/rbx1_design/Phase15_MassGeneration/validate_leads_v2.py'
with open(path, 'r') as f:
    code = f.read()

code = code.replace("seq = row['Sequence']", "seq = row['Sequence'].split('/')[-1]")

with open(path, 'w') as f:
    f.write(code)

print('Successfully patched validate_leads_v2.py')
