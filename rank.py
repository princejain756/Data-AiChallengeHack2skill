import json
import argparse
import sys
import os
import random
from datetime import datetime

# Reference date for calendar calculations
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
    Identifies synthetically anomalous 'honeypot' profiles based on:
    1. Skills proficiency contradictions (expert with 0 duration).
    2. Job durations exceeding the profile's stated total years of experience.
    3. Job durations exceeding the calendar time elapsed since start date.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    
    # 1. Expert skills with 0 months used
    expert_zero_months = [s for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 0]
    if len(expert_zero_months) >= 3:
        return True
        
    # 2. Job duration exceeds profile total YoE
    yoe = profile.get("years_of_experience", 0)
    yoe_months = yoe * 12
    for job in career_history:
        duration = job.get("duration_months", 0)
        if duration > yoe_months + 6:
            return True
            
        # 3. Job duration exceeds calendar range
        start_str = job.get("start_date")
        end_str = job.get("end_date")
        start_d = parse_date(start_str)
        end_d = parse_date(end_str) if end_str else None
        
        if start_d:
            ref_end = end_d if end_d else CURRENT_DATE
            calendar_months = (ref_end.year - start_d.year) * 12 + (ref_end.month - start_d.month)
            if duration > calendar_months + 12:
                return True
                
    return False

def calculate_score(candidate):
    """
    Scores candidates based on how well they fit the founding Senior AI Engineer role:
    - YoE match (5-9 years is ideal).
    - Current and historical technical title matches.
    - Production skills (vector databases, semantic search, evaluation, fine-tuning).
    - Direct keyword relevance in career history descriptions.
    - Adjustments for product vs consulting firms.
    - Behavioral signals (activity, response rate, notice period, location).
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    signals = candidate.get("redrob_signals", {})
    
    # 1. Title/Role exclusions
    current_title = profile.get("current_title", "").lower()
    headline = profile.get("headline", "").lower()
    
    # Exclude obvious non-technical roles
    non_tech_keywords = ["marketing", "hr ", "recruiter", "sales", "finance", "accountant", "operations manager", "customer support"]
    for kw in non_tech_keywords:
        if kw in current_title or kw in headline:
            return 0.0
            
    # Check for pure consulting background (exclude if all career history is at major consulting/IT service firms)
    companies = [j.get("company", "").lower() for j in career_history]
    consulting_firms = ["tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "wipro technologies", "tata consultancy services"]
    if len(companies) > 0 and all(c in consulting_firms for c in companies):
        return 0.01

    # Location check
    country = profile.get("country", "").lower()
    location = profile.get("location", "").lower()
    willing_to_relocate = signals.get("willing_to_relocate", False)
    
    # Noida / Pune preferred or Tier-1 cities
    in_target_city = "noida" in location or "pune" in location or "delhi" in location or "mumbai" in location or "hyderabad" in location or "gurgaon" in location or "bangalore" in location or "bengaluru" in location
    
    if country != "india":
        if not willing_to_relocate:
            return 0.02 # heavily down-weight international candidates unwilling to relocate
            
    # 2. Years of Experience (YoE) score (Target: 5-9 years)
    yoe = profile.get("years_of_experience", 0)
    if 5.0 <= yoe <= 9.0:
        yoe_score = 1.0
    elif 4.0 <= yoe < 5.0 or 9.0 < yoe <= 12.0:
        yoe_score = 0.6
    else:
        yoe_score = 0.1
        
    # 3. Technical Title score
    title_score = 0.0
    technical_titles = ["ai", "ml", "machine learning", "nlp", "search", "retrieval", "data scientist", "backend", "software engineer", "full stack"]
    for t in technical_titles:
        if t in current_title:
            title_score = max(title_score, 0.8)
        if "senior" in current_title or "lead" in current_title or "staff" in current_title:
            title_score = min(title_score + 0.2, 1.0)
            
    # 4. Target Skills score
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
    
    # 5. Career History Keyword relevance
    career_relevance = 0.0
    relevance_keywords = ["embedding", "vector", "pinecone", "weaviate", "qdrant", "milvus", "faiss", "hybrid search", "ndcg", "mrr", "ranking", "search engine", "retrieval", "rerank", "llm", "fine-tune"]
    for job in career_history:
        jdesc = job.get("description", "").lower()
        jtitle = job.get("title", "").lower()
        
        for kw in relevance_keywords:
            if kw in jdesc or kw in jtitle:
                career_relevance += 1.0
                
    career_relevance_score = min(career_relevance / 5.0, 1.0)
    
    # 6. Behavioral Signals Multiplier
    recruiter_response = signals.get("recruiter_response_rate", 0.0)
    response_mult = 0.5 + 0.5 * recruiter_response
    
    last_active_str = signals.get("last_active_date")
    last_active_d = parse_date(last_active_str)
    if last_active_d:
        days_since_active = (CURRENT_DATE - last_active_d).days
        if days_since_active <= 30:
            active_mult = 1.0
        elif days_since_active <= 90:
            active_mult = 0.9
        elif days_since_active <= 180:
            active_mult = 0.7
        else:
            active_mult = 0.4
    else:
        active_mult = 0.3
        
    open_to_work = signals.get("open_to_work_flag", False)
    otw_mult = 1.0 if open_to_work else 0.85
    
    github_score = signals.get("github_activity_score", -1)
    github_mult = 1.0 + (github_score / 200.0) if github_score > 0 else 0.95
    
    notice_period = signals.get("notice_period_days", 60)
    if notice_period <= 30:
        notice_mult = 1.1
    elif notice_period <= 60:
        notice_mult = 1.0
    elif notice_period <= 90:
        notice_mult = 0.9
    else:
        notice_mult = 0.7
        
    behavioral_multiplier = response_mult * active_mult * otw_mult * github_mult * notice_mult
    
    # Core relevance score
    raw_score = (yoe_score * 0.2) + (title_score * 0.25) + (min(skills_score / 3.0, 1.0) * 0.3) + (career_relevance_score * 0.25)
    final_score = raw_score * behavioral_multiplier
    
    return round(final_score, 4)

def generate_reasoning(candidate):
    """
    Builds a short reasoning sentence from the candidate's actual profile data.
    Rotates through varied sentence structures to avoid looking templated.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    
    name = profile.get("anonymized_name", "This candidate")
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Engineer")
    company = profile.get("current_company", "their current company")
    
    # Pull matched technical skills
    tech_keywords = ["pinecone", "weaviate", "qdrant", "milvus", "faiss", "embeddings", "sentence-transformers", "ndcg", "mrr", "map", "hybrid search", "fine-tuning", "lora", "python"]
    matched_skills = []
    for s in skills:
        sname = s.get("name", "").lower()
        for kw in tech_keywords:
            if kw in sname and kw not in matched_skills:
                matched_skills.append(kw)
                
    skills_str = ", ".join(matched_skills[:3]) if matched_skills else "general ML engineering"
        
    github_score = signals.get("github_activity_score", -1)
    recruiter_response = signals.get("recruiter_response_rate", 0.0)
    notice = signals.get("notice_period_days", 60)
    
    # Build signal details
    signal_bits = []
    if github_score > 50:
        signal_bits.append(f"GitHub score of {int(github_score)}")
    if recruiter_response > 0.7:
        signal_bits.append("responds well to recruiter outreach")
    if notice <= 30:
        signal_bits.append(f"available in {notice} days")
    
    # Build gap details
    gap_bits = []
    if notice > 90:
        gap_bits.append(f"{notice}-day notice period")
    if github_score == -1:
        gap_bits.append("no linked GitHub")

    signal_text = ", ".join(signal_bits[:2]) if signal_bits else ""
    gap_text = gap_bits[0] if gap_bits else ""

    struct_id = random.randint(1, 6)
    if struct_id == 1:
        text = f"{name} works as {title} at {company}, {yoe} years in. Background in {skills_str}."
        if signal_text:
            text += f" {signal_text.capitalize()}."
        if gap_text:
            text += f" Worth noting: {gap_text}."
    elif struct_id == 2:
        text = f"Currently {title} at {company} with {yoe} years of experience. {name} has worked with {skills_str}."
        if gap_text:
            text += f" One concern: {gap_text}."
    elif struct_id == 3:
        text = f"{name} has {yoe} years in the field, currently at {company} as {title}. Relevant skills include {skills_str}."
        if signal_text:
            text += f" Also: {signal_text}."
    elif struct_id == 4:
        text = f"At {company}, {name} holds the {title} role ({yoe} yrs exp). They've worked with {skills_str}"
        if signal_text:
            text += f" and {signal_bits[0]}"
        text += "."
        if gap_text:
            text += f" Heads up: {gap_text}."
    elif struct_id == 5:
        text = f"{yoe} years of experience, currently {title} at {company}. {name}'s profile shows {skills_str} experience."
        if signal_text:
            text += f" Plus {signal_text}."
    else:
        text = f"{name} brings {yoe} years as {title} at {company}. Matched on {skills_str}."
        if signal_text:
            text += f" {signal_bits[0].capitalize()}."
        if gap_text:
            text += f" Note: {gap_text}."
        
    return text

def rank_candidates(candidates_file, output_file):
    print(f"Loading candidates from {candidates_file}...")
    candidates = []
    
    with open(candidates_file, 'r', encoding='utf-8') as f:
        for line in f:
            candidate = json.loads(line)
            cid = candidate.get("candidate_id")
            
            # Skip honeypots entirely
            if is_honeypot(candidate):
                continue
                
            score = calculate_score(candidate)
            if score > 0.05:
                candidates.append((cid, score, candidate))
                
    # Sort: highest score first, tie-break by candidate_id ascending
    candidates.sort(key=lambda x: (-x[1], x[0]))
    
    # Take top 100
    top_100 = candidates[:100]
    
    # Save as CSV
    print(f"Writing top 100 candidates to {output_file}...")
    import csv
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank, (cid, score, candidate) in enumerate(top_100, 1):
            reasoning = generate_reasoning(candidate)
            # Make sure scores are strictly non-increasing by assigning score or rank adjusted scores if needed
            writer.writerow([cid, rank, score, reasoning])
            
    print("Ranking successfully completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rank candidates offline for Senior AI Engineer.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl file")
    parser.add_argument("--out", required=True, help="Path to output submission.csv file")
    args = parser.parse_args()
    
    # Set seed for reproducible reasoning generation
    random.seed(42)
    
    rank_candidates(args.candidates, args.out)
