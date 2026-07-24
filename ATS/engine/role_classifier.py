# ==========================================================
# ATS V4.0
# Role Classification Engine
# ==========================================================

import re
from dataclasses import dataclass, field
from typing import Dict, List

from ATS.config.role_database import DEFAULT_ROLE, ROLE_DATABASE


@dataclass
class RoleMatchResult:

    primary_role: str = DEFAULT_ROLE

    confidence: float = 0.0

    role_scores: Dict[str, float] = field(default_factory=dict)

    matched_title_aliases: List[str] = field(default_factory=list)

    matched_keywords: List[str] = field(default_factory=list)

    exclusion_matches: List[str] = field(default_factory=list)


class RoleClassifier:

    TITLE_WEIGHT = 55.0
    REQUIRED_SKILL_WEIGHT = 25.0
    PREFERRED_SKILL_WEIGHT = 10.0
    KEYWORD_WEIGHT = 10.0
    EXCLUSION_PENALTY = 40.0

    def __init__(self, role_database=None):

        self.role_database = role_database or ROLE_DATABASE

    @staticmethod
    def normalize(text: str) -> str:

        text = str(text or "").lower()

        text = re.sub(r"[_/|]+", " ", text)

        text = re.sub(r"[^a-z0-9+#.\-\s]", " ", text)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def contains_phrase(text: str, phrase: str) -> bool:

        phrase = phrase.strip().lower()

        if not phrase:

            return False

        pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"

        return re.search(pattern, text, flags=re.I) is not None

    def classify(
        self,
        title: str,
        description: str,
        extracted_skills=None,
    ) -> RoleMatchResult:

        normalized_title = self.normalize(title)

        normalized_description = self.normalize(description)

        combined_text = (
            f"{normalized_title} {normalized_description}"
        ).strip()

        extracted_skill_names = self._normalize_skill_names(
            extracted_skills
        )

        role_scores = {}

        role_details = {}

        for role_name, role_config in self.role_database.items():

            details = self._score_role(
                role_name=role_name,
                role_config=role_config,
                title_text=normalized_title,
                combined_text=combined_text,
                extracted_skills=extracted_skill_names,
            )

            role_scores[role_name] = details["score"]

            role_details[role_name] = details

        if not role_scores:

            return RoleMatchResult()

        primary_role = max(
            role_scores,
            key=lambda role: (
                role_scores[role],
                self._role_specificity(role),
            ),
        )

        primary_details = role_details[primary_role]

        return RoleMatchResult(
            primary_role=primary_role,
            confidence=round(role_scores[primary_role], 2),
            role_scores={
                role: round(score, 2)
                for role, score in sorted(
                    role_scores.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            },
            matched_title_aliases=primary_details[
                "matched_title_aliases"
            ],
            matched_keywords=primary_details[
                "matched_keywords"
            ],
            exclusion_matches=primary_details[
                "exclusion_matches"
            ],
        )


    @staticmethod
    def _role_specificity(role_name: str) -> int:
        """Prefer platform-specific roles when scores tie."""
        role = str(role_name or "").lower()
        specific_markers = (
            "databricks", "snowflake", "informatica", "ab initio",
            "tableau", "power bi", "governance", "mdm", "architect",
        )
        return sum(1 for marker in specific_markers if marker in role)

    def _score_role(
        self,
        role_name: str,
        role_config: dict,
        title_text: str,
        combined_text: str,
        extracted_skills: set,
    ) -> dict:

        title_aliases = role_config.get(
            "title_aliases",
            [],
        )

        required_skills = role_config.get(
            "required_skills",
            [],
        )

        preferred_skills = role_config.get(
            "preferred_skills",
            [],
        )

        keywords = role_config.get(
            "keywords",
            [],
        )

        excluded_keywords = role_config.get(
            "excluded_keywords",
            [],
        )

        matched_title_aliases = [
            alias
            for alias in title_aliases
            if self.contains_phrase(title_text, alias)
        ]

        matched_required_skills = [
            skill
            for skill in required_skills
            if (
                skill.lower() in extracted_skills
                or self.contains_phrase(
                    combined_text,
                    skill,
                )
            )
        ]

        matched_preferred_skills = [
            skill
            for skill in preferred_skills
            if (
                skill.lower() in extracted_skills
                or self.contains_phrase(
                    combined_text,
                    skill,
                )
            )
        ]

        matched_keywords = [
            keyword
            for keyword in keywords
            if self.contains_phrase(
                combined_text,
                keyword,
            )
        ]

        exclusion_matches = [
            keyword
            for keyword in excluded_keywords
            if self.contains_phrase(
                combined_text,
                keyword,
            )
        ]

        title_score = (
            self.TITLE_WEIGHT
            if matched_title_aliases
            else 0.0
        )

        required_score = self._coverage_score(
            matched_required_skills,
            required_skills,
            self.REQUIRED_SKILL_WEIGHT,
        )

        preferred_score = self._coverage_score(
            matched_preferred_skills,
            preferred_skills,
            self.PREFERRED_SKILL_WEIGHT,
        )

        keyword_score = self._coverage_score(
            matched_keywords,
            keywords,
            self.KEYWORD_WEIGHT,
        )

        exclusion_penalty = min(
            self.EXCLUSION_PENALTY,
            len(exclusion_matches) * 20.0,
        )

        raw_score = (
            title_score
            + required_score
            + preferred_score
            + keyword_score
            - exclusion_penalty
        )

        final_score = max(
            0.0,
            min(100.0, raw_score),
        )

        return {
            "role": role_name,
            "score": final_score,
            "matched_title_aliases": matched_title_aliases,
            "matched_required_skills": matched_required_skills,
            "matched_preferred_skills": matched_preferred_skills,
            "matched_keywords": matched_keywords,
            "exclusion_matches": exclusion_matches,
        }

    @staticmethod
    def _coverage_score(
        matched_items: List[str],
        configured_items: List[str],
        maximum_score: float,
    ) -> float:

        if not configured_items:

            return 0.0

        coverage = (
            len(set(matched_items))
            / len(set(configured_items))
        )

        return coverage * maximum_score

    @staticmethod
    def _normalize_skill_names(extracted_skills) -> set:

        if not extracted_skills:

            return set()

        if isinstance(extracted_skills, dict):

            return {
                str(skill).lower()
                for skill in extracted_skills.keys()
            }

        return {
            str(skill).lower()
            for skill in extracted_skills
        }