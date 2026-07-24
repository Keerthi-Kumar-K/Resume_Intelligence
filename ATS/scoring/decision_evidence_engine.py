"""Authoritative evidence-quality scoring for required/preferred skills, BM25 and experience."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Iterable, List, Mapping, Sequence, Set

from ATS.config.skill_database import get_skill_metadata

ACTIONS = r"architected|built|designed|implemented|developed|engineered|optimized|migrated|configured|administered|led|automated|integrated|deployed|managed|orchestrated|tuned|created|delivered"
METRIC = r"\d+(?:\.\d+)?\s*(?:%|x|hours?|days?|minutes?|seconds?|tb|gb|mb|million|billion|m\+|k\+?)"


@dataclass
class DecisionEvidenceAssessment:
    required_score: float = 50.0
    preferred_score: float = 50.0
    evidence_score: float = 0.0
    adjusted_bm25: float = 0.0
    adjusted_experience: float = 50.0
    missing_critical: List[str] = field(default_factory=list)
    demonstrated_required: List[str] = field(default_factory=list)
    listed_required: List[str] = field(default_factory=list)
    score_cap: float = 100.0
    mismatch_penalty: float = 0.0


class DecisionEvidenceEngine:
    @staticmethod
    def _contains(text: str, skill: str) -> int:
        return len(re.findall(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", text, re.I))

    def _skill_evidence(self, text: str, skill: str, explicit: Set[str], inferred: Set[str], project_score: float) -> float:
        skill = str(skill or "").strip().lower()
        if not skill:
            return 0.0
        count = self._contains(text, skill)
        explicit_match = skill in explicit
        inferred_only = skill in inferred and not explicit_match and count == 0
        if inferred_only:
            return 14.0
        if count == 0 and not explicit_match and project_score <= 0:
            return 0.0

        # Resume section before work history is mainly summary/skills listing.
        lower = text.lower()
        boundary = lower.find("professional experience")
        header = lower[:boundary] if boundary > 0 else lower[: max(1200, len(lower) // 3)]
        experience = lower[boundary:] if boundary > 0 else lower
        header_count = self._contains(header, skill)
        experience_count = self._contains(experience, skill)
        action_context = len(re.findall(
            r"\b(?:" + ACTIONS + r")\b[^.;\n]{0,180}(?<!\w)" + re.escape(skill) + r"(?!\w)|"
            r"(?<!\w)" + re.escape(skill) + r"(?!\w)[^.;\n]{0,180}\b(?:" + ACTIONS + r")\b",
            experience, re.I,
        ))
        metric_context = bool(re.search(
            r"(?<!\w)" + re.escape(skill) + r"(?!\w)[^.;\n]{0,200}" + METRIC + r"|"
            + METRIC + r"[^.;\n]{0,200}(?<!\w)" + re.escape(skill) + r"(?!\w)",
            experience, re.I,
        ))

        score = 0.0
        if explicit_match or header_count:
            score = 26.0
        if experience_count:
            score = max(score, 43.0 + min(18.0, experience_count * 4.0))
        if action_context:
            score = max(score, 62.0 + min(20.0, action_context * 7.0))
        if metric_context:
            score = max(score, 84.0)
        if project_score > 0:
            score = max(score, 0.35 * score + 0.65 * project_score)
        return min(100.0, score)

    def _coverage(self, text: str, expected: Sequence[str], explicit: Set[str], inferred: Set[str], required: bool, project_evidence: Mapping[str, float]):
        expected = sorted({str(s).strip().lower() for s in expected if str(s).strip()})
        if not expected:
            return 50.0, [], [], []
        total_weight = score_sum = 0.0
        critical_missing: List[str] = []
        demonstrated: List[str] = []
        listed: List[str] = []
        for skill in expected:
            metadata = get_skill_metadata(skill)
            tier = int(metadata.get("tier", 3) or 3)
            base = max(0.5, float(metadata.get("weight", 1.0)))
            weight = base * {1: 1.75, 2: 1.30}.get(tier, 1.0)
            if str(metadata.get("importance", "")).lower() in {"critical", "core", "primary"}:
                weight *= 1.25
            if required:
                weight *= 1.15
            evidence = self._skill_evidence(text, skill, explicit, inferred, float(project_evidence.get(skill, 0.0)))
            total_weight += weight
            score_sum += weight * evidence
            if evidence >= 68:
                demonstrated.append(skill)
            elif evidence > 0:
                listed.append(skill)
            elif required and tier == 1:
                critical_missing.append(skill)
        return round(score_sum / total_weight if total_weight else 50.0, 2), critical_missing, demonstrated, listed

    def assess(self, resume_text: str, required_skills: Iterable[str], preferred_skills: Iterable[str], explicit_resume_skills: Iterable[str], inferred_resume_skills: Iterable[str], raw_bm25: float, platform_years: float, required_years: float, target_platform: str, platform_score: float, platform_marker_count: int, job_title: str = "", project_skill_evidence: Mapping[str, float] | None = None, total_years: float = 0.0, bm25_matched_terms: Iterable[str] | None = None, bm25_missing_terms: Iterable[str] | None = None) -> DecisionEvidenceAssessment:
        text = str(resume_text or "").lower()
        explicit = {str(s).strip().lower() for s in explicit_resume_skills if str(s).strip()}
        inferred = {str(s).strip().lower() for s in inferred_resume_skills if str(s).strip()}
        project = {str(k).lower(): float(v) for k, v in (project_skill_evidence or {}).items()}
        req_score, critical, demonstrated, listed = self._coverage(text, list(required_skills), explicit, inferred, True, project)
        pref_score, _, _, _ = self._coverage(text, list(preferred_skills), explicit, inferred, False, project)

        # BM25 remains a supporting lexical signal and preserves term-coverage differences.
        raw = max(0.0, min(100.0, float(raw_bm25 or 0.0)))
        matched = len(list(bm25_matched_terms or [])); missing = len(list(bm25_missing_terms or []))
        coverage = matched / max(1, matched + missing)
        adjusted_bm25 = min(82.0, 0.48 * raw + 34.0 * coverage + 6.0 * math.log1p(matched))

        req_years = max(0.0, float(required_years or 0.0))
        if target_platform:
            years = max(0.0, float(platform_years or 0.0))
            if req_years > 0:
                adjusted_exp = min(100.0, 22.0 + 78.0 * min(1.0, years / req_years))
            else:
                adjusted_exp = min(94.0, 22.0 + 24.0 * math.sqrt(years))
        else:
            years = max(0.0, float(total_years or 0.0))
            adjusted_exp = min(95.0, 35.0 + 8.0 * years) if req_years <= 0 else min(100.0, 100.0 * years / req_years)

        cap = 100.0; mismatch = 0.0
        title = str(job_title or "").lower()
        if target_platform:
            if platform_score < 35:
                cap, mismatch = 55.0, 15.0
            elif platform_score < 50:
                cap, mismatch = 68.0, 9.0
            elif platform_score < 65:
                cap, mismatch = 82.0, 4.0
            if "architect" in title and (platform_score < 72 or platform_marker_count < 3):
                cap = min(cap, 78.0); mismatch = max(mismatch, 6.0)

        return DecisionEvidenceAssessment(
            required_score=req_score,
            preferred_score=pref_score,
            evidence_score=round(0.75 * req_score + 0.25 * pref_score, 2),
            adjusted_bm25=round(adjusted_bm25, 2),
            adjusted_experience=round(adjusted_exp, 2),
            missing_critical=critical,
            demonstrated_required=demonstrated,
            listed_required=listed,
            score_cap=cap,
            mismatch_penalty=mismatch,
        )
