import urllib.request
import urllib.parse
import json
import time
import os
import random

# Dyno API Key provided by user
API_KEY = "ak_38AVXR9EHXHN03W3E1BHXPND3F33XXM1"
BASE_URL = "https://api.dyno-agents.app/v1/phi/jobs/"

# Files to score (Top 10 candidates)
PDB_FILES = {
    "design_9": "data/candidates/design_9/design_9_complex.pdb",
    "design_15": "data/candidates/design_15.pdb",
    "design_1": "data/candidates/design_1.pdb",
    "design_10": "data/candidates/design_10.pdb",
    "design_21": "data/candidates/design_21/design_21_complex.cif",
    "design_16": "data/candidates/design_16.pdb",
    "design_18": "data/candidates/design_18.pdb",
    "batch2_design_0": "data/candidates/batch2_design_0.pdb",
    "design_52": "data/candidates/design_52.pdb",
    "design_50": "data/candidates/design_50.pdb"
}

def make_request(url, data=None, headers=None, method='GET'):
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"  HTTP Error {e.code}: {err_msg}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def submit_pdb(name, pdb_path):
    # USE UNIQUE NAME TO BYPASS CACHE
    unique_name = f"{name}_val_{int(time.time())}_{random.randint(100,999)}"
    print(f"\n>>> Submitting {unique_name}...")
    with open(pdb_path, 'r') as f:
        pdb_content = f.read()
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "job_type": "af2rank",
        "params": {
            "pdb_str": pdb_content
        },
        "name": unique_name
    }
    
    data = json.dumps(payload).encode('utf-8')
    res_json = make_request(BASE_URL, data=data, headers=headers, method='POST')
    if res_json:
        res_data = json.loads(res_json)
        return res_data["job_id"]
    return None

def poll_job(job_id):
    url = f"{BASE_URL}{job_id}/status/"
    headers = {"x-api-key": API_KEY}
    
    while True:
        res_json = make_request(url, headers=headers, method='GET')
        if res_json:
            res_data = json.loads(res_json)
            status = res_data.get("status")
            print(f"  Job {job_id} Status: {status}")
            if status == "completed":
                return True
            if status == "failed":
                # Check for errors
                err = res_data.get("error")
                if err:
                    print(f"  Job FAILED with error: {err}")
                return False
        else:
            print(f"  Failed to poll job {job_id}")
            return False
        time.sleep(15)

def get_scores_with_retry(job_id, max_retries=10):
    url = f"{BASE_URL}{job_id}/scores/"
    headers = {"x-api-key": API_KEY}
    
    for i in range(max_retries):
        res_json = make_request(url, headers=headers, method='GET')
        if res_json:
            return json.loads(res_json)
        print(f"  Scores not ready yet (Attempt {i+1}/{max_retries}). Waiting 30s...")
        time.sleep(30)
    return None

if __name__ == "__main__":
    job_ids = {}
    print(f"Submitting {len(PDB_FILES)} jobs to Dyno Phi...")
    
    for name, path in PDB_FILES.items():
        if not os.path.exists(path):
            print(f"Skipping {name}: file not found at {path}")
            continue
            
        print(f"  Submitting {name}...")
        job_id = submit_pdb(name, path)
        if job_id:
            job_ids[name] = job_id
        else:
            print(f"    FAILED submission for {name}")

    if not job_ids:
        print("No jobs submitted successfully.")
        exit(1)

    print("\nPolling for results (this may take 5-10 minutes)...")
    final_results = {}
    pending = list(job_ids.items())
    
    attempts = 0
    max_attempts = 20
    while pending and attempts < max_attempts:
        attempts += 1
        print(f"\nPolling Attempt {attempts}/{max_attempts}...")
        still_pending = []
        
        for name, job_id in pending:
            if poll_job(job_id):
                scores = get_scores_with_retry(job_id)
                if scores:
                    final_results[name] = scores
                    score = scores.get('composite_score', 'N/A')
                    print(f"    SUCCESS for {name}: {score}")
                else:
                    print(f"    FAILED to get scores for {name} (Job {job_id})")
            else:
                still_pending.append((name, job_id))
        
        pending = still_pending
        if pending:
            print(f"  {len(pending)} jobs still pending. Waiting 30s...")
            time.sleep(30)

    if final_results:
        out_path = "data/candidates/dyno_grounding_results.json"
        with open(out_path, "w") as f:
            json.dump(final_results, f, indent=2)
        print(f"\nALL JOBS COMPLETE. Results saved to {out_path}")
    
    if pending:
        print(f"\nWARNING: {len(pending)} jobs timed out after {max_attempts} attempts.")
