# Redrob AI Candidate Ranking

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

That's it. Takes about 9 seconds on an M2 MacBook, no GPU, no network calls.

---

## How it works

Three stages, all offline, all CPU.

### 1. Honeypot filtering

The dataset has ~80 synthetic profiles with impossible data baked in. We catch them by checking:
- Job durations that exceed the calendar gap between start and end dates
- Single jobs longer than the candidate's total stated experience
- Skills marked "expert" with 0 months of recorded usage (3+ of these trips the filter)

Any candidate that trips one of these checks gets dropped before scoring.

### 2. Relevance scoring

We score what actually matters for this role:

| Signal | Weight | What we look at |
|---|---|---|
| Technical skills | 30% | Pinecone, Milvus, Qdrant, FAISS, embeddings, NDCG/MRR, fine-tuning (LoRA/PEFT) |
| Title match | 25% | Senior/Lead AI/ML/NLP roles get max score. Marketing, HR, Sales → filtered out. |
| Career keywords | 25% | Actual mentions of search, retrieval, vector, ranking work in job descriptions |
| YoE fit | 20% | 5–9 years is the sweet spot. Below 4 or above 12 gets penalized. |

Consulting-only backgrounds (TCS, Infosys, Wipro across every role) get heavily down-weighted. Non-India candidates who won't relocate are dropped.

### 3. Behavioral modifiers

The raw score gets multiplied by platform signals:
- **Recruiter response rate**: candidates who don't reply get scaled down
- **Login recency**: inactive accounts (180+ days) take a hit
- **Notice period**: under 30 days gets a bump, over 90 gets penalized
- **GitHub activity**: verified contributions add a small boost
- **Open to work flag**: off means 0.85x multiplier

Ties are broken by candidate_id ascending.

## Reasoning

Each candidate gets a 1-2 sentence explanation pulled from their actual profile data: title, company, YoE, matched skills, and signal values. We rotate between six sentence structures so the output doesn't look templated. Every claim maps back to something in the candidate's JSON.

## Files

| File | Purpose |
|---|---|
| `rank.py` | Ranking script. Single entry point. |
| `validate_submission.py` | Format checker from the hackathon bundle |
| `prince_jain.csv` | Final ranked output (100 candidates) |
| `submission_metadata.yaml` | Team info and methodology summary |
| `generate_pdf.py` | Builds the approach deck PDF |
| `approach_deck.pdf` | 10-slide methodology document |

## Requirements

Python 3.9+ with standard library only for ranking. `reportlab` needed only for PDF generation.

```
pip install reportlab
```
