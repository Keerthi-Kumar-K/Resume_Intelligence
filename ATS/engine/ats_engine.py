# ==========================================================
# ATS Final 1.0
# Core ATS Ranking Engine
# Part 1: Models, Initialization, Comparison Pipeline
# ==========================================================

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ATS.engine.bm25_engine import BM25Engine
from ATS.engine.domain_classifier import DomainClassifier
from ATS.engine.experience_engine import ExperienceEngine
from ATS.engine.role_classifier import RoleClassifier
from ATS.engine.semantic_engine import SemanticEngine
from ATS.engine.skill_extractor import SkillExtractor
from ATS.engine.ontology_engine import SkillOntologyEngine
from ATS.engine.impact_engine import ImpactEngine
from ATS.scoring import (
    PlatformExpertiseEngine, EvidenceEngine, AchievementRelevanceEngine,
    RoleHierarchyEngine, FinalRanker, DecisionEvidenceEngine, ProjectEvidenceEngine,
)
from ATS.config.skill_database import get_skill_metadata
from ATS.config.role_database import ROLE_DATABASE, ROLE_COMPATIBILITY, PLATFORM_CORE_SKILLS


# ==========================================================
# DEFAULT SCORING WEIGHTS
# ==========================================================

DEFAULT_WEIGHTS = {
    "platform": 0.30,
    "role": 0.15,
    "required_skills": 0.22,
    "preferred_skills": 0.04,
    "experience": 0.13,
    "semantic": 0.025,
    "bm25": 0.025,
    "domain": 0.005,
    "certification": 0.005,
    "achievement": 0.05,
    "complexity": 0.05,
}


# ==========================================================
# SCORE THRESHOLDS
# ==========================================================

APPLY_THRESHOLD = 85.0
STRONG_MATCH_THRESHOLD = 75.0
REVIEW_THRESHOLD = 65.0


# ==========================================================
# COMPONENT SCORE MODEL
# ==========================================================

@dataclass
class ATSComponentScores:

    platform_score: float = 0.0
    tiered_skill_score: float = 0.0
    relevant_experience_score: float = 0.0
    required_skill_score: float = 0.0
    preferred_skill_score: float = 0.0
    semantic_score: float = 0.0
    bm25_score: float = 0.0
    role_score: float = 0.0
    experience_score: float = 0.0
    domain_score: float = 0.0
    certification_score: float = 0.0
    achievement_score: float = 0.0
    complexity_score: float = 0.0

    missing_required_penalty: float = 0.0
    role_mismatch_penalty: float = 0.0
    experience_penalty: float = 0.0
    core_skill_penalty: float = 0.0
    core_skill_bonus: float = 0.0
    critical_skill_penalty: float = 0.0
    platform_mismatch_penalty: float = 0.0

    weighted_score: float = 0.0
    total_penalty: float = 0.0
    final_score: float = 0.0


# ==========================================================
# ATS MATCH RESULT MODEL
# ==========================================================

@dataclass
class ATSMatchResult:

    job_id: str = ""
    job_name: str = ""
    job_url: str = ""

    resume_name: str = ""

    final_score: float = 0.0
    recommendation: str = "LOW MATCH"

    scores: ATSComponentScores = field(
        default_factory=ATSComponentScores
    )

    matched_required_skills: List[str] = field(
        default_factory=list
    )

    missing_required_skills: List[str] = field(
        default_factory=list
    )

    matched_preferred_skills: List[str] = field(
        default_factory=list
    )

    missing_preferred_skills: List[str] = field(
        default_factory=list
    )

    matched_certifications: List[str] = field(
        default_factory=list
    )

    missing_certifications: List[str] = field(
        default_factory=list
    )

    resume_role: str = ""
    job_role: str = ""

    resume_domain: str = ""
    job_domain: str = ""

    resume_experience: float = 0.0
    required_experience: float = 0.0

    bm25_matched_terms: List[str] = field(
        default_factory=list
    )

    bm25_missing_terms: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )

    inferred_resume_skills: List[str] = field(default_factory=list)
    inferred_job_skills: List[str] = field(default_factory=list)
    resume_specialization: str = ""
    specialization_confidence: float = 0.0
    achievements: List[str] = field(default_factory=list)
    complexity_signals: List[str] = field(default_factory=list)
    target_platform: str = ""
    platform_evidence: List[str] = field(default_factory=list)
    platform_years: float = 0.0
    platform_hard_gate_cap: float = 100.0
    strong_skill_evidence: List[str] = field(default_factory=list)
    weak_skill_evidence: List[str] = field(default_factory=list)
    demonstrated_required_skills: List[str] = field(default_factory=list)
    listed_required_skills: List[str] = field(default_factory=list)
    evidence_score: float = 0.0
    project_count: int = 0
    strong_project_count: int = 0
    evidence_summary: str = ""

    error: str = ""


# ==========================================================
# JOB RANKING RESULT MODEL
# ==========================================================

@dataclass
class JobRankingResult:

    job_id: str = ""
    job_name: str = ""
    job_url: str = ""

    best_resume: str = ""
    best_score: float = 0.0
    recommendation: str = ""

    rankings: List[ATSMatchResult] = field(
        default_factory=list
    )


# ==========================================================
# ATS RANKING ENGINE
# ==========================================================

class ATSRankingEngine:

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ):

        self.weights = (
            weights.copy()
            if weights
            else DEFAULT_WEIGHTS.copy()
        )

        self._validate_weights()

        self.skill_extractor = SkillExtractor()

        self.role_classifier = RoleClassifier()

        self.domain_classifier = DomainClassifier()

        self.experience_engine = ExperienceEngine()

        self.bm25_engine = BM25Engine()

        self.semantic_engine = SemanticEngine()

        self.ontology_engine = SkillOntologyEngine()
        self.impact_engine = ImpactEngine()
        self.platform_engine = PlatformExpertiseEngine()
        self.evidence_engine = EvidenceEngine()
        self.achievement_relevance_engine = AchievementRelevanceEngine()
        self.role_hierarchy_engine = RoleHierarchyEngine()
        self.final_ranker = FinalRanker()
        self.decision_evidence_engine = DecisionEvidenceEngine()
        self.project_evidence_engine = ProjectEvidenceEngine()

    # ======================================================
    # PUBLIC METHOD: COMPARE ONE RESUME TO ONE JOB
    # ======================================================

    def compare(
        self,
        resume_profile: Any,
        job_profile: Any,
    ) -> ATSMatchResult:

        result = ATSMatchResult(
            job_id=str(
                getattr(
                    job_profile,
                    "job_id",
                    "",
                )
                or ""
            ),
            job_name=str(
                getattr(
                    job_profile,
                    "title",
                    "",
                )
                or ""
            ),
            job_url=str(
                getattr(
                    job_profile,
                    "url",
                    "",
                )
                or ""
            ),
            resume_name=self._get_resume_name(
                resume_profile
            ),
        )

        try:

            self._prepare_resume_profile(
                resume_profile
            )

            self._prepare_job_profile(
                job_profile
            )

            resume_text = self._get_resume_text(
                resume_profile
            )

            job_text = self._get_job_text(
                job_profile
            )

            resume_skills = self._get_skill_names(
                getattr(
                    resume_profile,
                    "skills",
                    {},
                )
            )

            # ATS V6: deterministic ontology expansion. Explicit skills remain
            # distinguishable from inferred concepts for transparent scoring.
            explicit_resume_skills = list(resume_skills)
            resume_inference = self.ontology_engine.infer(resume_skills)
            result.inferred_resume_skills = sorted(resume_inference.inferred_skills)
            result.resume_specialization, result.specialization_confidence, _ = (
                self.ontology_engine.detect_specialization(resume_inference.explicit_skills)
            )
            resume_skills = sorted(resume_inference.all_skills)

            required_skills = self._normalize_list(
                getattr(
                    job_profile,
                    "required_skills",
                    [],
                )
            )

            preferred_skills = self._normalize_list(
                getattr(
                    job_profile,
                    "preferred_skills",
                    [],
                )
            )

            job_inference = self.ontology_engine.infer(required_skills + preferred_skills)
            result.inferred_job_skills = sorted(job_inference.inferred_skills)
            required_explicit = set(required_skills)
            preferred_explicit = set(preferred_skills)
            # Inferred JD concepts are supporting signals, not new mandatory requirements.
            preferred_skills = sorted(preferred_explicit | job_inference.inferred_skills)

            (
                result.matched_required_skills,
                result.missing_required_skills,
            ) = self._compare_skill_lists(
                resume_skills,
                required_skills,
            )

            (
                result.matched_preferred_skills,
                result.missing_preferred_skills,
            ) = self._compare_skill_lists(
                resume_skills,
                preferred_skills,
            )

            semantic_result = (
                self.semantic_engine.compare(
                    resume_text=resume_text,
                    jd_text=job_text,
                )
            )

            bm25_result = self.bm25_engine.compare(
                resume_text=resume_text,
                jd_text=job_text,
                jd_skills=(
                    required_skills
                    + preferred_skills
                ),
            )

            result.scores.semantic_score = (
                semantic_result.score
            )

            result.scores.bm25_score = (
                bm25_result.score
            )

            result.bm25_matched_terms = (
                bm25_result.matched_terms
            )

            result.bm25_missing_terms = (
                bm25_result.missing_terms
            )

            self._populate_role_details(
                result=result,
                resume_profile=resume_profile,
                job_profile=job_profile,
                resume_text=resume_text,
                job_text=job_text,
                resume_skills=resume_skills,
            )

            self._populate_domain_details(
                result=result,
                resume_profile=resume_profile,
                job_profile=job_profile,
                resume_text=resume_text,
                job_text=job_text,
            )

            self._populate_experience_details(
                result=result,
                resume_profile=resume_profile,
                job_profile=job_profile,
            )

            self._populate_certification_details(
                result=result,
                resume_profile=resume_profile,
                job_profile=job_profile,
            )

            # ATS V7: target-conditioned evidence, achievements and complexity.
            role_cfg = ROLE_DATABASE.get(result.job_role, {})
            result.target_platform = self.platform_engine.detect_target(
                result.job_name, required_skills + preferred_skills, role_cfg.get("platform", "")
            )
            # Final version: project evidence is calculated once and becomes the
            # authoritative source for platform tenure and project-backed depth.
            project_assessment = self.project_evidence_engine.assess(
                resume_text, result.target_platform, required_skills, result.resume_role
            )
            platform_assessment = self.platform_engine.assess(
                resume_text, resume_skills, result.target_platform, result.job_name
            )
            if result.target_platform:
                result.scores.platform_score = round(
                    0.35 * platform_assessment.score + 0.65 * project_assessment.platform_score, 2
                )
            else:
                result.scores.platform_score = 50.0
            result.scores.platform_mismatch_penalty = max(
                result.scores.platform_mismatch_penalty, platform_assessment.mismatch_penalty
            )
            result.platform_evidence = platform_assessment.explicit_markers
            result.platform_years = project_assessment.platform_years
            result.platform_hard_gate_cap = platform_assessment.hard_gate_cap
            result.project_count = project_assessment.project_count
            result.strong_project_count = project_assessment.strong_projects
            result.evidence_summary = project_assessment.evidence_summary

            target_terms = set(required_skills) | set(preferred_skills) | set(platform_assessment.explicit_markers)
            evidence = self.evidence_engine.assess(resume_text, target_terms)
            result.strong_skill_evidence = evidence.strong_evidence
            result.weak_skill_evidence = evidence.weak_evidence
            result.scores.tiered_skill_score = round(
                0.65 * result.scores.tiered_skill_score + 0.35 * evidence.score, 2
            )

            impact_result = self.achievement_relevance_engine.assess(resume_text, target_terms)
            result.scores.achievement_score = impact_result.achievement_score
            result.scores.complexity_score = impact_result.complexity_score
            result.achievements = impact_result.relevant_achievements
            result.complexity_signals = impact_result.relevant_complexity

            self._calculate_component_scores(
                result=result,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
            )

            self._evaluate_recruiter_alignment(
                result=result,
                resume_profile=resume_profile,
                job_profile=job_profile,
                resume_skills=resume_skills,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                job_title=result.job_name,
            )

            result.scores.role_score = self.role_hierarchy_engine.score(
                result.resume_role, result.job_role, result.scores.role_score
            )

            # _evaluate_recruiter_alignment contains legacy platform coverage.
            # Restore the final project/specialization-conditioned platform score
            # so the legacy pass cannot flatten tailored resume differences.
            if result.target_platform:
                result.scores.platform_score = round(
                    0.35 * platform_assessment.score + 0.65 * project_assessment.platform_score, 2
                )
            else:
                result.scores.platform_score = 50.0

            # Platform-specific evidence, not total tenure, drives platform roles.
            if result.target_platform:
                platform_exp_score = self._calculate_experience_score(
                    result.platform_years, result.required_experience
                )
                result.scores.relevant_experience_score = platform_exp_score
                result.scores.experience_score = round(
                    0.80 * platform_exp_score + 0.20 * result.scores.experience_score, 2
                )

            # Project evidence was already calculated above; do not recalculate
            # or overwrite platform years with a second heuristic.
            project_skill_evidence = project_assessment.skill_evidence

            # ATS V9: evidence quality replaces binary keyword coverage.
            decision_evidence = self.decision_evidence_engine.assess(
                resume_text=resume_text,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                explicit_resume_skills=explicit_resume_skills,
                inferred_resume_skills=result.inferred_resume_skills,
                raw_bm25=result.scores.bm25_score,
                platform_years=result.platform_years,
                required_years=result.required_experience,
                target_platform=result.target_platform,
                platform_score=result.scores.platform_score,
                platform_marker_count=len(result.platform_evidence),
                job_title=result.job_name,
                project_skill_evidence=project_skill_evidence,
                total_years=result.resume_experience,
                bm25_matched_terms=result.bm25_matched_terms,
                bm25_missing_terms=result.bm25_missing_terms,
            )
            result.scores.required_skill_score = decision_evidence.required_score
            result.scores.preferred_skill_score = decision_evidence.preferred_score
            result.scores.bm25_score = decision_evidence.adjusted_bm25
            result.scores.experience_score = decision_evidence.adjusted_experience
            result.scores.relevant_experience_score = decision_evidence.adjusted_experience
            result.evidence_score = decision_evidence.evidence_score
            result.demonstrated_required_skills = decision_evidence.demonstrated_required
            result.listed_required_skills = decision_evidence.listed_required
            result.scores.critical_skill_penalty = max(
                result.scores.critical_skill_penalty,
                min(18.0, len(decision_evidence.missing_critical) * 6.0),
            )
            result.scores.platform_mismatch_penalty = max(
                result.scores.platform_mismatch_penalty,
                decision_evidence.mismatch_penalty,
            )
            result.platform_hard_gate_cap = min(
                result.platform_hard_gate_cap, decision_evidence.score_cap
            )

            self._calculate_final_score(result)

            result.recommendation = (
                self._get_recommendation(
                    result.final_score
                )
            )

            self._generate_warnings(result)

        except Exception as error:

            result.error = str(error)

            result.final_score = 0.0

            result.recommendation = "ERROR"

        result.weights = self.weights.copy()
        return result

    # ======================================================
    # PUBLIC METHOD: RANK RESUMES FOR ONE JOB
    # ======================================================

    def rank_resumes(
        self,
        resume_profiles: List[Any],
        job_profile: Any,
    ) -> JobRankingResult:

        match_results = []

        for resume_profile in resume_profiles:

            match_result = self.compare(
                resume_profile=resume_profile,
                job_profile=job_profile,
            )

            match_results.append(
                match_result
            )

        match_results.sort(
            key=lambda item: item.final_score,
            reverse=True,
        )

        ranking_result = JobRankingResult(
            job_id=str(
                getattr(
                    job_profile,
                    "job_id",
                    "",
                )
                or ""
            ),
            job_name=str(
                getattr(
                    job_profile,
                    "title",
                    "",
                )
                or ""
            ),
            job_url=str(
                getattr(
                    job_profile,
                    "url",
                    "",
                )
                or ""
            ),
            rankings=match_results,
        )

        if match_results:

            best_match = match_results[0]

            ranking_result.best_resume = (
                best_match.resume_name
            )

            ranking_result.best_score = (
                best_match.final_score
            )

            ranking_result.recommendation = (
                best_match.recommendation
            )

        return ranking_result

    # ======================================================
    # PUBLIC METHOD: RANK RESUMES FOR MULTIPLE JOBS
    # ======================================================

    def rank_jobs(
        self,
        resume_profiles: List[Any],
        job_profiles: List[Any],
    ) -> List[JobRankingResult]:

        results = []

        for job_profile in job_profiles:

            ranking = self.rank_resumes(
                resume_profiles=resume_profiles,
                job_profile=job_profile,
            )

            results.append(ranking)

        return results

    # ======================================================
    # PROFILE PREPARATION
    # ======================================================

    def _prepare_resume_profile(
        self,
        resume_profile: Any,
    ) -> None:

        existing_skills = getattr(
            resume_profile,
            "skills",
            None,
        )

        if not existing_skills:

            self.skill_extractor.extract(
                resume_profile
            )

        if not float(getattr(resume_profile, "years_experience", 0.0) or 0.0):
            self.experience_engine.extract(resume_profile)

    def _prepare_job_profile(
        self,
        job_profile: Any,
    ) -> None:

        if not hasattr(
            job_profile,
            "required_skills",
        ):

            job_profile.required_skills = []

        if not hasattr(
            job_profile,
            "preferred_skills",
        ):

            job_profile.preferred_skills = []

    # ======================================================
    # TEXT EXTRACTION
    # ======================================================

    @staticmethod
    def _get_resume_text(
        resume_profile: Any,
    ) -> str:

        raw_text = getattr(
            resume_profile,
            "raw_text",
            "",
        )

        if raw_text:

            return str(raw_text)

        sections = [
            getattr(
                resume_profile,
                "summary",
                "",
            ),
            getattr(
                resume_profile,
                "experience",
                "",
            ),
            getattr(
                resume_profile,
                "projects",
                "",
            ),
            getattr(
                resume_profile,
                "skills_section",
                "",
            ),
            getattr(
                resume_profile,
                "certifications",
                "",
            ),
            getattr(
                resume_profile,
                "education",
                "",
            ),
        ]

        return "\n".join(
            str(section)
            for section in sections
            if section
        )

    @staticmethod
    def _get_job_text(
        job_profile: Any,
    ) -> str:

        raw_text = getattr(
            job_profile,
            "raw_text",
            "",
        )

        if raw_text:

            return str(raw_text)

        sections = [
            getattr(
                job_profile,
                "title",
                "",
            ),
            getattr(
                job_profile,
                "summary",
                "",
            ),
            getattr(
                job_profile,
                "responsibilities",
                "",
            ),
            getattr(
                job_profile,
                "qualifications",
                "",
            ),
        ]

        return "\n".join(
            str(section)
            for section in sections
            if section
        )

    # ======================================================
    # NORMALIZATION HELPERS
    # ======================================================

    @staticmethod
    def _get_resume_name(
        resume_profile: Any,
    ) -> str:

        for attribute in [
            "filename",
            "file_name",
            "name",
        ]:

            value = getattr(
                resume_profile,
                attribute,
                "",
            )

            if value:

                return str(value)

        return "Unknown Resume"

    @staticmethod
    def _get_skill_names(
        skills: Any,
    ) -> List[str]:

        if not skills:

            return []

        if isinstance(skills, dict):

            values = skills.keys()

        else:

            values = skills

        return sorted(
            {
                str(value).strip().lower()
                for value in values
                if str(value).strip()
            }
        )

    @staticmethod
    def _normalize_list(
        values: Any,
    ) -> List[str]:

        if not values:

            return []

        if isinstance(values, str):

            values = [
                values
            ]

        return sorted(
            {
                str(value).strip().lower()
                for value in values
                if str(value).strip()
            }
        )

    @staticmethod
    def _compare_skill_lists(
        resume_skills: List[str],
        job_skills: List[str],
    ) -> tuple[List[str], List[str]]:

        resume_skill_set = set(
            resume_skills
        )

        matched = []

        missing = []

        for skill in job_skills:

            if skill in resume_skill_set:

                matched.append(skill)

            else:

                missing.append(skill)

        return (
            sorted(matched),
            sorted(missing),
        )

    # ======================================================
    # WEIGHT VALIDATION
    # ======================================================

    def _validate_weights(self) -> None:

        required_keys = set(
            DEFAULT_WEIGHTS.keys()
        )

        supplied_keys = set(
            self.weights.keys()
        )

        missing_keys = (
            required_keys
            - supplied_keys
        )

        if missing_keys:

            raise ValueError(
                "Missing ATS weights: "
                + ", ".join(
                    sorted(missing_keys)
                )
            )

        total_weight = sum(
            float(
                self.weights[key]
            )
            for key in required_keys
        )

        if abs(total_weight - 1.0) > 0.001:

            raise ValueError(
                "ATS scoring weights must total 1.0. "
                f"Current total: {total_weight:.4f}"
            )

    # ======================================================
    # METHODS IMPLEMENTED IN PART 2
    # ======================================================

    def _populate_role_details(
        self,
        result,
        resume_profile,
        job_profile,
        resume_text,
        job_text,
        resume_skills,
    ):

        raise NotImplementedError(
            "Add ATS Engine Part 2."
        )

    def _populate_domain_details(
        self,
        result,
        resume_profile,
        job_profile,
        resume_text,
        job_text,
    ):

        raise NotImplementedError(
            "Add ATS Engine Part 2."
        )

    def _populate_experience_details(
        self,
        result,
        resume_profile,
        job_profile,
    ):

        raise NotImplementedError(
            "Add ATS Engine Part 2."
        )

    def _populate_certification_details(
        self,
        result,
        resume_profile,
        job_profile,
    ):

        raise NotImplementedError(
            "Add ATS Engine Part 2."
        )

    def _calculate_component_scores(
        self,
        result,
        required_skills,
        preferred_skills,
    ):

        raise NotImplementedError(
            "Add ATS Engine Part 2."
        )

    def _calculate_final_score(
        self,
        result,
    ):

        raise NotImplementedError(
            "Add ATS Engine Part 2."
        )

    @staticmethod
    def _get_recommendation(
        score: float,
    ) -> str:

        if score >= APPLY_THRESHOLD:

            return "APPLY"

        if score >= STRONG_MATCH_THRESHOLD:

            return "STRONG MATCH"

        if score >= REVIEW_THRESHOLD:

            return "REVIEW"

        return "LOW MATCH"

    @staticmethod
    def _generate_warnings(
        result: ATSMatchResult,
    ) -> None:

        if result.missing_required_skills:

            result.warnings.append(
                "Missing required skills: "
                + ", ".join(
                    result.missing_required_skills
                )
            )

        if result.scores.role_mismatch_penalty > 0:

            result.warnings.append(
                "Resume role does not strongly match "
                "the job role."
            )

        if result.scores.experience_penalty > 0:

            result.warnings.append(
                "Resume experience is below the "
                "job requirement."
            )
    # ======================================================
    # ROLE MATCHING
    # ======================================================

    def _populate_role_details(
        self,
        result,
        resume_profile,
        job_profile,
        resume_text,
        job_text,
        resume_skills,
    ):

        resume_role = getattr(
            resume_profile,
            "primary_role",
            "",
        )

        resume_role_confidence = float(
            getattr(
                resume_profile,
                "role_confidence",
                0.0,
            )
            or 0.0
        )

        if not resume_role:

            resume_title = self._get_resume_title(
                resume_profile
            )

            resume_role_result = (
                self.role_classifier.classify(
                    title=resume_title,
                    description=resume_text,
                    extracted_skills=resume_skills,
                )
            )

            resume_role = (
                resume_role_result.primary_role
            )

            resume_role_confidence = (
                resume_role_result.confidence
            )

            setattr(
                resume_profile,
                "primary_role",
                resume_role,
            )

            setattr(
                resume_profile,
                "role_confidence",
                resume_role_confidence,
            )

            setattr(
                resume_profile,
                "role_scores",
                resume_role_result.role_scores,
            )

        job_role = getattr(
            job_profile,
            "primary_role",
            "",
        )

        job_role_confidence = float(
            getattr(
                job_profile,
                "role_confidence",
                0.0,
            )
            or 0.0
        )

        if not job_role:

            job_role_result = (
                self.role_classifier.classify(
                    title=str(
                        getattr(
                            job_profile,
                            "title",
                            "",
                        )
                        or ""
                    ),
                    description=job_text,
                    extracted_skills=(
                        getattr(
                            job_profile,
                            "required_skills",
                            [],
                        )
                        or []
                    ),
                )
            )

            job_role = (
                job_role_result.primary_role
            )

            job_role_confidence = (
                job_role_result.confidence
            )

            setattr(
                job_profile,
                "primary_role",
                job_role,
            )

            setattr(
                job_profile,
                "role_confidence",
                job_role_confidence,
            )

            setattr(
                job_profile,
                "role_scores",
                job_role_result.role_scores,
            )

        result.resume_role = str(
            resume_role or ""
        ).lower()

        result.job_role = str(
            job_role or ""
        ).lower()

        result.scores.role_score = (
            self._calculate_role_score(
                resume_role=result.resume_role,
                job_role=result.job_role,
                resume_confidence=resume_role_confidence,
                job_confidence=job_role_confidence,
                resume_profile=resume_profile,
                job_profile=job_profile,
            )
        )

    def _calculate_role_score(
        self,
        resume_role,
        job_role,
        resume_confidence,
        job_confidence,
        resume_profile,
        job_profile,
    ):
        resume_role = str(resume_role or "").strip().lower()
        job_role = str(job_role or "").strip().lower()
        if not resume_role or not job_role:
            return 35.0

        compatibility = ROLE_COMPATIBILITY.get(job_role, {}).get(resume_role)
        if compatibility is None:
            compatibility = ROLE_COMPATIBILITY.get(resume_role, {}).get(job_role)
        if compatibility is None:
            resume_family = ROLE_DATABASE.get(resume_role, {}).get("role_family")
            job_family = ROLE_DATABASE.get(job_role, {}).get("role_family")
            compatibility = 65.0 if resume_family and resume_family == job_family else 30.0

        confidence = max(0.55, min(1.0, (float(resume_confidence or 0) + float(job_confidence or 0)) / 200.0))
        # Compatibility is authoritative; confidence only tempers uncertain classification.
        return round(compatibility * (0.85 + 0.15 * confidence), 2)

    # ======================================================
    # DOMAIN MATCHING
    # ======================================================

    def _populate_domain_details(
        self,
        result,
        resume_profile,
        job_profile,
        resume_text,
        job_text,
    ):

        resume_domain = getattr(
            resume_profile,
            "primary_domain",
            "",
        )

        resume_domain_confidence = float(
            getattr(
                resume_profile,
                "domain_confidence",
                0.0,
            )
            or 0.0
        )

        if not resume_domain:

            resume_domain_result = (
                self.domain_classifier.classify(
                    resume_text
                )
            )

            resume_domain = (
                resume_domain_result.primary_domain
            )

            resume_domain_confidence = (
                resume_domain_result.confidence
            )

            setattr(
                resume_profile,
                "primary_domain",
                resume_domain,
            )

            setattr(
                resume_profile,
                "domain_confidence",
                resume_domain_confidence,
            )

            setattr(
                resume_profile,
                "domain_scores",
                resume_domain_result.domain_scores,
            )

        job_domain = getattr(
            job_profile,
            "primary_domain",
            "",
        )

        job_domain_confidence = float(
            getattr(
                job_profile,
                "domain_confidence",
                0.0,
            )
            or 0.0
        )

        if not job_domain:

            job_domain_result = (
                self.domain_classifier.classify(
                    job_text
                )
            )

            job_domain = (
                job_domain_result.primary_domain
            )

            job_domain_confidence = (
                job_domain_result.confidence
            )

            setattr(
                job_profile,
                "primary_domain",
                job_domain,
            )

            setattr(
                job_profile,
                "domain_confidence",
                job_domain_confidence,
            )

            setattr(
                job_profile,
                "domain_scores",
                job_domain_result.domain_scores,
            )

        result.resume_domain = str(
            resume_domain or ""
        ).lower()

        result.job_domain = str(
            job_domain or ""
        ).lower()

        result.scores.domain_score = (
            self._calculate_domain_score(
                resume_domain=result.resume_domain,
                job_domain=result.job_domain,
                resume_confidence=resume_domain_confidence,
                job_confidence=job_domain_confidence,
                resume_profile=resume_profile,
                job_profile=job_profile,
            )
        )

    def _calculate_domain_score(
        self,
        resume_domain,
        job_domain,
        resume_confidence,
        job_confidence,
        resume_profile,
        job_profile,
    ):

        unknown_values = {
            "",
            "unknown",
            "none",
        }

        if (
            resume_domain in unknown_values
            or job_domain in unknown_values
        ):

            return 50.0

        if resume_domain == job_domain:

            confidence_factor = min(
                1.0,
                (
                    resume_confidence
                    + job_confidence
                ) / 100.0,
            )

            return round(
                80.0
                + confidence_factor * 20.0,
                2,
            )

        resume_scores = getattr(
            resume_profile,
            "domain_scores",
            {},
        ) or {}

        job_scores = getattr(
            job_profile,
            "domain_scores",
            {},
        ) or {}

        resume_support = float(
            resume_scores.get(
                job_domain,
                0.0,
            )
            or 0.0
        )

        job_support = float(
            job_scores.get(
                resume_domain,
                0.0,
            )
            or 0.0
        )

        cross_domain_score = (
            resume_support
            + job_support
        ) / 2.0

        if cross_domain_score > 0:

            return round(
                min(
                    70.0,
                    max(
                        30.0,
                        cross_domain_score,
                    ),
                ),
                2,
            )

        return 35.0

    # ======================================================
    # EXPERIENCE MATCHING
    # ======================================================

    def _populate_experience_details(
        self,
        result,
        resume_profile,
        job_profile,
    ):

        resume_experience = self._extract_resume_years(
            resume_profile
        )

        required_experience = float(
            getattr(
                job_profile,
                "minimum_experience",
                0.0,
            )
            or 0.0
        )

        result.resume_experience = round(
            resume_experience,
            2,
        )

        result.required_experience = round(
            required_experience,
            2,
        )

        result.scores.experience_score = (
            self._calculate_experience_score(
                resume_years=resume_experience,
                required_years=required_experience,
            )
        )

    def _extract_resume_years(
        self,
        resume_profile,
    ):

        direct_values = [
            getattr(
                resume_profile,
                "years_experience",
                0.0,
            ),
            getattr(
                resume_profile,
                "total_years",
                0.0,
            ),
        ]

        for value in direct_values:

            try:

                numeric_value = float(
                    value or 0.0
                )

                if numeric_value > 0:

                    return numeric_value

            except (
                TypeError,
                ValueError,
            ):

                pass

        experience_text = str(
            getattr(
                resume_profile,
                "experience",
                "",
            )
            or ""
        )

        if not experience_text:

            return 0.0

        try:

            extracted_years = (
                self.experience_engine.extract_total_years(
                    experience_text
                )
            )

            setattr(
                resume_profile,
                "years_experience",
                extracted_years,
            )

            return float(
                extracted_years or 0.0
            )

        except Exception:

            return 0.0

    @staticmethod
    def _calculate_experience_score(
        resume_years,
        required_years,
    ):

        resume_years = max(
            float(
                resume_years or 0.0
            ),
            0.0,
        )

        required_years = max(
            float(
                required_years or 0.0
            ),
            0.0,
        )

        if required_years <= 0:

            return 75.0

        if resume_years >= required_years:

            excess_years = (
                resume_years
                - required_years
            )

            bonus = min(
                excess_years * 2.0,
                10.0,
            )

            return round(
                min(
                    100.0,
                    90.0 + bonus,
                ),
                2,
            )

        ratio = (
            resume_years
            / required_years
        )

        return round(
            max(
                0.0,
                ratio * 90.0,
            ),
            2,
        )

    # ======================================================
    # CERTIFICATION MATCHING
    # ======================================================

    def _populate_certification_details(
        self,
        result,
        resume_profile,
        job_profile,
    ):

        resume_certifications = (
            self._extract_certification_names(
                getattr(
                    resume_profile,
                    "certifications",
                    [],
                )
            )
        )

        job_certifications = (
            self._extract_certification_names(
                getattr(
                    job_profile,
                    "certifications",
                    [],
                )
            )
        )

        (
            result.matched_certifications,
            result.missing_certifications,
        ) = self._compare_certifications(
            resume_certifications,
            job_certifications,
        )

        result.scores.certification_score = (
            self._calculate_certification_score(
                matched=(
                    result.matched_certifications
                ),
                missing=(
                    result.missing_certifications
                ),
                required=job_certifications,
            )
        )

    @staticmethod
    def _extract_certification_names(
        certifications,
    ):

        if not certifications:

            return []

        if isinstance(
            certifications,
            str,
        ):

            lines = certifications.splitlines()

        elif isinstance(
            certifications,
            dict,
        ):

            lines = list(
                certifications.keys()
            )

        else:

            lines = list(certifications)

        normalized = []

        for item in lines:

            value = str(
                item or ""
            ).strip().lower()

            if not value:

                continue

            normalized.append(value)

        return sorted(
            set(normalized)
        )

    @staticmethod
    def _compare_certifications(
        resume_certifications,
        job_certifications,
    ):

        matched = []
        missing = []

        resume_text = " ".join(
            resume_certifications
        )

        for certification in job_certifications:

            certification_words = {
                word
                for word in certification.split()
                if len(word) >= 3
            }

            exact_match = (
                certification in resume_text
            )

            word_match = False

            if certification_words:

                matched_words = sum(
                    1
                    for word in certification_words
                    if word in resume_text
                )

                word_match = (
                    matched_words
                    / len(certification_words)
                    >= 0.6
                )

            if exact_match or word_match:

                matched.append(
                    certification
                )

            else:

                missing.append(
                    certification
                )

        return (
            sorted(matched),
            sorted(missing),
        )

    @staticmethod
    def _calculate_certification_score(
        matched,
        missing,
        required,
    ):

        if not required:

            return 75.0

        total = len(
            set(required)
        )

        matched_count = len(
            set(matched)
        )

        if total == 0:

            return 75.0

        coverage = (
            matched_count
            / total
        )

        return round(
            coverage * 100.0,
            2,
        )

    # ======================================================
    # COMPONENT SCORE CALCULATION
    # ======================================================

    def _calculate_component_scores(
        self,
        result,
        required_skills,
        preferred_skills,
    ):

        result.scores.required_skill_score = (
            self._calculate_skill_coverage_score(
                matched=(
                    result.matched_required_skills
                ),
                expected=required_skills,
                empty_default=70.0,
            )
        )

        result.scores.preferred_skill_score = (
            self._calculate_skill_coverage_score(
                matched=(
                    result.matched_preferred_skills
                ),
                expected=preferred_skills,
                empty_default=75.0,
            )
        )

        result.scores.missing_required_penalty = (
            self._calculate_missing_required_penalty(
                missing_required=(
                    result.missing_required_skills
                ),
                total_required=required_skills,
            )
        )

        result.scores.role_mismatch_penalty = (
            self._calculate_role_mismatch_penalty(
                role_score=result.scores.role_score,
                resume_role=result.resume_role,
                job_role=result.job_role,
            )
        )

        result.scores.experience_penalty = (
            self._calculate_experience_penalty(
                resume_years=(
                    result.resume_experience
                ),
                required_years=(
                    result.required_experience
                ),
            )
        )

    @staticmethod
    def _calculate_skill_coverage_score(
        matched,
        expected,
        empty_default,
    ):

        expected_set = {
            str(skill).strip().lower()
            for skill in expected
            if str(skill).strip()
        }

        matched_set = {
            str(skill).strip().lower()
            for skill in matched
            if str(skill).strip()
        }

        if not expected_set:

            return float(
                empty_default
            )

        coverage = (
            len(
                matched_set.intersection(
                    expected_set
                )
            )
            / len(expected_set)
        )

        return round(
            coverage * 100.0,
            2,
        )

    @staticmethod
    def _calculate_missing_required_penalty(
        missing_required,
        total_required,
    ):

        total_count = len(
            set(total_required)
        )

        missing_count = len(
            set(missing_required)
        )

        if total_count == 0:

            return 0.0

        missing_ratio = (
            missing_count
            / total_count
        )

        if missing_ratio >= 0.75:

            return 25.0

        if missing_ratio >= 0.50:

            return 18.0

        if missing_ratio >= 0.30:

            return 10.0

        if missing_ratio > 0:

            return 4.0

        return 0.0

    @staticmethod
    def _calculate_role_mismatch_penalty(
        role_score,
        resume_role,
        job_role,
    ):

        if not resume_role or not job_role:

            return 0.0

        if resume_role == job_role:

            return 0.0

        if role_score < 30:

            return 20.0

        if role_score < 50:

            return 12.0

        if role_score < 65:

            return 6.0

        return 0.0

    @staticmethod
    def _calculate_experience_penalty(
        resume_years,
        required_years,
    ):

        resume_years = float(
            resume_years or 0.0
        )

        required_years = float(
            required_years or 0.0
        )

        if (
            required_years <= 0
            or resume_years >= required_years
        ):

            return 0.0

        gap = (
            required_years
            - resume_years
        )

        if gap >= 5:

            return 15.0

        if gap >= 3:

            return 10.0

        if gap >= 1:

            return 5.0

        return 2.0

    # ======================================================
    # RECRUITER-STYLE PLATFORM AND TIERED-SKILL ALIGNMENT
    # ======================================================

    def _evaluate_recruiter_alignment(
        self, result, resume_profile, job_profile, resume_skills,
        required_skills, preferred_skills, job_title,
    ):
        resume_set = {str(x).strip().lower() for x in (resume_skills or [])}
        required = {str(x).strip().lower() for x in (required_skills or [])}
        preferred = {str(x).strip().lower() for x in (preferred_skills or [])}
        job_role_cfg = ROLE_DATABASE.get(result.job_role, {})

        # Determine the dominant platform from the classified role, title and
        # explicit Tier-1 JD skills.  No job is rejected when no platform exists.
        platform = str(job_role_cfg.get("platform", "") or "").lower()
        title = str(job_title or "").lower()
        platform_candidates = []
        for name, core in PLATFORM_CORE_SKILLS.items():
            evidence = (2 if name in title else 0) + len(set(core).intersection(required))
            if evidence:
                platform_candidates.append((evidence, name))
        if platform_candidates:
            platform = max(platform_candidates)[1]

        def canonical(skill):
            return str(get_skill_metadata(skill).get("canonical", skill)).strip().lower()

        resume_set = {canonical(x) for x in resume_set}
        required = {canonical(x) for x in required}
        preferred = {canonical(x) for x in preferred}
        core_skills = {canonical(x) for x in PLATFORM_CORE_SKILLS.get(platform, [])}
        core_skills.update(skill for skill in required if get_skill_metadata(skill).get("tier") == 1)

        if core_skills:
            matched_core = core_skills.intersection(resume_set)
            core_coverage = len(matched_core) / len(core_skills)
            result.scores.platform_score = round(core_coverage * 100.0, 2)

            # ATS V6 specialization is inferred from resume content, not filenames.
            specialization = str(getattr(result, "resume_specialization", "") or "").lower()

            if specialization and platform:
                if specialization == platform:
                    result.scores.platform_score = max(result.scores.platform_score, 95.0)
                elif platform in {"databricks", "snowflake", "informatica", "ab initio"}:
                    result.scores.platform_score = min(result.scores.platform_score, 45.0)
                    result.scores.platform_mismatch_penalty = max(
                        result.scores.platform_mismatch_penalty, 8.0
                    )

            core_coverage = result.scores.platform_score / 100.0
            if core_coverage < 0.20:
                result.scores.platform_mismatch_penalty = 18.0
            elif core_coverage < 0.40:
                result.scores.platform_mismatch_penalty = 10.0
            elif core_coverage >= 0.80:
                result.scores.core_skill_bonus = 4.0
        else:
            # Generic/non-platform roles remain scoreable and neutral.
            result.scores.platform_score = 50.0

        if not required and job_role_cfg:
            required = {canonical(x) for x in job_role_cfg.get("required_skills", [])}
            preferred = {canonical(x) for x in job_role_cfg.get("preferred_skills", [])}
            result.matched_required_skills = sorted(required.intersection(resume_set))
            result.missing_required_skills = sorted(required.difference(resume_set))
            result.matched_preferred_skills = sorted(preferred.intersection(resume_set))
            result.missing_preferred_skills = sorted(preferred.difference(resume_set))
            result.scores.required_skill_score = self._calculate_skill_coverage_score(
                result.matched_required_skills, required, 50.0
            )
            result.scores.preferred_skill_score = self._calculate_skill_coverage_score(
                result.matched_preferred_skills, preferred, 50.0
            )

        all_jd_skills = required.union(preferred)
        weighted_total = 0.0
        weighted_matched = 0.0
        critical_missing = 0
        for skill in all_jd_skills:
            metadata = get_skill_metadata(skill)
            weight = float(metadata.get("weight", 1.0))
            # Required skills carry more recruiter importance.
            if skill in required:
                weight *= 1.35
            weighted_total += weight
            if skill in resume_set:
                weighted_matched += weight
            elif metadata.get("tier") == 1 and skill in required:
                critical_missing += 1

        result.scores.tiered_skill_score = round(
            100.0 * weighted_matched / weighted_total if weighted_total else 72.0,
            2,
        )
        # Feed tiered score into the legacy fields consumed by reports.
        result.scores.required_skill_score = round(
            0.65 * result.scores.required_skill_score + 0.35 * result.scores.tiered_skill_score,
            2,
        )
        result.scores.critical_skill_penalty = min(18.0, critical_missing * 6.0)

        relevant_targets = core_skills or required
        relevant_years = self.experience_engine.estimate_relevant_years(
            resume_profile, relevant_targets
        ) if hasattr(self.experience_engine, "estimate_relevant_years") else result.resume_experience
        required_years = result.required_experience
        result.scores.relevant_experience_score = self._calculate_experience_score(
            relevant_years, required_years
        )
        # Blend total and relevant experience; platform roles favor relevance.
        relevance_weight = 0.70 if core_skills else 0.40
        result.scores.experience_score = round(
            relevance_weight * result.scores.relevant_experience_score
            + (1.0 - relevance_weight) * result.scores.experience_score,
            2,
        )

    # ======================================================
    # FINAL SCORE
    # ======================================================

    def _calculate_final_score(self, result):
        s = result.scores
        weighted_score, total_penalty, final_score = self.final_ranker.calculate(
            s,
            self.weights,
            getattr(result, "platform_hard_gate_cap", 100.0),
            bool(getattr(result, "target_platform", "")),
        )
        s.weighted_score = weighted_score
        s.total_penalty = total_penalty
        s.final_score = final_score
        result.final_score = final_score

    # ======================================================
    # RESUME TITLE HELPER
    # ======================================================

    @staticmethod
    def _get_resume_title(
        resume_profile,
    ):

        detected_roles = getattr(
            resume_profile,
            "detected_roles",
            [],
        )

        if detected_roles:

            if isinstance(
                detected_roles,
                str,
            ):

                return detected_roles

            return str(
                detected_roles[0]
            )

        job_titles = getattr(
            resume_profile,
            "job_titles",
            [],
        )

        if job_titles:

            if isinstance(
                job_titles,
                str,
            ):

                return job_titles

            return str(
                job_titles[0]
            )

        filename = str(getattr(resume_profile, "filename", "") or "")
        lowered = filename.lower().replace("_", " ").replace("-", " ")
        if "databricks" in lowered:
            return "databricks engineer " + lowered
        if "snowflake" in lowered:
            return "snowflake engineer " + lowered
        if "informatica" in lowered or "ab initio" in lowered or "abinitio" in lowered:
            return "etl developer informatica ab initio " + lowered
        summary = str(getattr(resume_profile, "summary", "") or "")
        return f"{filename} {summary[:250]}".strip()

