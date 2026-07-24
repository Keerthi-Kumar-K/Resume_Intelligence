"""Deterministic skill ontology and inference for ATS V6."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set


# Relationships intentionally remain conservative: inferred concepts help
# matching, but never pretend to be explicit years of hands-on experience.
SKILL_ONTOLOGY: Dict[str, Set[str]] = {
    "delta live tables": {"databricks", "delta lake", "spark", "etl", "lakehouse"},
    "dlt": {"delta live tables", "databricks", "delta lake", "spark"},
    "unity catalog": {"databricks", "data governance", "metadata", "data lineage"},
    "photon": {"databricks", "spark", "performance optimization"},
    "medallion architecture": {"lakehouse", "data lake", "etl", "data modeling"},
    "delta lake": {"lakehouse", "spark", "data lake"},
    "pyspark": {"spark", "python", "data engineering"},
    "spark structured streaming": {"spark", "streaming", "real time processing"},
    "azure data factory": {"azure", "etl", "data integration", "orchestration"},
    "adf": {"azure data factory", "azure", "etl", "data integration"},
    "aws glue": {"aws", "etl", "data integration", "serverless"},
    "amazon emr": {"aws", "spark", "hadoop", "big data"},
    "emr": {"amazon emr", "aws", "spark", "hadoop"},
    "snowpipe": {"snowflake", "data ingestion", "streaming"},
    "snowpark": {"snowflake", "python", "data engineering"},
    "dynamic tables": {"snowflake", "etl", "data transformation"},
    "informatica powercenter": {"informatica", "etl", "data integration"},
    "ab initio": {"etl", "data integration", "batch processing"},
    "ssis": {"etl", "data integration", "sql server"},
    "dbt": {"analytics engineering", "sql", "data transformation", "data modeling"},
    "airflow": {"orchestration", "workflow orchestration", "data pipelines"},
    "kafka": {"streaming", "event driven architecture", "real time processing"},
    "kinesis": {"aws", "streaming", "event driven architecture"},
    "cdc": {"change data capture", "incremental loading", "data replication"},
    "terraform": {"infrastructure as code", "devops", "cloud"},
    "docker": {"containers", "devops"},
    "kubernetes": {"containers", "orchestration", "devops"},
    "power bi": {"business intelligence", "data visualization", "analytics"},
    "dax": {"power bi", "business intelligence", "analytics"},
    "tableau": {"business intelligence", "data visualization", "analytics"},
    "reltio": {"master data management", "mdm", "data governance"},
    "collibra": {"data governance", "metadata", "data catalog"},
    "alation": {"data governance", "metadata", "data catalog"},
    "hipaa": {"healthcare", "compliance", "data security"},
    "pci-dss": {"financial services", "compliance", "data security"},
}

ALIASES: Dict[str, str] = {
    "apache spark": "spark",
    "azure databricks": "databricks",
    "aws emr": "amazon emr",
    "powercenter": "informatica powercenter",
    "informatica pc": "informatica powercenter",
    "abinitio": "ab initio",
    "delta live table": "delta live tables",
    "change data capture": "cdc",
    "ci/cd": "continuous integration",
    "cicd": "continuous integration",
    "master data management": "mdm",
}

PLATFORM_EVIDENCE: Dict[str, Set[str]] = {
    "databricks": {"databricks", "delta live tables", "unity catalog", "photon", "delta lake", "pyspark"},
    "snowflake": {"snowflake", "snowpipe", "snowpark", "dynamic tables"},
    "informatica": {"informatica", "informatica powercenter", "powercenter"},
    "ab initio": {"ab initio"},
    "azure": {"azure", "azure data factory", "adf", "synapse analytics", "adls gen2"},
    "aws": {"aws", "aws glue", "amazon emr", "s3", "kinesis", "redshift"},
    "power bi": {"power bi", "dax"},
    "tableau": {"tableau"},
    "mdm": {"mdm", "reltio", "informatica mdm"},
}


@dataclass
class InferenceResult:
    explicit_skills: Set[str] = field(default_factory=set)
    inferred_skills: Set[str] = field(default_factory=set)
    evidence: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def all_skills(self) -> Set[str]:
        return self.explicit_skills | self.inferred_skills


class SkillOntologyEngine:
    def canonicalize(self, skill: str) -> str:
        value = str(skill or "").strip().lower()
        return ALIASES.get(value, value)

    def infer(self, skills: Iterable[str], max_depth: int = 2) -> InferenceResult:
        explicit = {self.canonicalize(skill) for skill in skills if str(skill or "").strip()}
        inferred: Set[str] = set()
        evidence: Dict[str, Set[str]] = defaultdict(set)
        queue = deque((skill, 0, skill) for skill in explicit)
        visited = set()

        while queue:
            skill, depth, root = queue.popleft()
            key = (skill, depth, root)
            if key in visited:
                continue
            visited.add(key)
            if depth >= max_depth:
                continue
            for related in SKILL_ONTOLOGY.get(skill, set()):
                canonical = self.canonicalize(related)
                evidence[canonical].add(root)
                if canonical not in explicit:
                    inferred.add(canonical)
                queue.append((canonical, depth + 1, root))

        return InferenceResult(
            explicit_skills=explicit,
            inferred_skills=inferred,
            evidence={key: sorted(values) for key, values in evidence.items()},
        )

    def detect_specialization(self, skills: Iterable[str]) -> tuple[str, float, Dict[str, float]]:
        result = self.infer(skills)
        all_skills = result.all_skills
        scores: Dict[str, float] = {}
        for platform, evidence_skills in PLATFORM_EVIDENCE.items():
            explicit_hits = len(result.explicit_skills & evidence_skills)
            inferred_hits = len(result.inferred_skills & evidence_skills)
            scores[platform] = explicit_hits * 2.0 + inferred_hits * 0.75
        if not scores or max(scores.values(), default=0.0) <= 0:
            return "", 0.0, scores
        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1.0
        confidence = min(100.0, 55.0 + 45.0 * scores[best] / total)
        return best, round(confidence, 2), scores
