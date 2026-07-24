"""Evidence depth scoring: repeated, contextual use outranks keyword mentions."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Iterable, List

@dataclass
class EvidenceAssessment:
    score: float = 0.0
    strong_evidence: List[str] = field(default_factory=list)
    weak_evidence: List[str] = field(default_factory=list)

class EvidenceEngine:
    ACTIONS = r"built|designed|architected|implemented|developed|optimized|migrated|configured|administered|led|automated|integrated"

    def assess(self, text: str, target_skills: Iterable[str]) -> EvidenceAssessment:
        text = str(text or "").lower()
        strong, weak = [], []
        points = 0.0
        for skill in sorted({str(s).strip().lower() for s in target_skills if str(s).strip()}):
            count = len(re.findall(r"\b" + re.escape(skill) + r"\b", text))
            contextual = bool(re.search(r"\b(?:" + self.ACTIONS + r")\b[^.;\n]{0,110}\b" + re.escape(skill) + r"\b|\b" + re.escape(skill) + r"\b[^.;\n]{0,110}\b(?:" + self.ACTIONS + r")\b", text, re.I))
            metric = bool(re.search(r"\b" + re.escape(skill) + r"\b[^.;\n]{0,130}\b\d+(?:\.\d+)?\s*(?:%|x|hours?|days?|tb|gb|million|billion)\b", text, re.I))
            if contextual or metric or count >= 3:
                strong.append(skill)
                points += min(8.0, 3.0 + count * 0.8 + (2.0 if metric else 0.0))
            elif count:
                weak.append(skill)
                points += min(2.0, 0.6 + count * 0.35)
        denominator = max(1, len(set(target_skills))) * 6.0
        score = min(100.0, 100.0 * points / denominator)
        return EvidenceAssessment(round(score, 2), strong, weak)
