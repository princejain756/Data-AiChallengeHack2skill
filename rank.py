import json
import argparse
import csv
import sys

def rank_candidates(candidates_file, output_file):
    """
    Basic candidate loader and placeholder scorer.
    Just reads the JSONL and outputs top 100 by a simple heuristic.
    """
    print(f"Loading candidates from {candidates_file}...")
    candidates = []
    
    with open(candidates_file, 'r', encoding='utf-8') as f:
        for line in f:
            candidate = json.loads(line)
            cid = candidate.get("candidate_id")
            profile = candidate.get("profile", {})
            yoe = profile.get("years_of_experience", 0)
            
            # Basic filter: only consider candidates with 3+ years
            if yoe >= 3:
                candidates.append((cid, yoe, candidate))
    
    # Sort by years of experience descending as a starting point
    candidates.sort(key=lambda x: -x[1])
    top_100 = candidates[:100]
    
    print(f"Writing top 100 candidates to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank, (cid, yoe, cand) in enumerate(top_100, 1):
            title = cand.get("profile", {}).get("current_title", "")
            writer.writerow([cid, rank, round(yoe / 10.0, 4), f"{title}, {yoe} years experience"])
    
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer role.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Output CSV path")
    args = parser.parse_args()
    rank_candidates(args.candidates, args.out)
