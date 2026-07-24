import re
from typing import Dict

from ATS.config.skill_database import SKILL_DATABASE
from ATS.engine.skill_profile import SkillProfile


YEAR_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)",
    re.I,
)


class SkillExtractor:

    GENERIC_SKILL_NAMES = {
        "task", "tasks", "required", "preferred", "experience",
        "responsibility", "responsibilities", "requirement", "requirements",
        "candidate", "project", "projects", "solution", "solutions",
        "support", "leadership", "communication", "collaboration",
        "training", "mentorship", "customer service", "problem solving",
    }

    def __init__(self):

        self.skills = {
            name: data
            for name, data in SKILL_DATABASE.items()
            if self.get_canonical_name(name, data) not in self.GENERIC_SKILL_NAMES
        }

    def extract(self, profile):

        extracted: Dict[str, SkillProfile] = {}

        self.scan_section(
            getattr(profile, "summary", ""),
            extracted,
            "summary",
        )

        self.scan_section(
            getattr(profile, "experience", ""),
            extracted,
            "experience",
        )

        self.scan_section(
            getattr(profile, "projects", ""),
            extracted,
            "projects",
        )

        self.scan_section(
            getattr(profile, "skills_section", ""),
            extracted,
            "skills",
        )

        self.scan_section(
            getattr(profile, "certifications", ""),
            extracted,
            "certifications",
        )

        self.calculate_scores(extracted)

        self.detect_primary(extracted)

        experience_text = getattr(
            profile,
            "experience",
            "",
        )

        for skill_profile in extracted.values():

            skill_data = self.skills.get(skill_profile.name, {})
            aliases = self.get_aliases(skill_profile.name, skill_data)
            skill_profile.estimated_years = self.estimate_years(
                skill_profile.name,
                experience_text,
                aliases=aliases,
            )

        profile.skills = extracted

        return extracted

    def scan_section(
        self,
        text,
        extracted,
        section,
    ):

        normalized_text = str(text or "").lower()

        for skill_name, skill_data in self.skills.items():

            aliases = self.get_aliases(
                skill_name,
                skill_data,
            )

            total_count = 0

            for alias in aliases:

                pattern = (
                    rf"(?<!\w)"
                    rf"{re.escape(alias.lower())}"
                    rf"(?!\w)"
                )

                total_count += len(
                    re.findall(
                        pattern,
                        normalized_text,
                        flags=re.I,
                    )
                )

            if total_count == 0:

                continue

            canonical_name = self.get_canonical_name(
                skill_name,
                skill_data,
            )

            if canonical_name in self.GENERIC_SKILL_NAMES:
                continue

            if canonical_name not in extracted:

                extracted[canonical_name] = SkillProfile(
                    canonical_name
                )

            skill_profile = extracted[canonical_name]

            skill_profile.frequency += total_count

            if section == "summary":

                skill_profile.summary_mentions += total_count

            elif section == "experience":

                skill_profile.experience_mentions += total_count

            elif section == "projects":

                skill_profile.project_mentions += total_count

            elif section == "skills":

                skill_profile.skills_mentions += total_count

            elif section == "certifications":

                skill_profile.certification_mentions += total_count

    def estimate_years(
        self,
        skill_name,
        experience_text,
        aliases=None,
    ):

        text = str(experience_text or "")

        aliases = aliases or [skill_name]
        skill_positions = []

        for alias in aliases:
            skill_pattern = (
                rf"(?<!\w)"
                rf"{re.escape(str(alias))}"
                rf"(?!\w)"
            )
            skill_positions.extend(
                match.start()
                for match in re.finditer(
                    skill_pattern,
                    text,
                    flags=re.I,
                )
            )

        if not skill_positions:

            return 0.0

        detected_years = []

        for position in skill_positions:

            start = max(
                0,
                position - 150,
            )

            end = min(
                len(text),
                position + 150,
            )

            context = text[start:end]

            matches = YEAR_PATTERN.findall(context)

            detected_years.extend(
                float(value)
                for value in matches
            )

        if not detected_years:

            return 0.0

        return max(detected_years)

    def calculate_scores(
        self,
        skills,
    ):

        for skill_profile in skills.values():

            score = 0.0

            score += (
                skill_profile.summary_mentions
                * 25
            )

            score += (
                skill_profile.experience_mentions
                * 20
            )

            score += (
                skill_profile.project_mentions
                * 15
            )

            score += (
                skill_profile.skills_mentions
                * 8
            )

            score += (
                skill_profile.certification_mentions
                * 15
            )

            score += (
                skill_profile.frequency
                * 2
            )

            skill_profile.confidence = min(
                round(score, 2),
                100.0,
            )

    def detect_primary(
        self,
        skills,
    ):

        for skill_profile in skills.values():

            skill_profile.primary = (
                skill_profile.confidence >= 70
                and skill_profile.frequency >= 3
            )

    @staticmethod
    def get_canonical_name(
        skill_name,
        skill_data,
    ):

        if isinstance(skill_data, dict):

            return str(
                skill_data.get(
                    "canonical",
                    skill_name,
                )
            ).lower()

        return str(skill_name).lower()

    @staticmethod
    def get_aliases(
        skill_name,
        skill_data,
    ):

        aliases = {
            str(skill_name).lower()
        }

        if isinstance(skill_data, dict):

            canonical = skill_data.get(
                "canonical",
                skill_name,
            )

            aliases.add(
                str(canonical).lower()
            )

            for alias in skill_data.get(
                "aliases",
                [],
            ):

                aliases.add(
                    str(alias).lower()
                )

        return sorted(
            aliases,
            key=len,
            reverse=True,
        )