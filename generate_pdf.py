"""
Generates the approach deck PDF by overlaying our content onto the
official Redrob/H2S template slides.
"""
import os
from reportlab.lib.pagesizes import landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from pypdf import PdfReader, PdfWriter
from io import BytesIO

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "[PUB] India_runs_data_and_ai_challenge",
    "Idea Submission Template _ Redrob.pdf"
)
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "approach_deck.pdf")

# Template page dimensions (from extraction: 720 x 405 pts)
PW = 720
PH = 405

# Colors
C_TEXT = colors.HexColor("#2D3748")
C_HEAD = colors.HexColor("#1A365D")
C_SUB = colors.HexColor("#5B21B6")

def make_overlay_page(draw_func):
    """Create a single-page PDF in memory with our text overlay."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PW, PH))
    draw_func(c)
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def draw_bullet(c, x, y, text, font="Helvetica", size=10):
    """Draw a bullet point at (x, y), returns new y."""
    c.setFont(font, size)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "\u2022")
    c.setFillColor(C_TEXT)
    max_w = PW - x - 50
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        if c.stringWidth(test, font, size) < max_w:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    for i, line in enumerate(lines):
        c.drawString(x + 16, y - i * (size + 3), line)
    return y - len(lines) * (size + 3) - 3


def draw_body(c, x, y, text, font="Helvetica", size=10, max_w=None):
    """Draw wrapped body text."""
    if max_w is None:
        max_w = PW - x - 50
    c.setFont(font, size)
    c.setFillColor(C_TEXT)
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        if c.stringWidth(test, font, size) < max_w:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    for i, line in enumerate(lines):
        c.drawString(x, y - i * (size + 3), line)
    return y - len(lines) * (size + 3) - 2


# ---- SLIDE 1: Cover ----
def slide_1(c):
    y = PH - 270
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(C_HEAD)
    c.drawString(65, y, "Team Name :  NoTone")
    y -= 32
    c.drawString(65, y, "Team Leader Name :  Prince Jain")
    y -= 32
    c.setFont("Helvetica-Bold", 12)
    c.drawString(65, y, "Problem Statement :")
    y -= 18
    draw_body(c, 65, y,
        "Keyword matching surfaces keyword stuffers and misses qualified people "
        "who shipped real systems but don't list trendy buzzwords. We built a 46-signal "
        "offline ranker that verifies skills through assessments, catches fake profiles, "
        "and factors in platform activity and career trajectory.",
        size=11)


# ---- SLIDE 2: Solution Overview ----
def slide_2(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What is your proposed solution?")
    y -= 16
    y = draw_body(c, x, y,
        "A single Python script (rank.py) that reads 100K candidates, filters out "
        "synthetic honeypots, scores the rest against the JD using 46 data signals "
        "across 5 categories, and outputs a ranked CSV with per-candidate reasoning. "
        "Runs in 10 seconds on CPU. No GPU, no network, no API calls, stdlib only.")
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What differentiates your approach from traditional candidate matching?")
    y -= 16
    y = draw_bullet(c, x, y,
        "We avoid the keyword-matching trap the JD warns about. 3,946 candidates have "
        "6+ AI keywords but are HR Managers or Graphic Designers. None made our top 100.")
    y = draw_bullet(c, x, y,
        "Verified Redrob assessments (actual test scores) outweigh self-reported skills. "
        "95 of our top 100 have platform-verified assessment scores.")
    y = draw_bullet(c, x, y,
        "Reasoning connects to JD requirements and flags honest concerns. 78% mention "
        "production system context, 39% flag gaps like YoE outside range or high notice periods.")


# ---- SLIDE 3: JD Understanding ----
def slide_3(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What are the key requirements extracted from the JD?")
    y -= 16
    y = draw_bullet(c, x, y,
        "5-9 years of hands-on ML/AI work, ideally at product companies not consulting")
    y = draw_bullet(c, x, y,
        "Direct experience with vector DBs (Pinecone, Milvus, Qdrant, FAISS), embeddings, "
        "and search evaluation metrics (NDCG, MRR, MAP)")
    y = draw_bullet(c, x, y,
        "Shipped ranking, search, or recommendation systems to production users")
    y = draw_bullet(c, x, y,
        "Founding team culture: prefers shippers over pure researchers, penalizes "
        "title-chasers who switch jobs every 1.5 years for title bumps")
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Which traps does the JD explicitly warn about?")
    y -= 16
    y = draw_bullet(c, x, y,
        "Keyword stuffers: non-technical people with many AI keywords in skills")
    y = draw_bullet(c, x, y,
        "LangChain-only candidates: know the wrapper but not the underlying ML")
    y = draw_bullet(c, x, y,
        "CV/speech/robotics people without any NLP or information retrieval exposure")
    y = draw_bullet(c, x, y,
        "Architecture-only seniors who haven't written production code recently")


# ---- SLIDE 4: Ranking Methodology ----
def slide_4(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How does your system score and rank candidates? (46 signals)")
    y -= 16
    y = draw_body(c, x, y,
        "Five-stage pipeline: (1) Honeypot filter drops synthetic profiles, "
        "(2) Technical fit scores skills, assessments, and career keywords, "
        "(3) Role fit evaluates YoE, title, company, location, "
        "(4) Engagement multipliers adjust for availability, "
        "(5) Tiebreakers separate close scores.")
    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Technical Fit (12 signals):")
    y -= 14
    y = draw_body(c, x, y,
        "Self-reported skills (proficiency x duration x endorsements, grouped into core/strong/support), "
        "verified assessment scores from Redrob platform (56 mapped categories), "
        "recency-weighted career keywords, profile summary mining, "
        "LangChain-only detection, multi-category combination bonus.", size=9)
    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Role Fit (10 signals):")
    y -= 14
    y = draw_body(c, x, y,
        "YoE band scoring (5-9 ideal), title match (RecSys/Search/NLP highest), "
        "company tier (product > AI startup > IT services), industry, company size, "
        "location (Pune/Noida preferred), work mode, HR-tech domain bonus, "
        "architecture-only penalty, CV/speech/robotics filter.", size=9)
    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Engagement (7) + Tiebreakers (12):")
    y -= 14
    y = draw_body(c, x, y,
        "Response rate, login recency, open-to-work, notice period, GitHub, "
        "interview completion, avg response time. Tiebreakers: education tier/field, "
        "recruiter saves, profile views, completeness, certs, career trajectory, "
        "job stability, title-chaser detection, endorsements, search appearances, verified identity.", size=9)


# ---- SLIDE 5: Explainability & Data Validation ----
def slide_5(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How are ranking decisions explained?")
    y -= 16
    y = draw_body(c, x, y,
        "Each candidate gets a 1-2 sentence explanation pulled from their profile: name, "
        "title, company, YoE, matched skills, whether they shipped a search/recommendation "
        "system, assessment scores, and platform signals. Six sentence templates rotate. "
        "78% explicitly connect to JD requirements. 39% flag honest concerns.")
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How do you prevent hallucinations?")
    y -= 16
    y = draw_body(c, x, y,
        "Reasoning is assembled programmatically from parsed JSON fields. No language "
        "model is called, so there's no way for a skill or employer to appear in the "
        "reasoning that isn't in the actual data.")
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How do you handle suspicious profiles?")
    y -= 16
    y = draw_body(c, x, y,
        "The honeypot filter checks three things: expert skills with zero usage duration "
        "(3+ triggers exclusion), job durations exceeding total stated YoE, and job durations "
        "that don't match calendar math between start and end dates. 42 profiles caught, "
        "0 in our top 100.")


# ---- SLIDE 6: End-to-End Workflow ----
def slide_6(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Complete workflow from input to ranked output:")
    y -= 22

    steps = [
        ("1. Load data", "Stream-reads candidates.jsonl line by line. Low memory."),
        ("2. Filter honeypots", "Drops 42 profiles with timeline or skill contradictions."),
        ("3. Hard filters", "Removes non-tech roles, wrong country, CV/speech-only."),
        ("4. Score tech fit", "Skills, assessments, career keywords, summary mining."),
        ("5. Score role fit", "YoE, title, company, industry, location, HR-tech bonus."),
        ("6. Apply multipliers", "Response rate, recency, notice, GitHub, completion rate."),
        ("7. Add tiebreakers", "Education, trajectory, stability, endorsements, certs."),
        ("8. Sort and rank", "Descending by score. Ties broken by candidate_id."),
        ("9. Generate reasoning", "JD-connected, concern-flagging, 6 template rotation."),
        ("10. Write CSV", "Validated output with 100 ranked candidates."),
    ]
    for label, desc in steps:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(C_HEAD)
        c.drawString(x, y, label)
        c.setFont("Helvetica", 9)
        c.setFillColor(C_TEXT)
        c.drawString(x + 120, y, desc)
        y -= 16


# ---- SLIDE 7: System Architecture ----
def slide_7(c):
    x_center = PW / 2
    y = PH - 100

    blocks = [
        "candidates.jsonl (100K profiles, streamed line-by-line)",
        "Honeypot filter (timeline checks, skill contradictions) -> 42 dropped",
        "Hard filters (non-tech, wrong country, CV/speech) -> 55K filtered",
        "46-signal scoring (tech fit + role fit + HR-tech + assessments)",
        "Engagement multipliers (response rate, recency, GitHub, notice)",
        "Tiebreakers (education, trajectory, stability, endorsements)",
        "Sort desc, generate reasoning, write prince_jain.csv (top 100)",
    ]

    for i, block in enumerate(blocks):
        bw = 470
        bh = 20
        bx = x_center - bw / 2
        c.setStrokeColor(C_SUB)
        c.setFillColor(colors.HexColor("#F5F3FF"))
        c.roundRect(bx, y - bh, bw, bh, 4, fill=1, stroke=1)
        c.setFillColor(C_HEAD)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x_center, y - bh + 6, block)
        y -= bh + 4

        if i < len(blocks) - 1:
            c.setStrokeColor(C_SUB)
            c.setLineWidth(1.5)
            c.line(x_center, y + 4, x_center, y - 3)
            c.line(x_center - 3, y, x_center, y - 3)
            c.line(x_center + 3, y, x_center, y - 3)
            y -= 6


# ---- SLIDE 8: Results & Performance ----
def slide_8(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What results demonstrate ranking quality?")
    y -= 16
    y = draw_bullet(c, x, y,
        "Top 10: 8 out of 10 are in the ideal 6-8 YoE range. All have shipped "
        "search, ranking, or recommendation systems. Companies include CRED, Meta, "
        "Paytm, Netflix, Zomato, Genpact AI, Aganitha, Sarvam AI.")
    y = draw_bullet(c, x, y,
        "95 of 100 have verified Redrob assessment scores. Average YoE is 6.4 years. "
        "24 from AI/ML industry, 13 from Fintech, 9 from Internet companies.")
    y = draw_bullet(c, x, y,
        "Zero honeypots in the output. Zero keyword stuffers (the dataset has 3,946). "
        "Zero CV/speech/robotics people without NLP/IR crossover.")
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Runtime and compute?")
    y -= 16
    y = draw_bullet(c, x, y,
        "~10 seconds end-to-end for 100K candidates. Under 15 MB memory.")
    y = draw_bullet(c, x, y,
        "Fully offline, no GPU, passes validate_submission.py with zero errors.")


# ---- SLIDE 9: Technologies Used ----
def slide_9(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What technologies were used and why?")
    y -= 16
    y = draw_bullet(c, x, y,
        "Python stdlib (json, csv, datetime, argparse, random): The ranking step "
        "has zero external dependencies. Nothing to install, works on any Python 3.9+.")
    y = draw_bullet(c, x, y,
        "Type-hinted code with module docstring. All functions documented. "
        "22 iterative git commits across 3 development days.")
    y = draw_bullet(c, x, y,
        "ReportLab + pypdf: Only used for this PDF, not part of the ranking pipeline.")
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Why no ML model or LLM?")
    y -= 16
    y = draw_body(c, x, y,
        "Without labeled training data, a model would be fitting noise. Hand-crafted "
        "rules grounded in the JD's explicit criteria are more transparent and defensible. "
        "Every scoring decision maps to something the JD says.")


# ---- SLIDE 10: Submission Assets ----
def slide_10(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Submission assets:")
    y -= 22

    assets = [
        ("GitHub repo:", "https://github.com/princejain756/Data-AiChallengeHack2skill"),
        ("Sandbox:", "sandbox_notebook.ipynb (Google Colab ready)"),
        ("Ranked output:", "prince_jain.csv (100 candidates, validated)"),
        ("Metadata:", "submission_metadata.yaml"),
        ("This deck:", "approach_deck.pdf (10 slides on official template)"),
        ("Run command:", "python rank.py --candidates ./candidates.jsonl --out output.csv"),
    ]
    for label, value in assets:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(C_HEAD)
        c.drawString(x, y, label)
        c.setFont("Helvetica", 10)
        c.setFillColor(C_TEXT)
        c.drawString(x + 115, y, value)
        y -= 20

    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Signal count: 46 scoring signals + 3 honeypot checks + 6 reasoning templates")


# ---- SLIDE 11: Thank You (no overlay needed) ----
def slide_11(c):
    pass  # Template already has the "THANK YOU" branding


def build_pdf():
    template = PdfReader(TEMPLATE_PATH)
    writer = PdfWriter()

    slide_funcs = [
        slide_1, slide_2, slide_3, slide_4, slide_5,
        slide_6, slide_7, slide_8, slide_9, slide_10, slide_11
    ]

    for i, page in enumerate(template.pages):
        if i < len(slide_funcs):
            overlay = make_overlay_page(slide_funcs[i])
            page.merge_page(overlay)
        writer.add_page(page)

    with open(OUTPUT_PATH, "wb") as f:
        writer.write(f)

    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
