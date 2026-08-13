from pathlib import Path

# ============================================================
# PROJECT
# ============================================================

PROJECT_ROOT = Path.cwd()

OUTPUT_ROOT = PROJECT_ROOT / "outputs"

LOG_ROOT = PROJECT_ROOT / "logs"

OUTPUT_ROOT.mkdir(exist_ok=True)

LOG_ROOT.mkdir(exist_ok=True)

# ============================================================
# SCRAPER
# ============================================================

MAX_PAGES = 100

SCROLL_PAUSE = 2

PAGE_LOAD_WAIT = 5

HEADLESS = False

RETRY_COUNT = 2

# ============================================================
# DATA ROLE KEYWORDS
# ============================================================

DATA_ROLE_KEYWORDS = [

# ---------------------------
# Data Engineering
# ---------------------------

"data engineer",
"senior data engineer",
"principal data engineer",
"lead data engineer",

"etl developer",
"etl engineer",
"elt developer",
"elt engineer",

"big data engineer",

"data platform engineer",

"data pipeline engineer",

"lakehouse engineer",

"data warehouse engineer",

"analytics engineer",

# ---------------------------
# Snowflake
# ---------------------------

"snowflake developer",

"snowflake engineer",

"snowflake architect",

# ---------------------------
# Databricks
# ---------------------------

"databricks engineer",

"databricks developer",

"spark engineer",

"pyspark",

# ---------------------------
# BI
# ---------------------------

"bi developer",

"business intelligence",

"power bi",

"tableau",

"report developer",

"reporting analyst",

# ---------------------------
# Analytics
# ---------------------------

"data analyst",

"analytics analyst",

"business analyst",

"product analyst",

"data science",

"data scientist",

"machine learning engineer",

"ai engineer",

"ml engineer",

# ---------------------------
# Data Architecture
# ---------------------------

"data architect",

"cloud data engineer",

"azure data engineer",

"aws data engineer",

"gcp data engineer",

# ---------------------------
# Governance
# ---------------------------

"mdm",

"master data management",

"data governance",

"data quality",

"data steward",

"data modeler",

# ---------------------------
# Streaming
# ---------------------------

"kafka",

"kinesis",

"streaming",

"event streaming",

# ---------------------------
# Generic
# ---------------------------

"etl",

"elt",

"analytics",

"warehouse",

"lakehouse",

"data"

]