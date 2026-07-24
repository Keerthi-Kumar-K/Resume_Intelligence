SKILL_CATEGORIES = {

    "Programming": [],

    "Databases": [],

    "Cloud": [],

    "Big Data": [],

    "Data Warehouse": [],

    "ETL": [],

    "Streaming": [],

    "Orchestration": [],

    "BI": [],

    "DevOps": [],

    "Data Modeling": [],

    "Governance": [],

    "Data Quality": [],

    "Machine Learning": [],

    "AI": [],

    "Operating Systems": [],

    "Version Control": [],

    "Testing": []

}

PROGRAMMING = {

    "Python": [

        "python",

        "python3",

        "python 3"

    ],

    "SQL": [

        "sql",

        "tsql",

        "t-sql",

        "pl/sql"

    ],

    "Scala":[

        "scala"

    ],

    "Java":[

        "java"

    ],

    "R":[

        "r language",

        "r programming",

        "r"

    ],

    "Shell":[

        "shell",

        "bash",

        "ksh"

    ]

}

BIG_DATA = {

    "Spark":[

        "spark",

        "apache spark",

        "spark sql",

        "pyspark"

    ],

    "Kafka":[

        "kafka",

        "apache kafka"

    ],

    "Hadoop":[

        "hadoop"

    ],

    "Hive":[

        "hive",

        "apache hive"

    ],

    "Flink":[

        "flink",

        "apache flink"

    ]

}

CLOUD = {

    "AWS":[

        "aws",

        "amazon web services"

    ],

    "Azure":[

        "azure",

        "microsoft azure"

    ],

    "GCP":[

        "gcp",

        "google cloud"

    ]

}

DATABRICKS = {

    "Databricks":[

        "databricks"

    ],

    "Delta Lake":[

        "delta lake"

    ],

    "Unity Catalog":[

        "unity catalog"

    ],

    "MLflow":[

        "mlflow"

    ],

    "DLT":[

        "delta live tables",

        "dlt"

    ],

    "Photon":[

        "photon"

    ]

}
SNOWFLAKE = {

    "Snowflake":[

        "snowflake"

    ],

    "Snowpipe":[

        "snowpipe"

    ],

    "Streams":[

        "streams"

    ],

    "Tasks":[

        "tasks"

    ],

    "Time Travel":[

        "time travel"

    ]

}
ETL = {

    "Informatica":[

        "informatica",

        "powercenter"

    ],

    "Talend":[

        "talend"

    ],

    "Ab Initio":[

        "ab initio"

    ],

    "DataStage":[

        "datastage"

    ],

    "SSIS":[

        "ssis"

    ],

    "ADF":[

        "azure data factory",

        "adf"

    ],

    "AWS Glue":[

        "aws glue",

        "glue"

    ]

}
BI = {

    "Power BI":[

        "power bi"

    ],

    "Tableau":[

        "tableau"

    ],

    "Looker":[

        "looker"

    ],

    "QuickSight":[

        "quicksight"

    ]
}
DATABASES = {

    "Oracle":["oracle"],

    "SQL Server":[

        "sql server"

    ],

    "PostgreSQL":[

        "postgresql",

        "postgres"

    ],

    "MySQL":[

        "mysql"

    ],

    "Teradata":[

        "teradata"

    ],

    "DB2":[

        "db2"

    ]
}
DEVOPS = {

    "Docker":["docker"],

    "Kubernetes":[

        "kubernetes",

        "aks",

        "eks"

    ],

    "Terraform":[

        "terraform"

    ],

    "Jenkins":[

        "jenkins"

    ],

    "Git":[

        "git",

        "github",

        "gitlab",

        "bitbucket"

    ]
}
ORCHESTRATION = {

    "Airflow":[

        "airflow",

        "apache airflow"

    ],

    "Control-M":[

        "control-m"

    ],

    "Prefect":[

        "prefect"

    ]
}

# Additional recruiter-relevant skills used by role and JD classification.
DATA_ENGINEERING = {
    "ETL": ["etl", "extract transform load"],
    "Data Pipelines": ["data pipeline", "data pipelines"],
    "Data Warehouse": ["data warehouse", "data warehousing"],
    "Data Lake": ["data lake", "data lakes"],
    "Data Modeling": ["data modeling", "data modelling"],
    "dbt": ["dbt", "data build tool"],
    "ADLS": ["adls", "azure data lake storage", "adls gen2"],
    "Medallion Architecture": ["medallion architecture", "bronze silver gold"],
}

GOVERNANCE = {
    "Data Governance": ["data governance"],
    "Data Quality": ["data quality"],
    "Metadata": ["metadata", "metadata management"],
    "Data Lineage": ["data lineage", "lineage"],
    "Collibra": ["collibra"],
    "Alation": ["alation"],
    "Reltio": ["reltio"],
    "Master Data Management": ["master data management", "mdm"],
}

ANALYTICS = {
    "Excel": ["excel", "microsoft excel"],
    "DAX": ["dax"],
    "Statistics": ["statistics", "statistical analysis"],
    "Data Visualization": ["data visualization", "data visualisation"],
    "Business Intelligence": ["business intelligence", "bi reporting"],
}

ALL_GROUPS = {
    "Programming": PROGRAMMING,
    "Big Data": BIG_DATA,
    "Cloud": CLOUD,
    "Databricks": DATABRICKS,
    "Snowflake": SNOWFLAKE,
    "ETL": ETL,
    "BI": BI,
    "Databases": DATABASES,
    "DevOps": DEVOPS,
    "Orchestration": ORCHESTRATION,
    "Data Engineering": DATA_ENGINEERING,
    "Governance": GOVERNANCE,
    "Analytics": ANALYTICS,
}

SKILL_DATABASE = {}

for category, skills in ALL_GROUPS.items():
    for canonical_name, aliases in skills.items():
        SKILL_DATABASE[canonical_name.lower()] = {
            "canonical": canonical_name,
            "aliases": [a.lower() for a in aliases],
            "category": category,
            "weight": 5,
        }

# ==========================================================
# ATS V5.0 - RECRUITER-STYLE SKILL METADATA
# ==========================================================
# The original dictionaries above remain backward compatible.  The metadata
# below enriches each canonical skill with tier, weight, platform and type.

CORE_PLATFORM_SKILLS = {
    "databricks", "snowflake", "informatica", "ab initio", "datastage",
    "talend", "ssis", "power bi", "tableau", "looker", "reltio",
    "informatica mdm", "collibra", "alation", "data governance",
    "master data management", "reltio",
}

MAJOR_TECHNOLOGY_SKILLS = {
    "spark", "delta lake", "unity catalog", "dlt", "mlflow", "snowpipe",
    "streams", "tasks", "adf", "aws glue", "airflow", "control-m",
    "kafka", "hadoop", "hive", "terraform", "kubernetes", "docker",
    "aws", "azure", "gcp", "oracle", "teradata", "sql server",
    "postgresql", "db2", "data quality", "metadata", "data lineage",
    "data modeling", "dbt", "adls",
}

SUPPORTING_SKILLS = {
    "python", "sql", "scala", "java", "r", "shell", "git", "jenkins",
    "mysql", "excel", "json", "rest", "agile", "etl", "data pipelines",
    "data warehouse", "data lake", "business intelligence", "dax",
}

PLATFORM_OWNERSHIP = {
    "databricks": "databricks", "delta lake": "databricks",
    "unity catalog": "databricks", "dlt": "databricks",
    "mlflow": "databricks", "photon": "databricks", "spark": "databricks",
    "snowflake": "snowflake", "snowpipe": "snowflake",
    "streams": "snowflake", "tasks": "snowflake", "time travel": "snowflake",
    "informatica": "informatica", "ab initio": "ab initio",
    "datastage": "datastage", "talend": "talend", "ssis": "ssis",
    "power bi": "power bi", "tableau": "tableau", "looker": "looker",
    "adf": "azure", "azure": "azure", "aws glue": "aws", "aws": "aws",
    "gcp": "gcp",
}

SKILL_TYPE_BY_CATEGORY = {
    "Databricks": "platform", "Snowflake": "platform", "ETL": "platform",
    "BI": "platform", "Cloud": "cloud", "Big Data": "major_technology",
    "Databases": "database", "Orchestration": "major_technology",
    "DevOps": "supporting", "Programming": "supporting",
    "Data Engineering": "major_technology", "Governance": "major_technology",
    "Analytics": "supporting",
}

for _skill_name, _metadata in SKILL_DATABASE.items():
    _name = _skill_name.lower()
    _category = _metadata.get("category", "")

    if _name in CORE_PLATFORM_SKILLS:
        _tier, _weight = 1, 10
    elif _name in MAJOR_TECHNOLOGY_SKILLS:
        _tier, _weight = 2, 5
    else:
        _tier, _weight = 3, 1

    _metadata.update({
        "tier": _tier,
        "weight": _weight,
        "platform": PLATFORM_OWNERSHIP.get(_name, ""),
        "skill_type": SKILL_TYPE_BY_CATEGORY.get(_category, "supporting"),
        "importance": "core" if _tier == 1 else "major" if _tier == 2 else "supporting",
    })


def get_skill_metadata(skill_name):
    """Return normalized V5 metadata for a skill without raising KeyError."""
    name = str(skill_name or "").strip().lower()
    return SKILL_DATABASE.get(name, {
        "canonical": str(skill_name or "").strip(),
        "aliases": [name] if name else [],
        "category": "Unknown",
        "tier": 3,
        "weight": 1,
        "platform": "",
        "skill_type": "supporting",
        "importance": "supporting",
    })
