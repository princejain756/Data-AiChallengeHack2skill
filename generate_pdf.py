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


def draw_bullet(c, x, y, text, font="Helvetica", size=11):
    """Draw a bullet point at (x, y), returns new y."""
    c.setFont(font, size)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "\u2022")
    c.setFillColor(C_TEXT)
    # Handle line wrapping manually
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
    return y - len(lines) * (size + 3) - 4


def draw_body(c, x, y, text, font="Helvetica", size=11, max_w=None):
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
    c.drawString(65, y, "Team Name :  Prince Jain")
    y -= 32
    c.drawString(65, y, "Team Leader Name :  Prince Jain")
    y -= 32
    c.setFont("Helvetica-Bold", 12)
    c.drawString(65, y, "Problem Statement :")
    y -= 18
    draw_body(c, 65, y,
        "Keyword matching surfaces keyword stuffers and misses qualified people. "
        "It also can't tell if someone is available or interested. We built an offline "
        "ranker that checks real skills, catches fake profiles, and factors in platform activity.",
        size=11)


# ---- SLIDE 2: Solution Overview ----
def slide_2(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What is your proposed solution?")
    y -= 18
    y = draw_body(c, x, y,
        "A Python script that reads 100K candidate profiles, filters out synthetic fakes, "
        "scores the rest against the job description, adjusts for availability signals, and "
        "outputs a ranked CSV with per-candidate reasoning. Runs in about 9 seconds on CPU. "
        "No GPU, no network, no external API calls.")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What differentiates your approach from traditional candidate matching?")
    y -= 18
    y = draw_bullet(c, x, y,
        "We check recruiter response rates and login recency. A perfect skill match who "
        "hasn't been active in 6 months isn't useful for hiring.")
    y = draw_bullet(c, x, y,
        "We cross-check job timelines against calendar math. If someone claims 5 years at a "
        "role that started 18 months ago, the profile gets flagged and dropped.")
    y = draw_bullet(c, x, y,
        "Reasoning is built from actual profile fields, not generated text. Every claim "
        "in the output maps directly to a field in the candidate's JSON.")


# ---- SLIDE 3: JD Understanding ----
def slide_3(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What are the key requirements extracted from the JD?")
    y -= 18
    y = draw_bullet(c, x, y,
        "5 to 9 years of hands-on ML/AI work, ideally at product companies (not consulting-only)")
    y = draw_bullet(c, x, y,
        "Direct experience with vector databases (Pinecone, Milvus, Qdrant, FAISS), embeddings, "
        "and search evaluation metrics (NDCG, MRR, MAP)")
    y = draw_bullet(c, x, y,
        "Python fluency. Bonus for fine-tuning work (LoRA, PEFT). Filter out marketing, HR, "
        "sales, finance, ops roles. Pure academic researchers also deprioritized.")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Which candidate signals matter most?")
    y -= 18
    y = draw_bullet(c, x, y,
        "Recruiter response rate: are they engaging with outreach?")
    y = draw_bullet(c, x, y,
        "Timeline consistency: do the dates in their career history add up?")
    y = draw_bullet(c, x, y,
        "Login recency and GitHub activity: are they active on the platform?")


# ---- SLIDE 4: Ranking Methodology ----
def slide_4(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How does your system retrieve, score, and rank candidates?")
    y -= 18
    y = draw_body(c, x, y,
        "Three sequential offline steps: (1) Honeypot filter drops synthetic profiles, "
        "(2) Feature scoring evaluates relevance, (3) Behavioral multipliers adjust final weights.")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What heuristics are used?")
    y -= 18
    y = draw_bullet(c, x, y,
        "Technical skills match: 30% (vector DBs, embeddings, eval metrics, fine-tuning, Python)")
    y = draw_bullet(c, x, y,
        "Title relevance: 25% (Senior/Lead AI/ML/NLP roles score highest)")
    y = draw_bullet(c, x, y,
        "Career keywords: 25% (mentions of search, retrieval, vector, ranking in job descriptions)")
    y = draw_bullet(c, x, y,
        "YoE fit: 20% (5-9 years = full, 4 or 10-12 = partial, outside = minimal)")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How are signals combined?")
    y -= 18
    y = draw_body(c, x, y,
        "Raw score gets multiplied by: response rate (0.5 + 0.5 * RR), login recency "
        "(1.0 down to 0.4), open-to-work flag (1.0 or 0.85), notice period (up to 1.1x "
        "for <30 days), GitHub activity. Ties break on candidate_id ascending.")


# ---- SLIDE 5: Explainability & Data Validation ----
def slide_5(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How are ranking decisions explained?")
    y -= 18
    y = draw_body(c, x, y,
        "Each candidate gets a 1-2 sentence explanation pulled from their profile: name, "
        "title, company, YoE, matched skills, signal values like GitHub score or notice "
        "period. Six sentence templates rotate to keep things varied.")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How do you prevent hallucinations?")
    y -= 18
    y = draw_body(c, x, y,
        "There aren't any. Reasoning is assembled programmatically from parsed JSON "
        "fields. No language model is called, so there's no way for a skill or employer "
        "to appear in the reasoning that isn't in the actual data.")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "How do you handle suspicious profiles?")
    y -= 18
    y = draw_body(c, x, y,
        "The honeypot filter checks three things: expert skills with zero usage duration, "
        "job durations exceeding total stated YoE, and job durations that don't fit the "
        "calendar range. Any of these trips the filter and the candidate gets excluded.")


# ---- SLIDE 6: End-to-End Workflow ----
def slide_6(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Complete workflow from JD input to ranked output:")
    y -= 22

    steps = [
        ("1. Load data", "Stream-reads candidates.jsonl line by line. Low memory footprint."),
        ("2. Filter honeypots", "Drops profiles with timeline or skill-proficiency contradictions."),
        ("3. Score relevance", "Evaluates YoE, titles, skills, and career history keywords."),
        ("4. Apply modifiers", "Multiplies score by response rate, login recency, notice, GitHub."),
        ("5. Sort and rank", "Descending by score. Ties broken by candidate_id ascending."),
        ("6. Write output", "Generates per-candidate reasoning and writes validated CSV."),
    ]
    for label, desc in steps:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(C_HEAD)
        c.drawString(x, y, label)
        c.setFont("Helvetica", 10)
        c.setFillColor(C_TEXT)
        c.drawString(x + 130, y, desc)
        y -= 18


# ---- SLIDE 7: System Architecture ----
def slide_7(c):
    x_center = PW / 2
    y = PH - 110

    blocks = [
        "candidates.jsonl (100K profiles, streamed)",
        "Honeypot filter (timeline checks, skill contradictions)",
        "Feature scoring (YoE + titles + skills + career keywords)",
        "Behavioral multipliers (response rate, recency, notice, GitHub)",
        "Sort by score desc, tie-break on candidate_id",
        "prince_jain.csv (top 100 with reasoning)",
    ]

    for i, block in enumerate(blocks):
        # Draw box
        bw = 440
        bh = 22
        bx = x_center - bw / 2
        c.setStrokeColor(C_SUB)
        c.setFillColor(colors.HexColor("#F5F3FF"))
        c.roundRect(bx, y - bh, bw, bh, 4, fill=1, stroke=1)
        c.setFillColor(C_HEAD)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x_center, y - bh + 7, block)
        y -= bh + 6

        # Draw arrow between blocks
        if i < len(blocks) - 1:
            c.setStrokeColor(C_SUB)
            c.setLineWidth(1.5)
            c.line(x_center, y + 6, x_center, y - 4)
            # arrowhead
            c.line(x_center - 4, y, x_center, y - 4)
            c.line(x_center + 4, y, x_center, y - 4)
            y -= 8


# ---- SLIDE 8: Results & Performance ----
def slide_8(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What results demonstrate ranking quality?")
    y -= 18
    y = draw_bullet(c, x, y,
        "Top 10 are Senior AI/ML/NLP Engineers from product companies with real "
        "vector DB and search infrastructure experience, 5-9 years in, actively "
        "responding to recruiters.")
    y = draw_bullet(c, x, y,
        "Zero honeypots in the output. All synthetic profiles were caught by the filter.")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Runtime and compute?")
    y -= 18
    y = draw_bullet(c, x, y,
        "9 seconds end-to-end for 100K candidates on an M2 MacBook")
    y = draw_bullet(c, x, y,
        "Under 15 MB peak memory. Well within the 16 GB constraint.")
    y = draw_bullet(c, x, y,
        "Fully offline, no GPU, passes validate_submission.py with zero errors.")


# ---- SLIDE 9: Technologies Used ----
def slide_9(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "What technologies were used and why?")
    y -= 18
    y = draw_bullet(c, x, y,
        "Python stdlib (json, csv, datetime, argparse): The ranking step has zero "
        "external dependencies. Nothing to install, nothing to break, works on any "
        "Python 3.9+ environment.")
    y = draw_bullet(c, x, y,
        "ReportLab + pypdf: For generating this PDF using the official template. "
        "Only dependency outside stdlib, not part of the ranking pipeline.")
    y = draw_bullet(c, x, y,
        "Git: Version control with iterative commit history showing actual development "
        "progression.")


# ---- SLIDE 10: Submission Assets ----
def slide_10(c):
    x, y = 65, PH - 115
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(C_SUB)
    c.drawString(x, y, "Submission assets:")
    y -= 22

    assets = [
        ("GitHub repo:", "https://github.com/princejain756/Data-AiChallengeHack2skill"),
        ("Ranked output:", "prince_jain.csv (100 candidates, validated)"),
        ("Metadata:", "submission_metadata.yaml"),
        ("This deck:", "approach_deck.pdf (10 slides on official template)"),
        ("Entry point:", "python rank.py --candidates ./candidates.jsonl --out ./prince_jain.csv"),
    ]
    for label, value in assets:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(C_HEAD)
        c.drawString(x, y, label)
        c.setFont("Helvetica", 10)
        c.setFillColor(C_TEXT)
        c.drawString(x + 110, y, value)
        y -= 20


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
