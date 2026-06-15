# Redrob AI Candidate Ranking

**Team NoTone** - Prince Jain

Offline ranking system that picks the top 100 candidates for a **Senior AI Engineer, Founding Team** role from 100K profiles.

## How to run it

```bash
# Optional: set up a venv
python3 -m venv venv
source venv/bin/activate

# Run the ranker
python rank.py --candidates ./candidates.jsonl --out prince_jain.csv

# Validate format
python validate_submission.py prince_jain.csv
```

Takes about 10 seconds on an M2 MacBook, no GPU, no network calls.

---

## How it works

Four signal groups, all offline, all CPU.

### 1. Honeypot filtering

The dataset has ~42 synthetic profiles with impossible data. We catch them by checking:
- Job durations that exceed the calendar gap between start and end dates
- Single jobs longer than the candidate's total stated experience
- Skills marked "expert" with 0 months of recorded usage (3+ of these trips the filter)

Any candidate that trips one of these gets dropped before scoring.

### 2. Technical fit scoring (strongest signal)

Five sub-signals, each contributing independently:

**Self-reported skills** - We group the candidate's skill list into core (vector DBs, embeddings, semantic search), strong (fine-tuning, LoRA, eval metrics, retrieval), and support (Python, PyTorch, NLP). Proficiency, duration, and endorsement count all factor in, with diminishing returns past 24 months. Candidates who cover multiple categories get a combination bonus because the JD asks for the intersection of these areas.

**Verified assessments from Redrob** - The platform's own `skill_assessment_scores` field. These are actual test results, not self-reported. Categories like Information Retrieval, Vector Search, Learning to Rank, Embeddings, and Semantic Search map directly to the JD. A candidate with a 90/100 in Information Retrieval is weighted much more heavily than someone who just listed "information retrieval" as a skill. 94 of our top 100 have verified assessments.

**Career history keywords (recency-weighted)** - We scan job descriptions and titles for relevant terms (embedding, vector, retrieval, ranking, etc.), but weight the current job at 1.0x, one job back at 0.65x, two back at 0.35x. Someone doing vector DB work right now matters more than someone who did it three jobs ago.

**Profile summary mining** - The candidate's free-text summary often reveals experience that doesn't show up in structured fields. We scan for mentions of retrieval, vector, embedding, search, ranking, and specific tools like FAISS or Pinecone.

**LangChain-only filter** - The JD says not to surface candidates whose AI experience is mostly recent LangChain/LlamaIndex usage without deeper ML fundamentals. Candidates who list LangChain but lack PyTorch, TensorFlow, or actual vector DB tools get a heavy penalty.

### 3. Role fit scoring

| Signal | What we look at |
|---|---|
| YoE fit | 5-9 years = full, 4 or 10-12 = partial, outside = minimal |
| Title match | Recommendation Systems Engineer, Search Engineer, Senior AI/ML/NLP roles score highest |
| Company/industry | Product companies and AI/ML startups get a boost. Pure IT Services backgrounds get penalized. |
| Location | Pune/Noida preferred. Tier-1 Indian cities next. Non-India without willingness to relocate filtered out. |
| CV/Speech/Robotics | JD says to deprioritize CV, speech, robotics people without NLP/IR exposure. Applied as 0.3x multiplier. |
| Company size | Startup/mid-size companies (11-500) get a founding-team fit bonus. |

### 4. Availability and engagement (multiplier)

The raw score gets scaled by platform signals:
- **Recruiter response rate**: candidates who don't reply get scaled down
- **Login recency**: inactive accounts (180+ days) take a big hit. Active in last 14 days gets a small boost.
- **Notice period**: under 30 days gets a bump, over 90 gets penalized
- **GitHub activity**: score above 70 gets a 15% boost
- **Interview completion rate**: shows follow-through on hiring processes
- **Average response time**: candidates who reply within 24 hours get a 10% boost
- **Open to work flag**: off means 0.8x multiplier

### 5. Tiebreakers

Small additive bonuses for:
- Education tier (tier_1 institutions get +0.15)
- Saved by recruiters in last 30 days (market demand signal)
- Profile views received (visibility on platform)
- Relevant certifications (ML, Deep Learning, Cloud specializations)
- Profile completeness score
- Career trajectory (progressive ML/AI titles get a bonus, regressions get penalized)
- Job stability and title-chaser detection (JD explicitly flags people switching every 1.5 years for title bumps)
- Total endorsements received (network credibility)
- Verified email and phone (platform commitment)

## Output quality

| Metric | Value |
|---|---|
| Honeypots in top 100 | 0 |
| Average YoE in top 100 | 6.4 years |
| In ideal 5-9 YoE range | 78/100 |
| Candidates with verified assessments | 95/100 |
| Top industries | AI/ML (25), Fintech (13), Internet (8) |
| Score monotonic decreasing | Yes |
| Runtime (100K candidates) | ~10 seconds |

## Reasoning

Each candidate gets a 1-2 sentence explanation pulled from their actual profile data: name, title, company, YoE, matched skills, assessment scores, and signal values. Six sentence templates rotate to keep things varied. Every claim maps directly to a field in the candidate's JSON. No language model is called, so there's nothing made up.

## Files

| File | Purpose |
|---|---|
| `rank.py` | Ranking script. Single entry point. |
| `prince_jain.csv` | Final ranked output (100 candidates) |
| `submission_metadata.yaml` | Team info and methodology summary |
| `sandbox_notebook.ipynb` | Google Colab notebook (mandatory sandbox) |
| `approach_deck.pptx` | Methodology document on Redrob template |

## Sandbox

Open the [sandbox notebook](sandbox_notebook.ipynb) in Google Colab. It clones this repo, lets you upload a `candidates.jsonl` (or uses a built-in 20-candidate sample), runs the full pipeline, and shows the ranked output.

## Requirements

Python 3.9+ with standard library only. No external dependencies needed.
