import tarfile
import base64
import io
import os
from pathlib import Path

def create_bundle():
    buf = io.BytesIO()
    # Ensure we include everything needed for v2
    files_to_add = [
        'binder_design',
        'STRATEGY_V2.md',
        'COMPETITION_ANALYSIS.md'
    ]
    
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        for item in files_to_add:
            if os.path.exists(item):
                tar.add(item, arcname=item)
            else:
                print(f"Warning: {item} not found")
                
    b64_data = base64.b64encode(buf.getvalue()).decode()
    
    # Construct the single command
    command = f"echo '{b64_data}' | base64 -d | tar -xz -C ~/ && cd ~/binder_design && chmod +x *.sh && ./rescore_v1_pool.sh"
    
    with open("deploy_v2.command", "w") as f:
        f.write(command)
        
    print(f"Deployment command generated (Size: {len(command)/1024:.2f} KB)")

if __name__ == "__main__":
    create_bundle()
