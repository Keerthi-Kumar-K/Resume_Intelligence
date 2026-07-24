"""Achievement and project-complexity scoring for ATS V6."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class ImpactResult:
    achievement_score: float = 0.0
    complexity_score: float = 0.0
    achievements: List[str] = field(default_factory=list)
    complexity_signals: List[str] = field(default_factory=list)


class ImpactEngine:
    METRIC_PATTERNS = [
        re.compile(r"\b(?:reduced|decreased|improved|increased|accelerated|optimized|saved|cut)\b[^\n.;]{0,90}?\b\d+(?:\.\d+)?\s*%", re.I),
        re.compile(r"\b\d+(?:\.\d+)?\s*(?:million|billion|m\+|k\+|tb|gb|hours?|days?|minutes?)\b", re.I),
        re.compile(r"\b(?:from|under|within)\s+\d+(?:\.\d+)?\s*(?:hours?|days?|minutes?|seconds?)\b", re.I),
    ]
    ACTION_WORDS = re.compile(r"\b(?:architected|designed|built|led|implemented|migrated|modernized|automated|optimized|scaled|secured|reduced|decreased|improved|increased|accelerated|saved|cut)\b", re.I)
    COMPLEXITY_TERMS = {
        "lakehouse", "medallion architecture", "cdc", "change data capture",
        "streaming", "kafka", "kinesis", "event hubs", "terraform", "ci/cd",
        "kubernetes", "docker", "microservices", "data governance", "unity catalog",
        "data lineage", "rbac", "dynamic masking", "high availability",
        "disaster recovery", "real time", "near real time", "distributed",
        "orchestration", "airflow", "control-m", "iceberg", "delta lake",
    }

    def evaluate(self, text: str) -> ImpactResult:
        text = str(text or "")
        lowered = text.lower()
        achievements: List[str] = []
        for pattern in self.METRIC_PATTERNS:
            for match in pattern.finditer(text):
                snippet = match.group(0).strip()
                if self.ACTION_WORDS.search(snippet) or self.ACTION_WORDS.search(text[max(0, match.start()-80):match.end()+30]):
                    achievements.append(snippet)
        achievements = list(dict.fromkeys(achievements))[:12]
        complexity = sorted(term for term in self.COMPLEXITY_TERMS if term in lowered)

        achievement_score = min(100.0, len(achievements) * 16.0)
        complexity_score = min(100.0, len(complexity) * 8.0)
        return ImpactResult(
            achievement_score=round(achievement_score, 2),
            complexity_score=round(complexity_score, 2),
            achievements=achievements,
            complexity_signals=complexity,
        )
