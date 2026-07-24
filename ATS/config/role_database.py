# ==========================================================
# ATS V4.0
# Role Knowledge Base
# ==========================================================

ROLE_DATABASE = {

    "data engineer": {

        "title_aliases": [
            "data engineer",
            "senior data engineer",
            "lead data engineer",
            "data engineering lead",
            "data pipeline engineer",
            "big data engineer",
        ],

        "required_skills": [
            "python",
            "sql",
            "etl",
            "data pipelines",
        ],

        "preferred_skills": [
            "spark",
            "pyspark",
            "airflow",
            "databricks",
            "snowflake",
            "aws",
            "azure",
            "gcp",
            "kafka",
            "dbt",
        ],

        "keywords": [
            "data engineering",
            "data pipeline",
            "data ingestion",
            "batch processing",
            "stream processing",
            "data lake",
            "data warehouse",
        ],

        "excluded_keywords": [
            "frontend",
            "mobile developer",
            "network engineer",
            "security analyst",
        ],
    },

    "databricks engineer": {

        "title_aliases": [
            "databricks engineer",
            "azure databricks engineer",
            "databricks developer",
            "databricks data engineer",
            "pyspark engineer",
            "databricks architect",
        ],

        "required_skills": [
            "databricks",
            "spark",
            "pyspark",
            "python",
            "sql",
        ],

        "preferred_skills": [
            "delta lake",
            "unity catalog",
            "azure data factory",
            "adls",
            "mlflow",
            "delta live tables",
            "medallion architecture",
        ],

        "keywords": [
            "lakehouse",
            "bronze silver gold",
            "medallion architecture",
            "spark optimization",
            "delta tables",
        ],

        "excluded_keywords": [
            "machine learning scientist",
            "frontend",
            "salesforce",
        ],
    },

    "snowflake engineer": {

        "title_aliases": [
            "snowflake engineer",
            "snowflake developer",
            "snowflake data engineer",
            "snowflake administrator",
            "snowflake architect",
        ],

        "required_skills": [
            "snowflake",
            "sql",
            "data warehouse",
        ],

        "preferred_skills": [
            "snowpipe",
            "streams",
            "tasks",
            "dbt",
            "python",
            "aws",
            "azure",
            "terraform",
        ],

        "keywords": [
            "virtual warehouse",
            "time travel",
            "zero copy cloning",
            "micro partitions",
            "snowflake optimization",
        ],

        "excluded_keywords": [
            "frontend",
            "network engineer",
            "salesforce administrator",
        ],
    },

    "etl developer": {

        "title_aliases": [
            "etl developer",
            "etl engineer",
            "senior etl developer",
            "etl consultant",
            "data integration developer",
        ],

        "required_skills": [
            "etl",
            "sql",
        ],

        "preferred_skills": [
            "informatica",
            "ab initio",
            "datastage",
            "talend",
            "ssis",
            "control-m",
            "shell",
            "oracle",
            "teradata",
        ],

        "keywords": [
            "data integration",
            "source to target mapping",
            "batch processing",
            "etl workflows",
            "data transformation",
        ],

        "excluded_keywords": [
            "frontend",
            "mobile application",
            "network support",
        ],
    },

    "business intelligence engineer": {

        "title_aliases": [
            "business intelligence engineer",
            "bi engineer",
            "business intelligence developer",
            "bi developer",
            "analytics engineer",
        ],

        "required_skills": [
            "sql",
            "business intelligence",
        ],

        "preferred_skills": [
            "power bi",
            "tableau",
            "looker",
            "dax",
            "data modeling",
            "snowflake",
            "dbt",
        ],

        "keywords": [
            "dashboard",
            "reporting",
            "semantic model",
            "data visualization",
            "business metrics",
        ],

        "excluded_keywords": [
            "frontend developer",
            "graphic designer",
            "network engineer",
        ],
    },

    "data analyst": {

        "title_aliases": [
            "data analyst",
            "senior data analyst",
            "business data analyst",
            "reporting analyst",
            "analytics analyst",
            "data management analyst",
            "data product analyst",
        ],

        "required_skills": [
            "sql",
            "data analysis",
        ],

        "preferred_skills": [
            "excel",
            "python",
            "power bi",
            "tableau",
            "statistics",
            "data visualization",
        ],

        "keywords": [
            "data analysis",
            "business insights",
            "reporting",
            "trend analysis",
            "data validation",
        ],

        "excluded_keywords": [
            "financial advisor",
            "network analyst",
            "security operations analyst",
        ],
    },

    "data scientist": {

        "title_aliases": [
            "data scientist",
            "senior data scientist",
            "machine learning scientist",
            "applied data scientist",
        ],

        "required_skills": [
            "python",
            "machine learning",
            "statistics",
        ],

        "preferred_skills": [
            "pandas",
            "numpy",
            "scikit-learn",
            "tensorflow",
            "pytorch",
            "spark",
            "sql",
            "mlflow",
        ],

        "keywords": [
            "predictive modeling",
            "feature engineering",
            "model training",
            "statistical modeling",
            "machine learning models",
        ],

        "excluded_keywords": [
            "data entry",
            "network scientist",
            "laboratory scientist",
        ],
    },

    "data architect": {

        "title_aliases": [
            "data architect",
            "enterprise data architect",
            "cloud data architect",
            "solution data architect",
            "data platform architect",
        ],

        "required_skills": [
            "data architecture",
            "data modeling",
            "sql",
        ],

        "preferred_skills": [
            "cloud architecture",
            "data warehouse",
            "data lake",
            "snowflake",
            "databricks",
            "aws",
            "azure",
            "gcp",
            "governance",
        ],

        "keywords": [
            "enterprise architecture",
            "solution design",
            "logical data model",
            "physical data model",
            "architecture standards",
        ],

        "excluded_keywords": [
            "application architect",
            "network architect",
            "security architect",
        ],
    },

    "data governance engineer": {

        "title_aliases": [
            "data governance engineer",
            "data governance analyst",
            "data governance specialist",
            "data quality engineer",
            "metadata analyst",
        ],

        "required_skills": [
            "data governance",
            "data quality",
            "metadata",
        ],

        "preferred_skills": [
            "data lineage",
            "data catalog",
            "collibra",
            "alation",
            "informatica axon",
            "informatica edc",
            "unity catalog",
            "master data management",
        ],

        "keywords": [
            "data stewardship",
            "business glossary",
            "data ownership",
            "data classification",
            "data quality rules",
        ],

        "excluded_keywords": [
            "cybersecurity governance",
            "network governance",
        ],
    },

    "mdm engineer": {

        "title_aliases": [
            "mdm engineer",
            "mdm developer",
            "master data management engineer",
            "mdm consultant",
            "reltio developer",
            "informatica mdm developer",
        ],

        "required_skills": [
            "master data management",
            "data modeling",
            "sql",
        ],

        "preferred_skills": [
            "reltio",
            "informatica mdm",
            "api",
            "data quality",
            "data governance",
            "match merge",
            "reference data",
        ],

        "keywords": [
            "golden record",
            "entity resolution",
            "survivorship",
            "match and merge",
            "master data",
        ],

        "excluded_keywords": [
            "mobile device management",
            "endpoint management",
        ],
    },

    "cloud data engineer": {

        "title_aliases": [
            "cloud data engineer",
            "aws data engineer",
            "azure data engineer",
            "gcp data engineer",
            "cloud analytics engineer",
        ],

        "required_skills": [
            "python",
            "sql",
            "cloud",
            "etl",
        ],

        "preferred_skills": [
            "aws",
            "azure",
            "gcp",
            "spark",
            "databricks",
            "snowflake",
            "terraform",
            "docker",
            "kubernetes",
        ],

        "keywords": [
            "cloud data platform",
            "cloud migration",
            "data lake",
            "cloud warehouse",
            "serverless data processing",
        ],

        "excluded_keywords": [
            "cloud network engineer",
            "cloud security engineer",
            "cloud support engineer",
        ],
    },
}


DEFAULT_ROLE = "data engineer"

# ==========================================================
# ATS V5.0 - ROLE FAMILIES, PLATFORMS AND COMPATIBILITY
# ==========================================================
ROLE_FAMILIES = {
    "data engineer": "data_engineering",
    "cloud data engineer": "data_engineering",
    "databricks engineer": "data_engineering",
    "snowflake engineer": "data_engineering",
    "etl developer": "data_integration",
    "business intelligence engineer": "analytics_bi",
    "data analyst": "analytics_bi",
    "analytics engineer": "analytics_bi",
    "data scientist": "data_science",
    "data architect": "architecture",
    "data governance engineer": "governance",
    "mdm engineer": "governance",
}

ROLE_PLATFORMS = {
    "databricks engineer": "databricks",
    "snowflake engineer": "snowflake",
    "etl developer": "etl",
    "business intelligence engineer": "bi",
    "cloud data engineer": "cloud",
    "mdm engineer": "mdm",
    "data governance engineer": "governance",
}

PLATFORM_CORE_SKILLS = {
    "databricks": ["databricks", "spark", "delta lake", "unity catalog"],
    "snowflake": ["snowflake", "snowpipe"],
    "informatica": ["informatica"],
    "ab initio": ["ab initio"],
    "datastage": ["datastage"],
    "talend": ["talend"],
    "power bi": ["power bi", "dax"],
    "tableau": ["tableau"],
    "mdm": ["master data management", "reltio", "informatica mdm"],
    "governance": ["data governance", "data quality", "metadata", "data lineage"],
}

ROLE_COMPATIBILITY = {
    "data engineer": {"data engineer": 100, "cloud data engineer": 92, "databricks engineer": 88, "snowflake engineer": 86, "etl developer": 72, "data architect": 70, "analytics engineer": 62, "data analyst": 45, "business intelligence engineer": 48, "data scientist": 50},
    "cloud data engineer": {"cloud data engineer": 100, "data engineer": 92, "databricks engineer": 90, "snowflake engineer": 86, "etl developer": 68, "data architect": 75},
    "databricks engineer": {"databricks engineer": 100, "cloud data engineer": 92, "data engineer": 90, "snowflake engineer": 68, "etl developer": 55, "data architect": 70, "data scientist": 58},
    "snowflake engineer": {"snowflake engineer": 100, "data engineer": 88, "cloud data engineer": 84, "databricks engineer": 68, "etl developer": 62, "business intelligence engineer": 64, "data architect": 72},
    "etl developer": {"etl developer": 100, "data engineer": 76, "cloud data engineer": 66, "databricks engineer": 52, "snowflake engineer": 60, "mdm engineer": 58},
    "business intelligence engineer": {"business intelligence engineer": 100, "data analyst": 84, "analytics engineer": 90, "snowflake engineer": 58, "data engineer": 52},
    "data analyst": {"data analyst": 100, "business intelligence engineer": 82, "analytics engineer": 78, "data scientist": 58, "data engineer": 44},
    "data scientist": {"data scientist": 100, "data engineer": 55, "databricks engineer": 58, "data analyst": 62},
    "data architect": {"data architect": 100, "data engineer": 78, "cloud data engineer": 82, "databricks engineer": 72, "snowflake engineer": 74, "data governance engineer": 70},
    "data governance engineer": {"data governance engineer": 100, "mdm engineer": 84, "data architect": 72, "data analyst": 48},
    "mdm engineer": {"mdm engineer": 100, "data governance engineer": 85, "etl developer": 62, "data architect": 68},
}

for _role_name, _config in ROLE_DATABASE.items():
    _required = list(_config.get("required_skills", []))
    _preferred = list(_config.get("preferred_skills", []))
    _config.setdefault("role_family", ROLE_FAMILIES.get(_role_name, "other"))
    _config.setdefault("platform", ROLE_PLATFORMS.get(_role_name, ""))
    _config.setdefault("core_skills", _required)
    _config.setdefault("secondary_skills", _preferred)
    _config.setdefault("compatible_roles", ROLE_COMPATIBILITY.get(_role_name, {_role_name: 100}))
    _config.setdefault("platform_priority", 1.0 if _config.get("platform") else 0.5)
