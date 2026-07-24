"""Target-platform expertise and hard-gate scoring for ATS V7."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set

PLATFORM_MARKERS: Dict[str, Set[str]] = {
    "databricks": {"databricks", "delta lake", "delta live tables", "dlt", "unity catalog", "photon", "pyspark", "medallion architecture"},
    "snowflake": {"snowflake", "snowpipe", "snowpark", "streams", "tasks", "dynamic tables", "warehouse"},
    "informatica": {"informatica", "informatica powercenter", "powercenter", "iics", "informatica cloud"},
    "ab initio": {"ab initio", "abinitio", "gde", "co>operating system"},
    "azure": {"azure", "azure data factory", "adf", "synapse", "adls", "event hubs", "fabric"},
    "aws": {"aws", "amazon emr", "emr", "aws glue", "s3", "redshift", "kinesis", "athena"},
    "power bi": {"power bi", "dax", "power query", "semantic model", "row level security"},
    "tableau": {"tableau", "tableau server", "tableau prep"},
    "mdm": {"mdm", "master data management", "reltio", "informatica mdm"},
}

ARCHITECT_GATES = {
    "databricks": {"databricks", "delta lake", "unity catalog", "pyspark", "medallion architecture", "delta live tables"},
    "snowflake": {"snowflake", "snowpipe", "streams", "tasks", "snowpark", "dynamic tables"},
    "informatica": {"informatica", "informatica powercenter", "iics", "etl", "data integration"},
}

@dataclass
class PlatformAssessment:
    target_platform: str = ""
    score: float = 50.0
    evidence_score: float = 0.0
    estimated_years: float = 0.0
    explicit_markers: List[str] = field(default_factory=list)
    missing_core_markers: List[str] = field(default_factory=list)
    hard_gate_cap: float = 100.0
    mismatch_penalty: float = 0.0

class PlatformExpertiseEngine:
    def detect_target(self, job_title: str, job_skills: Iterable[str], role_platform: str = "") -> str:
        title = str(job_title or "").lower()
        skills = {str(s).strip().lower() for s in job_skills if str(s).strip()}
        candidates = []
        for platform, markers in PLATFORM_MARKERS.items():
            score = (4 if platform in title else 0) + len(markers & skills)
            if score:
                candidates.append((score, platform))
        if candidates:
            return max(candidates)[1]
        fallback = str(role_platform or "").strip().lower()
        return fallback if fallback in PLATFORM_MARKERS else ""

    def assess(self, resume_text: str, resume_skills: Iterable[str], target_platform: str, job_title: str = "") -> PlatformAssessment:
        target = str(target_platform or "").lower()
        if not target or target not in PLATFORM_MARKERS:
            return PlatformAssessment(target_platform=target, score=50.0)

        text = str(resume_text or "").lower()
        skills = {str(s).strip().lower() for s in resume_skills if str(s).strip()}
        markers = PLATFORM_MARKERS[target]
        explicit = sorted(marker for marker in markers if marker in skills or re.search(r"\b" + re.escape(marker) + r"\b", text))

        # Frequency and contextual use provide depth; a skill-list mention alone is weaker.
        frequency = sum(min(5, len(re.findall(r"\b" + re.escape(marker) + r"\b", text))) for marker in explicit)
        action_contexts = 0
        for marker in explicit:
            pattern = re.compile(r"\b(?:built|designed|architected|implemented|migrated|optimized|administered|developed|led|configured)\b[^.;\n]{0,100}\b" + re.escape(marker) + r"\b|\b" + re.escape(marker) + r"\b[^.;\n]{0,100}\b(?:built|designed|architected|implemented|migrated|optimized|administered|developed|led|configured)\b", re.I)
            action_contexts += min(3, len(pattern.findall(text)))

        marker_coverage = len(explicit) / max(1, len(markers))
        evidence_score = min(100.0, marker_coverage * 55.0 + min(25.0, frequency * 2.0) + min(20.0, action_contexts * 4.0))
        estimated_years = min(10.0, len(explicit) * 0.55 + frequency * 0.12 + action_contexts * 0.35)
        # Text-wide score is deliberately conservative; the final engine blends
        # this with dated project evidence and specialization dominance.
        score = min(100.0, 12.0 + evidence_score * 0.76)

        title = str(job_title or "").lower()
        gate_markers = ARCHITECT_GATES.get(target, set()) if "architect" in title else set()
        missing = sorted(gate_markers.difference(set(explicit)))
        cap = 100.0
        penalty = 0.0
        if gate_markers:
            gate_coverage = len(gate_markers & set(explicit)) / len(gate_markers)
            if gate_coverage < 0.34:
                cap, penalty = 62.0, 14.0
            elif gate_coverage < 0.50:
                cap, penalty = 75.0, 8.0
            elif gate_coverage < 0.67:
                cap, penalty = 88.0, 3.0
        elif len(explicit) <= 1:
            cap, penalty = 72.0, 8.0

        score = min(score, cap)
        return PlatformAssessment(
            target_platform=target,
            score=round(score, 2),
            evidence_score=round(evidence_score, 2),
            estimated_years=round(estimated_years, 2),
            explicit_markers=explicit,
            missing_core_markers=missing,
            hard_gate_cap=cap,
            mismatch_penalty=penalty,
        )
