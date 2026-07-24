# ==========================================================
# ATS V4 Configuration
# ==========================================================

from pathlib import Path

# ----------------------------------------------------------
# Project Paths
# ----------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

RESUME_DIR = ROOT / "resumes"
CACHE_DIR = ROOT / "cache"
MODEL_DIR = Path(r"C:\ATS\models")
OUTPUT_DIR = ROOT / "output"

# ----------------------------------------------------------
# Embedding Model
# ----------------------------------------------------------

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL_PATH = MODEL_DIR / EMBEDDING_MODEL

# ----------------------------------------------------------
# Similarity Thresholds
# ----------------------------------------------------------

SEMANTIC_THRESHOLD = 0.55
FUZZY_MATCH_THRESHOLD = 90

# ----------------------------------------------------------
# Scoring Weights
# ----------------------------------------------------------

WEIGHTS = {

    "required_skills":30,

    "preferred_skills":10,

    "semantic":15,

    "bm25":10,

    "experience":10,

    "domain":5,

    "role":10,

    "seniority":5,

    "certifications":5,

    "ecosystem":5,

    "penalty":-5

}

# ----------------------------------------------------------
# Cache Files
# ----------------------------------------------------------

RESUME_CACHE = CACHE_DIR / "resume_cache.pkl"

RESUME_EMBEDDINGS = CACHE_DIR / "resume_embeddings.pkl"

JD_EMBEDDINGS = CACHE_DIR / "jd_embeddings.pkl"

BM25_CACHE = CACHE_DIR / "bm25.pkl"

SKILL_CACHE = CACHE_DIR / "skill_cache.pkl"

# ----------------------------------------------------------
# Excel Sheets
# ----------------------------------------------------------

REPORT_SHEETS = [

    "Summary",

    "Ranking",

    "Missing Skills",

    "Skill Analysis",

    "Role Analysis",

    "Recommendations"

]