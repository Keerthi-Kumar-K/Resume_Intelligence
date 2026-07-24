"""Role/platform-conditioned achievement and complexity scoring."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Iterable, List

@dataclass
class AchievementAssessment:
    achievement_score: float = 0.0
    complexity_score: float = 0.0
    relevant_achievements: List[str] = field(default_factory=list)
    relevant_complexity: List[str] = field(default_factory=list)

class AchievementRelevanceEngine:
    METRIC = re.compile(r"[^\n.;]{0,120}\b(?:reduced|improved|increased|accelerated|optimized|saved|cut|processed|supported)\b[^\n.;]{0,130}\b\d+(?:\.\d+)?\s*(?:%|x|hours?|days?|minutes?|tb|gb|million|billion|m\+|k\+)\b[^\n.;]{0,60}", re.I)
    COMPLEXITY = {"lakehouse", "medallion architecture", "cdc", "streaming", "kafka", "kinesis", "event hubs", "terraform", "ci/cd", "kubernetes", "docker", "microservices", "unity catalog", "data lineage", "rbac", "dynamic masking", "iceberg", "delta lake", "snowpipe", "snowpark", "streams", "tasks", "powercenter", "ab initio"}

    def assess(self, text: str, target_terms: Iterable[str]) -> AchievementAssessment:
        text = str(text or "")
        lowered = text.lower()
        targets = {str(t).strip().lower() for t in target_terms if str(t).strip()}
        achievements = []
        for match in self.METRIC.finditer(text):
            snippet = match.group(0).strip()
            nearby = lowered[max(0, match.start()-140):min(len(lowered), match.end()+140)]
            overlap = sum(1 for term in targets if term and term in nearby)
            if overlap:
                achievements.append(snippet)
        achievements = list(dict.fromkeys(achievements))[:10]

        relevant_complexity = sorted(term for term in self.COMPLEXITY if term in lowered and (term in targets or any(t in lowered[max(0, lowered.find(term)-160):lowered.find(term)+200] for t in targets)))
        ach_score = min(100.0, len(achievements) * 22.0)
        comp_score = min(100.0, len(relevant_complexity) * 12.5)
        return AchievementAssessment(round(ach_score, 2), round(comp_score, 2), achievements, relevant_complexity)
