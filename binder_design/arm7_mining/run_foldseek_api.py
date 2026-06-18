import os
import sys
import time
import requests
import json
from pathlib import Path

# Foldseek API endpoints
FOLDSEEK_URL = "https://search.foldseek.com/api/ticket"
DATABASES = ["afdb50", "afdb-swissprot", "afdb-proteome", "pdb100", "mgnify_esm30"]

def submit_search(pdb_path, databases=DATABASES):
    """Submits a structural search ticket to Foldseek."""
    print(f"Submitting {pdb_path} to Foldseek API...")
    
    with open(pdb_path, "rb") as f:
        # Explicitly set filename and content-type for the multipart form
        files = {
            "q": (os.path.basename(pdb_path), f, "text/plain"),
        }
        # Some Foldseek API versions prefer multiple 'database' keys
        data = [
            ("mode", "3diaa"),
        ]
        for db in databases:
            data.append(("database[]", db))
        
        response = requests.post(FOLDSEEK_URL, files=files, data=data)
        if response.status_code != 200:
            print(f"  Submission failed: {response.text}")
            response.raise_for_status()
            
        ticket = response.json()
        print(f"  Ticket created: {ticket['id']}")
        return ticket['id']

def poll_status(ticket_id):
    """Polls the ticket status until it is COMPLETE."""
    status_url = f"{FOLDSEEK_URL}/{ticket_id}"
    print(f"Polling ticket {ticket_id}...")
    
    while True:
        try:
            response = requests.get(status_url)
            response.raise_for_status()
            status_data = response.json()
        except Exception as e:
            print(f"  Polling error: {e}")
            time.sleep(5)
            continue
        
        status = status_data.get("status")
        print(f"  Status: {status}")
        
        if status == "COMPLETE":
            return status_data
        elif status == "ERROR":
            print(f"  Error in Foldseek search: {status_data}")
            return None
        
        time.sleep(10) # Wait 10 seconds between polls

def download_results(ticket_id, out_dir):
    """Downloads the results of a completed ticket."""
    # API result endpoint is typically /result/{id}/0
    results_url = f"https://search.foldseek.com/api/result/{ticket_id}/0"
    print(f"Downloading results for {ticket_id}...")
    
    response = requests.get(results_url)
    response.raise_for_status()
    
    out_path = Path(out_dir) / f"foldseek_results_{ticket_id}.json"
    with open(out_path, "w") as f:
        json.dump(response.json(), f, indent=2)
    
    print(f"  Results saved to {out_path}")
    return response.json()

def process_results(results_data, length_range=(40, 150)):
    """Logs the top hits that match our criteria."""
    hits_data = results_data.get("results", [])
    if not hits_data:
        print("No hits found.")
        return []

    valid_hits = []
    print(f"\nProcessing results (Length {length_range[0]}-{length_range[1]} AA):")
    
    for db_res in hits_data:
        db_name = db_res.get("db", "unknown")
        # alignments is a list of lists of hit dicts
        alignments = db_res.get("alignments", [])
        for aln_group in alignments:
            # aln_group is usually a list with one hit dict
            for hit in aln_group:
                target = hit.get("target")
                length = hit.get("dbLen", hit.get("len", 0))
                evalue = hit.get("eval", 1.0)
                
                # Filter by length
                if length_range[0] <= length <= length_range[1]:
                    hit["db"] = db_name # Store source DB
                    valid_hits.append(hit)

    # Sort by E-value
    valid_hits.sort(key=lambda h: h.get("eval", 1.0))

    for hit in valid_hits[:20]:
        target = hit.get("target", "Unknown")
        length = hit.get("dbLen", 0)
        eval_  = hit.get("eval", 1.0)
        db     = hit.get("db", "?")
        print(f"  [{db}] {target[:40]:<40} | L: {length:>3} | E: {eval_:.2e}")

    print(f"\nTotal valid hits found: {len(valid_hits)}")
    return valid_hits

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_foldseek_api.py <pdb_path> [out_dir]")
        sys.exit(1)

    pdb_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "target"
    os.makedirs(out_dir, exist_ok=True)

    try:
        ticket_id = submit_search(pdb_path)
        status_data = poll_status(ticket_id)
        if status_data:
            results = download_results(ticket_id, out_dir)
            valid_hits = process_results(results)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
