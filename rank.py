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
    
    expert_zero = [s for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 0]
    if len(expert_zero) >= 3:
        return True
    
    yoe = profile.get("years_of_experience", 0)
    yoe_months = yoe * 12
    
    for job in career_history:
        duration = job.get("duration_months", 0)
        if duration > yoe_months + 6:
            return True
        
        start_d = parse_date(job.get("start_date"))
        end_d = parse_date(job.get("end_date"))
        
        if start_d:
            ref_end = end_d if end_d else CURRENT_DATE
            cal_months = (ref_end.year - start_d.year) * 12 + (ref_end.month - start_d.month)
            if duration > cal_months + 12:
                return True
    
    return False

def calculate_score(candidate):
    """
    Multi-feature scoring:
    - YoE fit (20%)
    - Title match (25%)
    - Technical skills (30%)
    - Career description keywords (25%)
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    
    current_title = profile.get("current_title", "").lower()
    headline = profile.get("headline", "").lower()
    
    # Filter non-technical roles
    non_tech = ["marketing", "hr ", "recruiter", "sales", "finance", "accountant", "operations manager", "customer support"]
    for kw in non_tech:
        if kw in current_title or kw in headline:
            return 0.0
    
    # Consulting-only backgrounds
    companies = [j.get("company", "").lower() for j in career_history]
    consulting = ["tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "wipro technologies", "tata consultancy services"]
    if len(companies) > 0 and all(c in consulting for c in companies):
        return 0.01
    
    # Location check
    country = profile.get("country", "").lower()
    location = profile.get("location", "").lower()
    signals = candidate.get("redrob_signals", {})
    willing_to_relocate = signals.get("willing_to_relocate", False)
    
    if country != "india" and not willing_to_relocate:
        return 0.02
    
    # YoE score
    yoe = profile.get("years_of_experience", 0)
    if 5.0 <= yoe <= 9.0:
        yoe_score = 1.0
    elif 4.0 <= yoe < 5.0 or 9.0 < yoe <= 12.0:
        yoe_score = 0.6
    else:
        yoe_score = 0.1
    
    # Title score
    title_score = 0.0
    tech_titles = ["ai", "ml", "machine learning", "nlp", "search", "retrieval", "data scientist", "backend", "software engineer", "full stack"]
    for t in tech_titles:
        if t in current_title:
            title_score = max(title_score, 0.8)
        if "senior" in current_title or "lead" in current_title or "staff" in current_title:
            title_score = min(title_score + 0.2, 1.0)
    
    # Skills score
    target_skills = {
        "vector_db": ["pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch", "elasticsearch"],
        "embeddings": ["embeddings", "sentence-transformers", "bge", "e5", "semantic search"],
        "evaluation": ["ndcg", "mrr", "map", "evaluation", "a/b testing"],
        "python": ["python"],
        "fine_tuning": ["fine-tuning", "lora", "qlora", "peft"]
    }
    
    skills_found = {}
    for s in skills:
        sname = s.get("name", "").lower()
        prof = s.get("proficiency", "beginner")
        duration = s.get("duration_months", 0)
        prof_mult = {"beginner": 0.5, "intermediate": 0.8, "advanced": 1.0, "expert": 1.2}[prof]
        
        for category, keywords in target_skills.items():
            for kw in keywords:
                if kw in sname:
                    skills_found[category] = max(skills_found.get(category, 0), prof_mult * (duration / 12.0))
    
    skills_score = sum(skills_found.values())
    
    # Career keyword relevance
    career_relevance = 0.0
    rel_keywords = ["embedding", "vector", "pinecone", "weaviate", "qdrant", "milvus", "faiss", "hybrid search", "ndcg", "mrr", "ranking", "search engine", "retrieval", "rerank", "llm", "fine-tune"]
    for job in career_history:
        jdesc = job.get("description", "").lower()
        jtitle = job.get("title", "").lower()
        for kw in rel_keywords:
            if kw in jdesc or kw in jtitle:
                career_relevance += 1.0
    
    career_score = min(career_relevance / 5.0, 1.0)
    
    # Combined score (no behavioral modifiers yet)
    raw_score = (yoe_score * 0.2) + (title_score * 0.25) + (min(skills_score / 3.0, 1.0) * 0.3) + (career_score * 0.25)
    
    return round(raw_score, 4)

def rank_candidates(candidates_file, output_file):
    print(f"Loading candidates from {candidates_file}...")
    candidates = []
    honeypots = 0
    
    with open(candidates_file, 'r', encoding='utf-8') as f:
        for line in f:
            candidate = json.loads(line)
            cid = candidate.get("candidate_id")
            
            if is_honeypot(candidate):
                honeypots += 1
                continue
            
            score = calculate_score(candidate)
            if score > 0.05:
                candidates.append((cid, score, candidate))
    
    print(f"Filtered {honeypots} honeypots.")
    
    # Sort by score desc, tie-break by ID
    candidates.sort(key=lambda x: (-x[1], x[0]))
    top_100 = candidates[:100]
    
    print(f"Writing top 100 to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank, (cid, score, cand) in enumerate(top_100, 1):
            title = cand.get("profile", {}).get("current_title", "")
            yoe = cand.get("profile", {}).get("years_of_experience", 0)
            writer.writerow([cid, rank, score, f"{title} with {yoe} years"])
    
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer role.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Output CSV path")
    args = parser.parse_args()
    rank_candidates(args.candidates, args.out)
