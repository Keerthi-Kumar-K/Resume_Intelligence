from pathlib import Path


# ==========================================================
# BASE PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

TEMPLATES_DIR = BASE_DIR / "templates"


# ==========================================================
# DEFAULT INPUT / OUTPUT PATHS
# ==========================================================

# Change these defaults or pass command-line arguments to main.py.

DEFAULT_ATS_EXCEL = (
    BASE_DIR
    / "inputs"
    / "ATS_Result.xlsx"
)

DEFAULT_FILTERED_JD = (
    BASE_DIR
    / "inputs"
    / "Filtered_JDs.docx"
)

DEFAULT_OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
)


# ==========================================================
# ATS SCORE FILTERS
# ==========================================================

SCORE_THRESHOLD = 80.0

MIN_SCORE_TO_TAILOR = 45.0


# ==========================================================
# OLLAMA CONFIGURATION
# ==========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"

OLLAMA_MODEL = "qwen2.5:3b"

OLLAMA_TIMEOUT_SECONDS = 600

OLLAMA_KEEP_ALIVE = "30m"

OLLAMA_NUM_CTX = 4096

OLLAMA_NUM_PREDICT = 1200

OLLAMA_TEMPERATURE = 0.15


# ==========================================================
# RESUME TEMPLATE MAPPING
# ==========================================================
#
# Key:
# Exact PDF filename appearing in ATS Excel
#
# Value:
# Corresponding LaTeX template file
#
# ==========================================================

RESUME_TEMPLATE_MAP = {

    "Resume_Keerthi_Kumar_Azure_Databricks.pdf":
        TEMPLATES_DIR
        / "Resume_Keerthi_Kumar_Azure_Databricks.tex",

    "Resume_Keerthi_Kumar_Snowflake.pdf":
        TEMPLATES_DIR
        / "Resume_Keerthi_Kumar_Snowflake.tex",

    "Resume_Keerthi_Kumar_Karani_Informatica_Abinitio.pdf":
        TEMPLATES_DIR
        / "Resume_Keerthi_Kumar_Karani_Informatica_Abinitio.tex",
}


# ==========================================================
# EVIDENCE FILE
# ==========================================================

EVIDENCE_FILE = (
    BASE_DIR
    / "data"
    / "resume_evidence.json"
)


# ==========================================================
# LATEX COMPILER
# ==========================================================
#
# MiKTeX and TeX Live commonly include latexmk.
#
# ==========================================================

LATEX_COMMAND = [
    "latexmk",
    "-pdf",
    "-interaction=nonstopmode",
    "-halt-on-error",
]


# ==========================================================
# TAILORING LIMITS
# ==========================================================
#
# The first version updates only:
#
# - Professional Summary
# - Technical Skills
# - Latest Experience
# - Second-Latest Experience
#
# ==========================================================

MAX_SUMMARY_BULLETS = 7

MAX_EXPERIENCE_1_BULLETS = 10

MAX_EXPERIENCE_2_BULLETS = 9