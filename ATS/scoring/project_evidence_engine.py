"""Project-level evidence and platform tenure estimation.

This is the authoritative source for project count, platform years and
project-backed skill evidence. It handles resume text extracted from PDFs,
including curly apostrophes and two-digit years.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Set

from ATS.scoring.platform_engine import PLATFORM_MARKERS

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7,
    "july": 7, "aug": 8, "august": 8, "sep": 9, "sept": 9,
    "september": 9, "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}
MONTH_PATTERN = r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
DATE_RANGE = re.compile(
    rf"(?P<m1>{MONTH_PATTERN})?\s*[’'`]?(?P<y1>\d{{2}}|(?:19|20)\d{{2}})\s*(?:-|–|—|to)\s*"
    rf"(?:(?P<m2>{MONTH_PATTERN})?\s*[’'`]?(?P<y2>\d{{2}}|(?:19|20)\d{{2}})|(?P<present>present|current))",
    re.I,
)
ACTIONS = re.compile(r"\b(architected|built|designed|implemented|developed|engineered|optimized|migrated|configured|administered|led|automated|integrated|deployed|managed|orchestrated|tuned|created|delivered|established|enforced)\b", re.I)
METRICS = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|x|hours?|days?|minutes?|seconds?|tb|gb|mb|million|billion|m\+|k\+?)\b", re.I)


@dataclass
class ProjectEvidenceAssessment:
    platform_years: float = 0.0
    project_count: int = 0
    strong_projects: int = 0
    platform_projects: List[str] = field(default_factory=list)
    evidence_summary: str = ""
    skill_evidence: Dict[str, float] = field(default_factory=dict)
    platform_score: float = 50.0
    specialization_prior: float = 0.5


class ProjectEvidenceEngine:
    @staticmethod
    def _contains(text: str, term: str) -> bool:
        return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I))

    @staticmethod
    def _normalize_year(value: str) -> int:
        year = int(value)
        return 2000 + year if year < 70 else (1900 + year if year < 100 else year)

    @classmethod
    def _duration_years(cls, block: str) -> float:
        match = DATE_RANGE.search(block)
        if not match:
            return 0.0
        y1 = cls._normalize_year(match.group("y1"))
        m1 = MONTHS.get((match.group("m1") or "jan").lower(), 1)
        if match.group("present"):
            now = datetime.now()
            y2, m2 = now.year, now.month
        else:
            y2 = cls._normalize_year(match.group("y2"))
            m2 = MONTHS.get((match.group("m2") or "dec").lower(), 12)
        months = max(1, (y2 - y1) * 12 + m2 - m1 + 1)
        return min(15.0, months / 12.0)

    @staticmethod
    def _experience_blocks(text: str) -> List[str]:
        text = str(text or "").replace("\f", "\n")
        # Most resumes in this project use "Client:" to begin each dated role.
        starts = [m.start() for m in re.finditer(r"(?im)^\s*client\s*:", text)]
        if starts:
            starts.append(len(text))
            return [text[starts[i]:starts[i + 1]].strip() for i in range(len(starts) - 1)]
        # Fallback for conventional company/date resume layouts.
        pieces = re.split(r"(?im)(?=^.{0,100}(?:19|20)?\d{2}\s*(?:-|–|—|to)\s*(?:present|current|(?:19|20)?\d{2})\s*$)", text)
        return [p.strip() for p in pieces if len(p.strip()) >= 120]

    @classmethod
    def _header_prior(cls, text: str, target: str) -> float:
        lower = str(text or "").lower()
        boundary = lower.find("professional experience")
        header = lower[:boundary] if boundary > 0 else lower[: max(1200, len(lower) // 3)]
        platform_scores: Dict[str, float] = {}
        for platform, markers in PLATFORM_MARKERS.items():
            score = 0.0
            for marker in markers:
                count = len(re.findall(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", header, re.I))
                score += min(4, count)
            if re.search(r"(?im)^\s*core stack[^\n]*" + re.escape(platform), header):
                score += 8.0
            if re.search(r"(?im)^\s*(?:role|title)\s*:[^\n]*" + re.escape(platform), header):
                score += 6.0
            platform_scores[platform] = score
        target_score = platform_scores.get(target, 0.0)
        best_other_platform, best_other = max(
            ((k, v) for k, v in platform_scores.items() if k != target),
            key=lambda item: item[1],
            default=("", 0.0),
        )
        if target_score <= 0:
            return 0.12

        # The first technology in Core Stack is an intentional specialization
        # signal in tailored resumes. It should outweigh incidental cross-stack
        # mentions elsewhere in the summary.
        core_match = re.search(r"(?im)^\s*core stack\s+([^\n]+)", header)
        core_line = core_match.group(1).strip() if core_match else ""
        primary_core = ""
        earliest = 10**9
        for platform in PLATFORM_MARKERS:
            pos = core_line.find(platform)
            if 0 <= pos < earliest:
                primary_core, earliest = platform, pos

        dominance = target_score / max(1.0, target_score + best_other)
        prior = 0.18 + 0.82 * dominance
        if primary_core == target:
            prior = max(prior, 0.92)
        elif primary_core and primary_core != target:
            prior = min(prior, 0.46)
        elif best_other > target_score:
            prior = min(prior, 0.52)
        return max(0.12, min(1.0, prior))

    def assess(self, resume_text: str, target_platform: str, required_skills: Iterable[str], resume_role: str = "") -> ProjectEvidenceAssessment:
        text = str(resume_text or "")
        target = str(target_platform or "").strip().lower()
        required = {str(x).strip().lower() for x in required_skills if str(x).strip()}
        markers: Set[str] = set(PLATFORM_MARKERS.get(target, set()))
        blocks = self._experience_blocks(text)
        prior = self._header_prior(text, target) if target else 0.5
        role_text = str(resume_role or "").lower()
        if target and target in role_text:
            prior = max(prior, 0.94)
        elif target and role_text:
            if any(p in role_text for p in PLATFORM_MARKERS if p != target):
                prior = min(prior, 0.38)
            elif "etl" in role_text and target not in {"informatica", "ab initio"}:
                prior = min(prior, 0.30)

        matched_blocks: List[str] = []
        years = 0.0
        strong = 0
        skill_values: Dict[str, List[float]] = {s: [] for s in required}
        project_strengths: List[float] = []

        for block in blocks:
            low = block.lower()
            target_hits = {m for m in markers if self._contains(low, m)}
            required_hits = {s for s in required if self._contains(low, s)}
            if target and not target_hits:
                continue
            if not target and not required_hits:
                continue

            all_platform_hits = 0
            for platform_markers in PLATFORM_MARKERS.values():
                all_platform_hits += sum(1 for m in platform_markers if self._contains(low, m))
            action_count = min(8, len(ACTIONS.findall(block)))
            metric_count = min(5, len(METRICS.findall(block)))
            unique_target = len(target_hits)
            unique_required = len(required_hits)
            density = unique_target / max(1, all_platform_hits)

            strength = min(100.0,
                18.0 + unique_target * 9.0 + unique_required * 4.0
                + action_count * 3.0 + metric_count * 2.5 + density * 18.0
            )
            project_strengths.append(strength)
            if strength >= 68:
                strong += 1

            duration = self._duration_years(block)
            relevance = min(1.0, 0.20 + 0.50 * density + 0.30 * (strength / 100.0))
            if duration > 0:
                years += duration * relevance
            else:
                years += min(0.75, strength / 160.0)

            for skill in required_hits:
                sentence_actions = bool(re.search(r"\b(?:" + ACTIONS.pattern[3:-5] + r")\b[^.;\n]{0,160}" + re.escape(skill), low, re.I))
                score = 48.0 + min(24.0, strength * 0.24) + (12.0 if sentence_actions else 0.0)
                skill_values.setdefault(skill, []).append(min(100.0, score))

            matched_blocks.append(re.sub(r"\s+", " ", block)[:320])

        # Specialization dominance controls how much cross-platform project evidence counts.
        years *= 0.55 + 0.45 * prior
        years = min(12.0, years)
        avg_strength = sum(project_strengths) / len(project_strengths) if project_strengths else 0.0
        platform_score = 50.0 if not target else min(100.0,
            8.0 + 42.0 * prior + 30.0 * (avg_strength / 100.0)
            + min(20.0, years * 4.0)
        )

        skill_evidence = {}
        for skill, values in skill_values.items():
            if values:
                repeat_bonus = min(12.0, max(0, len(values) - 1) * 5.0)
                skill_evidence[skill] = min(100.0, max(values) + repeat_bonus)

        confidence = "Strong" if platform_score >= 78 and (strong >= 1 or years >= 2.5) else "Moderate" if matched_blocks else "Weak"
        label = target.title() if target else "Role"
        summary = f"{label}: {confidence}; projects {len(matched_blocks)}; strong {strong}; estimated years {years:.1f}; specialization {prior * 100:.0f}%"
        return ProjectEvidenceAssessment(
            platform_years=round(years, 2),
            project_count=len(matched_blocks),
            strong_projects=strong,
            platform_projects=matched_blocks[:4],
            evidence_summary=summary,
            skill_evidence={k: round(v, 2) for k, v in skill_evidence.items()},
            platform_score=round(platform_score, 2),
            specialization_prior=round(prior, 3),
        )
