import json
import argparse
import csv
import sys
from datetime import datetime

CURRENT_DATE = datetime(2026, 6, 15)

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

def is_honeypot(candidate):
    """
    Checks for synthetic profiles:
    - Expert skills with 0 months duration
    - Job durations exceeding total stated YoE
    - Job durations exceeding calendar range between start/end dates
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    
    # Expert with 0 months
    expert_zero = [s for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 0]
    if len(expert_zero) >= 3:
        return True
    
    yoe = profile.get("years_of_experience", 0)
    yoe_months = yoe * 12
    
    for job in career_history:
        duration = job.get("duration_months", 0)
        
        # Duration exceeds total YoE
        if duration > yoe_months + 6:
            return True
        
        # Duration exceeds calendar range
        start_d = parse_date(job.get("start_date"))
        end_d = parse_date(job.get("end_date"))
        
        if start_d:
            ref_end = end_d if end_d else CURRENT_DATE
            cal_months = (ref_end.year - start_d.year) * 12 + (ref_end.month - start_d.month)
            if duration > cal_months + 12:
                return True
    
    return False

def rank_candidates(candidates_file, output_file):
    print(f"Loading candidates from {candidates_file}...")
    candidates = []
    honeypots_found = 0
    
    with open(candidates_file, 'r', encoding='utf-8') as f:
        for line in f:
            candidate = json.loads(line)
            cid = candidate.get("candidate_id")
            
            if is_honeypot(candidate):
                honeypots_found += 1
                continue
            
            profile = candidate.get("profile", {})
            yoe = profile.get("years_of_experience", 0)
            
            if yoe >= 3:
                candidates.append((cid, yoe, candidate))
    
    print(f"Filtered {honeypots_found} honeypot profiles.")
    
    # Still sorting by YoE for now, proper scoring coming next
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
