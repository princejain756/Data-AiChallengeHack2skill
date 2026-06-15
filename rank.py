import json
import argparse
import csv
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
    Identifies synthetically anomalous profiles based on:
    1. Skills proficiency contradictions (expert with 0 duration).
    2. Job durations exceeding total stated years of experience.
    3. Job durations exceeding the calendar time between start and end dates.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])

    # 1. Expert skills with 0 months used
    expert_zero = [s for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 0]
    if len(expert_zero) >= 3:
        return True

    # 2. Job duration exceeds profile total YoE
    yoe = profile.get("years_of_experience", 0)
    yoe_months = yoe * 12
    for job in career_history:
        duration = job.get("duration_months", 0)
        if duration > yoe_months + 6:
            return True

        # 3. Job duration exceeds calendar range
        start_d = parse_date(job.get("start_date"))
        end_d = parse_date(job.get("end_date")) if job.get("end_date") else None
        if start_d:
            ref_end = end_d if end_d else CURRENT_DATE
            cal_months = (ref_end.year - start_d.year) * 12 + (ref_end.month - start_d.month)
            if duration > cal_months + 12:
                return True

    return False


# ---- SCORING CONSTANTS ----

# JD target skills grouped by importance
CORE_SKILLS = ["pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
               "elasticsearch", "embeddings", "sentence-transformers", "semantic search",
               "vector search", "bge", "e5"]
STRONG_SKILLS = ["fine-tuning", "lora", "qlora", "peft", "rag", "reranking",
                 "ndcg", "mrr", "map", "a/b testing", "evaluation", "learning to rank",
                 "information retrieval", "hybrid search"]
SUPPORT_SKILLS = ["python", "pytorch", "tensorflow", "transformers", "hugging face",
                  "langchain", "llm", "nlp", "deep learning"]

# Redrob skill assessment categories grouped by JD relevance
ASSESS_CORE = {"Information Retrieval", "Vector Search", "Semantic Search",
               "Learning to Rank", "Embeddings", "FAISS"}
ASSESS_STRONG = {"Fine-tuning LLMs", "RAG", "PEFT", "LoRA", "QLoRA",
                 "Sentence Transformers", "NLP"}
ASSESS_SUPPORT = {"LLMs", "Python", "PyTorch", "TensorFlow", "Deep Learning",
                  "Machine Learning", "Haystack", "BM25", "Elasticsearch",
                  "OpenSearch", "Pinecone", "Weaviate", "Milvus", "Qdrant"}

# Known product/AI companies (boost)
PRODUCT_COMPANIES = {
    "google", "microsoft", "meta", "apple", "amazon", "nvidia", "netflix",
    "uber", "linkedin", "twitter", "x", "salesforce", "adobe", "oracle",
    "flipkart", "swiggy", "zomato", "paytm", "razorpay", "cred",
    "phonepe", "freshworks", "zoho", "meesho", "ola", "myntra",
    "sharechat", "dream11", "sarvam ai", "niramai", "aganitha",
    "hasura", "postman", "browserstack", "vedantu", "unacademy",
    "byju's", "byjus", "nykaa",
}

# IT Services / consulting (deprioritize)
IT_SERVICES_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "wipro technologies", "tata consultancy services", "hcl", "hcl technologies",
    "tech mahindra", "mindtree", "mphasis", "ltimindtree", "lti",
    "genpact", "genpact ai", "hexaware", "persistent systems",
}

# Non-technical role keywords (hard filter)
NON_TECH = ["marketing", "hr ", "human resources", "recruiter", "sales",
            "finance", "accountant", "operations manager", "customer support",
            "business development", "content writer", "copywriter", "graphic design"]


def calculate_score(candidate):
    """
    Multi-signal scoring for Senior AI Engineer (Founding Team) at Redrob.

    Signal groups and approximate contribution:
      A. Technical fit (skills + assessments + career keywords) ~ 45%
      B. Role fit (title + YoE + industry + company) ~ 25%
      C. Availability & engagement (behavioral signals) ~ 20%
      D. Tiebreakers (education, market signals) ~ 10%
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    signals = candidate.get("redrob_signals", {})
    education = candidate.get("education", [])

    current_title = profile.get("current_title", "").lower()
    headline = profile.get("headline", "").lower()
    current_company = profile.get("current_company", "").lower()
    current_industry = profile.get("current_industry", "").lower()

    # ========== HARD FILTERS ==========

    # Filter non-technical roles
    for kw in NON_TECH:
        if kw in current_title or kw in headline:
            return 0.0

    # Location gate
    country = profile.get("country", "").lower()
    willing_to_relocate = signals.get("willing_to_relocate", False)
    if country != "india" and not willing_to_relocate:
        return 0.0

    # JD: deprioritize CV/speech/robotics without NLP/IR exposure (line 49)
    cv_speech_titles = ["computer vision", "robotics", "speech", "image processing",
                        "autonomous", "perception"]
    nlp_ir_keywords = ["nlp", "search", "retrieval", "ranking", "recommendation",
                       "embedding", "vector", "language model", "text"]
    is_cv_speech = any(kw in current_title or kw in headline for kw in cv_speech_titles)
    has_nlp_ir = any(kw in current_title or kw in headline for kw in nlp_ir_keywords)
    cv_penalty = 0.3 if (is_cv_speech and not has_nlp_ir) else 1.0

    # ========== A. TECHNICAL FIT (max ~4.5) ==========

    # A1. Self-reported skills (proficiency x duration, grouped by category)
    skill_cats = {"core": 0.0, "strong": 0.0, "support": 0.0}
    prof_weights = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.9, "expert": 1.2}

    for s in skills:
        sname = s.get("name", "").lower()
        prof = s.get("proficiency", "beginner")
        duration = s.get("duration_months", 0)
        endorsements = s.get("endorsements", 0)
        pw = prof_weights.get(prof, 0.3)
        # Endorsements boost credibility of self-reported skills
        endorse_boost = 1.0 + min(endorsements, 20) * 0.01
        depth = pw * min(duration / 24.0, 2.0) * endorse_boost

        for kw in CORE_SKILLS:
            if kw in sname:
                skill_cats["core"] = max(skill_cats["core"], depth)
                break
        for kw in STRONG_SKILLS:
            if kw in sname:
                skill_cats["strong"] = max(skill_cats["strong"], depth)
                break
        for kw in SUPPORT_SKILLS:
            if kw in sname:
                skill_cats["support"] = max(skill_cats["support"], depth)
                break

    # Count distinct skill categories hit (for combination bonus)
    cats_hit = sum(1 for v in skill_cats.values() if v > 0)
    self_skill_score = (skill_cats["core"] * 1.5 +
                        skill_cats["strong"] * 1.0 +
                        skill_cats["support"] * 0.5)
    # Combination bonus: having multiple relevant categories is more valuable
    if cats_hit >= 3:
        self_skill_score *= 1.3
    elif cats_hit >= 2:
        self_skill_score *= 1.15

    # A2. Verified skill assessments from Redrob (much stronger signal)
    assess_scores = signals.get("skill_assessment_scores", {})
    assess_val = 0.0
    assess_count = 0
    for cat, score in assess_scores.items():
        if cat in ASSESS_CORE:
            assess_val += (score / 100.0) * 2.0
            assess_count += 1
        elif cat in ASSESS_STRONG:
            assess_val += (score / 100.0) * 1.2
            assess_count += 1
        elif cat in ASSESS_SUPPORT:
            assess_val += (score / 100.0) * 0.5
            assess_count += 1

    # Bonus for having multiple relevant assessments
    if assess_count >= 3:
        assess_val *= 1.2
    elif assess_count >= 2:
        assess_val *= 1.1

    # A3. Career history keyword relevance (recency-weighted)
    relevance_keywords = [
        "embedding", "vector", "pinecone", "weaviate", "qdrant", "milvus",
        "faiss", "hybrid search", "ndcg", "mrr", "ranking", "search engine",
        "retrieval", "rerank", "llm", "fine-tune", "fine-tuning", "rag",
        "semantic search", "similarity", "recommendation", "knowledge graph",
        "information retrieval", "query", "candidate matching",
    ]

    career_score = 0.0
    # Sort by start_date descending so we can weight by recency
    sorted_jobs = sorted(career_history,
                         key=lambda j: j.get("start_date", "1900-01-01"),
                         reverse=True)
    for idx, job in enumerate(sorted_jobs):
        jdesc = job.get("description", "").lower()
        jtitle = job.get("title", "").lower()
        text = jdesc + " " + jtitle

        hits = sum(1 for kw in relevance_keywords if kw in text)
        if hits == 0:
            continue

        # Recency weight: current/most recent = 1.0, then decays
        if idx == 0:
            recency = 1.0
        elif idx == 1:
            recency = 0.65
        elif idx == 2:
            recency = 0.35
        else:
            recency = 0.15

        career_score += min(hits, 6) * recency * 0.3

    career_score = min(career_score, 2.5)

    # A3b. HR-tech / marketplace domain bonus (JD: "Prior exposure to HR-tech,
    # recruiting tech, or marketplace products" is explicitly desired)
    hrtech_keywords = ["recruit", "hiring", "talent", "marketplace", "job board",
                       "hr-tech", "applicant tracking", "staffing", "candidate matching"]
    hrtech_bonus = 0.0
    for job in sorted_jobs:
        jdesc = job.get("description", "").lower()
        jind = job.get("industry", "").lower()
        if any(kw in jdesc or kw in jind for kw in hrtech_keywords):
            hrtech_bonus = 0.25  # domain experience bonus
            break

    # A4. Profile summary keyword mining
    summary = profile.get("summary", "").lower()
    summary_keywords = ["retrieval", "vector", "embedding", "search", "ranking",
                        "recommendation", "ndcg", "rerank", "semantic", "faiss",
                        "pinecone", "qdrant", "weaviate", "milvus"]
    summary_hits = sum(1 for kw in summary_keywords if kw in summary)
    summary_score = min(summary_hits * 0.12, 0.6)

    # A5. LangChain-only deprioritization (JD explicitly says to avoid these)
    skill_names_lower = [s.get("name", "").lower() for s in skills]
    all_skill_text = " ".join(skill_names_lower)
    has_langchain = "langchain" in all_skill_text or "llamaindex" in all_skill_text
    has_deeper_ml = any(kw in all_skill_text for kw in
                        ["pytorch", "tensorflow", "faiss", "pinecone", "fine-tuning",
                         "embeddings", "qdrant", "milvus", "weaviate", "sentence-transformers",
                         "ndcg", "mrr"])
    langchain_penalty = 1.0
    if has_langchain and not has_deeper_ml:
        langchain_penalty = 0.4  # heavy penalty for framework-only profiles

    # Combine technical fit
    tech_score = (min(self_skill_score, 2.5) + min(assess_val, 3.0) +
                  career_score + summary_score) * langchain_penalty

    # ========== B. ROLE FIT (max ~2.5) ==========

    # B1. YoE (5-9 ideal, 4 or 10-12 partial, outside minimal)
    yoe = profile.get("years_of_experience", 0)
    if 5.0 <= yoe <= 9.0:
        yoe_score = 1.0
    elif 4.0 <= yoe < 5.0 or 9.0 < yoe <= 12.0:
        yoe_score = 0.5
    elif 3.0 <= yoe < 4.0:
        yoe_score = 0.25
    else:
        yoe_score = 0.05

    # B2. Title match
    title_score = 0.0
    # Direct AI/ML/NLP/Search titles
    high_titles = ["ai engineer", "ml engineer", "machine learning engineer",
                   "nlp engineer", "search engineer", "retrieval",
                   "recommendation", "data scientist"]
    mid_titles = ["ai", "ml", "machine learning", "nlp", "search",
                  "data scientist", "backend engineer", "software engineer"]

    for t in high_titles:
        if t in current_title:
            title_score = max(title_score, 0.9)
    for t in mid_titles:
        if t in current_title:
            title_score = max(title_score, 0.6)

    # Seniority bonus
    if any(s in current_title for s in ["senior", "lead", "staff", "principal"]):
        title_score = min(title_score + 0.25, 1.0)
    elif "junior" in current_title or "intern" in current_title:
        title_score *= 0.4

    # JD line 29: "moved into 'architecture' or 'tech lead' roles" = deprioritize
    # They want someone who still writes code
    arch_only = ["architect", "director", "vp of", "head of", "chief"]
    if any(a in current_title for a in arch_only) and "engineer" not in current_title:
        title_score *= 0.5

    # B3. Company/industry quality
    company_score = 0.5  # default neutral

    # Pure consulting-only background
    all_companies = [j.get("company", "").lower() for j in career_history]
    if len(all_companies) > 0 and all(c in IT_SERVICES_COMPANIES for c in all_companies):
        company_score = 0.05
    elif current_company in PRODUCT_COMPANIES:
        company_score = 1.0
    elif current_industry in ("ai/ml", "saas", "fintech"):
        company_score = 0.85
    elif current_industry == "software":
        company_score = 0.7
    elif current_industry == "it services":
        # IT services but not all-consulting, partial penalty
        company_score = 0.3
    elif current_industry in ("manufacturing", "paper products", "conglomerate"):
        company_score = 0.15

    # Company size: startup/mid preferred for founding team
    company_size = profile.get("current_company_size", "")
    if company_size in ("11-50", "51-200", "201-500"):
        company_score = min(company_score + 0.15, 1.0)

    # B4. Location preference
    location = profile.get("location", "").lower()
    work_mode = signals.get("preferred_work_mode", "remote")
    target_cities = ["noida", "pune", "delhi", "gurgaon", "gurugram"]
    tier1_cities = ["mumbai", "hyderabad", "bangalore", "bengaluru", "chennai"]

    loc_score = 0.5
    if any(c in location for c in target_cities):
        loc_score = 1.0
    elif any(c in location for c in tier1_cities):
        loc_score = 0.8
    elif country == "india":
        loc_score = 0.6 if willing_to_relocate else 0.4

    if work_mode in ("hybrid", "onsite", "flexible"):
        loc_score = min(loc_score + 0.1, 1.0)

    role_fit = (yoe_score * 0.35 + title_score * 0.30 +
                company_score * 0.20 + loc_score * 0.15) * 2.5

    # B5. HR-tech domain bonus (additive, not part of weighted blend)
    role_fit += hrtech_bonus

    # ========== C. AVAILABILITY & ENGAGEMENT (multiplier 0.3 - 1.4) ==========

    # C1. Recruiter response rate
    rr = signals.get("recruiter_response_rate", 0.0)
    rr_mult = 0.5 + 0.5 * rr

    # C2. Login recency
    last_active_d = parse_date(signals.get("last_active_date"))
    if last_active_d:
        days_inactive = (CURRENT_DATE - last_active_d).days
        if days_inactive <= 14:
            active_mult = 1.05
        elif days_inactive <= 30:
            active_mult = 1.0
        elif days_inactive <= 90:
            active_mult = 0.85
        elif days_inactive <= 180:
            active_mult = 0.6
        else:
            active_mult = 0.3
    else:
        active_mult = 0.25

    # C3. Open to work
    otw = signals.get("open_to_work_flag", False)
    otw_mult = 1.0 if otw else 0.8

    # C4. Notice period
    notice = signals.get("notice_period_days", 60)
    if notice <= 15:
        notice_mult = 1.15
    elif notice <= 30:
        notice_mult = 1.1
    elif notice <= 60:
        notice_mult = 1.0
    elif notice <= 90:
        notice_mult = 0.85
    else:
        notice_mult = 0.6

    # C5. GitHub activity
    gh = signals.get("github_activity_score", -1)
    if gh > 70:
        gh_mult = 1.15
    elif gh > 40:
        gh_mult = 1.08
    elif gh > 10:
        gh_mult = 1.0
    elif gh >= 0:
        gh_mult = 0.95
    else:
        gh_mult = 0.9

    # C6. Interview completion rate (follows through on processes)
    icr = signals.get("interview_completion_rate", 0.5)
    icr_mult = 0.7 + 0.3 * icr

    # C7. Average response time (faster = more engaged)
    resp_time = signals.get("avg_response_time_hours", 150)
    if resp_time <= 24:
        resp_mult = 1.1
    elif resp_time <= 72:
        resp_mult = 1.05
    elif resp_time <= 150:
        resp_mult = 1.0
    else:
        resp_mult = 0.9

    engagement_mult = (rr_mult * active_mult * otw_mult * notice_mult *
                       gh_mult * icr_mult * resp_mult)

    # ========== D. TIEBREAKERS (additive bonus 0 - 0.5) ==========

    tiebreak = 0.0

    # D1. Education tier
    best_tier = 5
    for e in education:
        tier_str = e.get("tier", "tier_4")
        try:
            tier_num = int(tier_str.replace("tier_", ""))
            best_tier = min(best_tier, tier_num)
        except:
            pass
    tier_bonus = {1: 0.15, 2: 0.08, 3: 0.03, 4: 0.0}.get(best_tier, 0.0)
    tiebreak += tier_bonus

    # D2. Market demand signals (social proof)
    saved = signals.get("saved_by_recruiters_30d", 0)
    if saved >= 10:
        tiebreak += 0.12
    elif saved >= 5:
        tiebreak += 0.06

    views = signals.get("profile_views_received_30d", 0)
    if views >= 30:
        tiebreak += 0.08
    elif views >= 15:
        tiebreak += 0.04

    # D3. Profile completeness
    completeness = signals.get("profile_completeness_score", 50)
    if completeness >= 90:
        tiebreak += 0.05

    # D4. Certifications in relevant areas
    certs = candidate.get("certifications", [])
    relevant_cert_keywords = ["ml", "machine learning", "deep learning", "nlp",
                              "ai", "data science", "cloud", "aws", "gcp"]
    cert_hits = 0
    for cert in certs:
        cname = cert.get("name", "").lower()
        if any(k in cname for k in relevant_cert_keywords):
            cert_hits += 1
    if cert_hits >= 2:
        tiebreak += 0.08
    elif cert_hits >= 1:
        tiebreak += 0.04

    # D5. Career trajectory analysis
    ml_title_keywords = ["ai", "ml", "machine learning", "nlp", "search",
                         "retrieval", "data scientist", "recommendation"]
    seniority_levels = {"intern": 0, "junior": 1, "associate": 2, "": 3,
                        "mid": 3, "senior": 4, "lead": 5, "staff": 6,
                        "principal": 7, "director": 8, "vp": 9}

    trajectory_scores = []
    for job in sorted_jobs:
        jtitle = job.get("title", "").lower()
        is_ml = any(kw in jtitle for kw in ml_title_keywords)
        if not is_ml:
            continue
        lvl = 3  # default mid
        for prefix, val in seniority_levels.items():
            if prefix and prefix in jtitle:
                lvl = val
                break
        trajectory_scores.append(lvl)

    if len(trajectory_scores) >= 2:
        # Check if career shows upward progression
        if trajectory_scores[0] > trajectory_scores[-1]:
            tiebreak += 0.12  # progressed upward
        elif trajectory_scores[0] < trajectory_scores[-1]:
            tiebreak -= 0.05  # regressed

    # D6. Job stability (founding team wants committed people)
    # JD line 46: "switching companies every 1.5 years" = disqualifier
    if len(career_history) >= 3:
        avg_duration = sum(j.get("duration_months", 0) for j in career_history) / len(career_history)
        if avg_duration < 18:
            # Title-chaser check: did they get progressive titles from switching?
            unique_companies = len(set(j.get("company", "").lower() for j in career_history))
            if unique_companies >= len(career_history) - 1 and avg_duration < 15:
                tiebreak -= 0.15  # classic title-chaser pattern
            else:
                tiebreak -= 0.06
        elif avg_duration >= 30:
            tiebreak += 0.06  # stable tenure bonus

    # D7. Endorsements received (network credibility)
    total_endorsements = signals.get("endorsements_received", 0)
    if total_endorsements >= 50:
        tiebreak += 0.06
    elif total_endorsements >= 20:
        tiebreak += 0.03

    # D8. Verified identity (platform commitment)
    if signals.get("verified_email", False) and signals.get("verified_phone", False):
        tiebreak += 0.03

    # D9. Search appearances (market demand - recruiters are looking for this person)
    search_app = signals.get("search_appearance_30d", 0)
    if search_app >= 500:
        tiebreak += 0.08
    elif search_app >= 200:
        tiebreak += 0.04

    # D10. Education field of study (CS/AI/ML fields are more relevant for this role)
    cs_fields = {"computer science", "computer engineering", "artificial intelligence",
                 "machine learning", "data science", "information technology",
                 "electrical engineering", "electronics", "mathematics", "statistics"}
    for e in education:
        field = e.get("field_of_study", "").lower()
        if field in cs_fields:
            tiebreak += 0.04
            break

    final = (tech_score + role_fit) * engagement_mult * cv_penalty + tiebreak
    return round(final, 4)


def generate_reasoning(candidate):
    """
    Builds a short reasoning string from the candidate's actual data.
    Rotates through six structures to avoid looking templated.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})

    name = profile.get("anonymized_name", "This candidate")
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Engineer")
    company = profile.get("current_company", "their current company")

    # Matched technical skills
    tech_kw = ["pinecone", "weaviate", "qdrant", "milvus", "faiss",
               "embeddings", "sentence-transformers", "ndcg", "mrr",
               "hybrid search", "fine-tuning", "lora", "python",
               "semantic search", "rag", "vector search"]
    matched = []
    for s in skills:
        sname = s.get("name", "").lower()
        for kw in tech_kw:
            if kw in sname and kw not in matched:
                matched.append(kw)
    skills_str = ", ".join(matched[:3]) if matched else "general ML engineering"

    # Assessment highlights
    assess = signals.get("skill_assessment_scores", {})
    assess_relevant = {k: v for k, v in assess.items()
                       if k in ASSESS_CORE | ASSESS_STRONG}
    assess_str = ""
    if assess_relevant:
        top_assess = sorted(assess_relevant.items(), key=lambda x: -x[1])[:2]
        assess_str = ", ".join(f"{k} ({v:.0f}/100)" for k, v in top_assess)

    github_score = signals.get("github_activity_score", -1)
    rr = signals.get("recruiter_response_rate", 0.0)
    notice = signals.get("notice_period_days", 60)

    # Signal bits
    sig_bits = []
    if github_score > 50:
        sig_bits.append(f"GitHub score of {int(github_score)}")
    if rr > 0.7:
        sig_bits.append("responds well to recruiter outreach")
    if notice <= 30:
        sig_bits.append(f"available in {notice} days")
    if assess_str:
        sig_bits.append(f"assessed in {assess_str}")

    gap_bits = []
    if notice > 90:
        gap_bits.append(f"{notice}-day notice period")
    if github_score == -1:
        gap_bits.append("no linked GitHub")

    sig_text = ", ".join(sig_bits[:2]) if sig_bits else ""
    gap_text = gap_bits[0] if gap_bits else ""

    sid = random.randint(1, 6)
    if sid == 1:
        text = f"{name} works as {title} at {company}, {yoe} years in. Background in {skills_str}."
        if sig_text:
            text += f" {sig_text.capitalize()}."
        if gap_text:
            text += f" Worth noting: {gap_text}."
    elif sid == 2:
        text = f"Currently {title} at {company} with {yoe} years of experience. {name} has worked with {skills_str}."
        if gap_text:
            text += f" One concern: {gap_text}."
    elif sid == 3:
        text = f"{name} has {yoe} years in the field, currently at {company} as {title}. Relevant skills include {skills_str}."
        if sig_text:
            text += f" Also: {sig_text}."
    elif sid == 4:
        text = f"At {company}, {name} holds the {title} role ({yoe} yrs exp). They've worked with {skills_str}"
        if sig_text:
            text += f" and {sig_bits[0]}"
        text += "."
        if gap_text:
            text += f" Heads up: {gap_text}."
    elif sid == 5:
        text = f"{yoe} years of experience, currently {title} at {company}. {name}'s profile shows {skills_str} experience."
        if sig_text:
            text += f" Plus {sig_text}."
    else:
        text = f"{name} brings {yoe} years as {title} at {company}. Matched on {skills_str}."
        if sig_text:
            text += f" {sig_bits[0].capitalize()}."
        if gap_text:
            text += f" Note: {gap_text}."

    return text


def rank_candidates(candidates_file, output_file):
    print(f"Loading candidates from {candidates_file}...")
    candidates = []
    honeypots = 0
    filtered = 0

    with open(candidates_file, 'r', encoding='utf-8') as f:
        for line in f:
            candidate = json.loads(line)
            cid = candidate.get("candidate_id")

            if is_honeypot(candidate):
                honeypots += 1
                continue

            score = calculate_score(candidate)
            if score > 0.1:
                candidates.append((cid, score, candidate))
            else:
                filtered += 1

    print(f"Honeypots dropped: {honeypots}")
    print(f"Low-relevance filtered: {filtered}")
    print(f"Candidates scored: {len(candidates)}")

    # Sort: highest score first, tie-break by candidate_id ascending
    candidates.sort(key=lambda x: (-x[1], x[0]))

    top_n = candidates[:100]
    output_count = len(top_n)

    print(f"Writing top {output_count} candidates to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank, (cid, score, candidate) in enumerate(top_n, 1):
            reasoning = generate_reasoning(candidate)
            writer.writerow([cid, rank, score, reasoning])

    print("Ranking complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer role.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Output CSV path")
    args = parser.parse_args()

    random.seed(42)
    rank_candidates(args.candidates, args.out)
