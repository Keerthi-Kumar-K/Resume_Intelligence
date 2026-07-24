"""Hierarchical role compatibility for ATS V7."""
from __future__ import annotations

ROLE_FAMILY = {
    "data engineer": "data engineering", "databricks engineer": "data engineering",
    "snowflake engineer": "data engineering", "etl developer": "data engineering",
    "informatica developer": "data engineering", "ab initio developer": "data engineering",
    "analytics engineer": "analytics engineering", "data analyst": "analytics",
    "business intelligence engineer": "analytics", "bi developer": "analytics",
    "data scientist": "data science", "machine learning engineer": "data science",
    "data architect": "architecture", "databricks architect": "architecture",
    "snowflake architect": "architecture", "data governance analyst": "governance",
    "mdm developer": "governance",
}

FAMILY_COMPATIBILITY = {
    ("data engineering", "data engineering"): 92,
    ("architecture", "data engineering"): 78,
    ("data engineering", "architecture"): 72,
    ("analytics engineering", "data engineering"): 75,
    ("data engineering", "analytics engineering"): 72,
    ("analytics", "data engineering"): 48,
    ("data engineering", "analytics"): 55,
    ("governance", "data engineering"): 45,
    ("data engineering", "governance"): 50,
}

class RoleHierarchyEngine:
    def score(self, resume_role: str, job_role: str, existing_score: float = 0.0) -> float:
        rr, jr = str(resume_role or "").lower(), str(job_role or "").lower()
        if rr and rr == jr:
            return 100.0
        rf, jf = ROLE_FAMILY.get(rr, rr), ROLE_FAMILY.get(jr, jr)
        hierarchical = FAMILY_COMPATIBILITY.get((rf, jf), 35.0 if rf and jf else 50.0)
        return round(max(float(existing_score or 0.0), hierarchical), 2)
