# ==========================================================
# ATS V4.0
# Experience Intelligence Engine
# ==========================================================

import re
from datetime import datetime

from ATS.engine.experience_profile import ExperienceProfile


CURRENT_YEAR = datetime.now().year


YEAR_RANGE_PATTERN = re.compile(

    r"(?:[A-Za-z]{3,9}\s+|\d{1,2}[/-])?(20\d{2}|19\d{2})\s*[-–—to]+\s*(?:[A-Za-z]{3,9}\s+|\d{1,2}[/-])?(Present|Current|20\d{2}|19\d{2})",

    re.I

)


SINGLE_YEAR_PATTERN = re.compile(

    r"\b(20\d{2}|19\d{2})\b"

)


YEARS_PATTERN = re.compile(

    r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)",

    re.I

)

class ExperienceEngine:

    def __init__(self):

        pass

    def extract(self, profile):

        result = ExperienceProfile()

        text = getattr(profile, "raw_text", "") or profile.experience

        result.total_years = self.extract_total_years(text)

        result.seniority = self.detect_seniority(
            result.total_years
        )

        result.skill_experience = self.skill_experience(
            text,
            profile.skills
        )

        result.confidence = self.calculate_confidence(result)

        # Persist values expected by ATS scoring and relevant-experience logic.
        profile.years_experience = result.total_years
        profile.skill_experience = result.skill_experience
        profile.seniority = result.seniority

        return result
        
    def extract_total_years(self, text):

        explicit = YEARS_PATTERN.findall(text)

        if explicit:

            return max(float(x) for x in explicit)

        ranges = YEAR_RANGE_PATTERN.findall(text)

        total = 0

        for start, end in ranges:

            start = int(start)

            if end.lower() in ["present", "current"]:

                end = CURRENT_YEAR

            else:

                end = int(end)

            if end >= start:

                total += end - start

        return float(total)
        
    def skill_experience(

            self,

            text,

            skills

    ):

        experience = {}

        total = self.extract_total_years(text)

        if total == 0:

            total = 1

        for skill in skills.values():

            score = (

                skill.experience_mentions * 2

                + skill.project_mentions

                + skill.summary_mentions

            )

            years = (

                score / 10

            ) * total

            years = min(

                total,

                round(years,1)

            )

            experience[skill.name] = years

        return experience
        
    def detect_seniority(

            self,

            years

    ):

        if years < 2:

            return "Junior"

        elif years < 5:

            return "Mid"

        elif years < 8:

            return "Senior"

        elif years < 12:

            return "Lead"

        return "Architect"
        
    def calculate_confidence(

            self,

            profile

    ):

        score = 50

        if profile.total_years > 0:

            score += 20

        if profile.skill_experience:

            score += 20

        if len(profile.skill_experience) > 10:

            score += 10

        return min(score,100)

    def estimate_relevant_years(self, profile, target_skills):
        """Estimate relevant years using extracted per-skill experience.

        Falls back conservatively to a fraction of total experience when the
        profile does not expose mention-level skill evidence.
        """
        target = {str(x or "").strip().lower() for x in (target_skills or []) if str(x or "").strip()}
        if not target:
            return float(getattr(profile, "years_experience", 0.0) or getattr(profile, "total_years", 0.0) or 0.0)

        total = float(getattr(profile, "years_experience", 0.0) or getattr(profile, "total_years", 0.0) or 0.0)
        skill_years = getattr(profile, "skill_experience", {}) or {}
        normalized = {str(k).strip().lower(): float(v or 0.0) for k, v in skill_years.items()}
        matches = [years for skill, years in normalized.items() if skill in target]
        if matches:
            return round(min(total or max(matches), max(matches)), 2)

        skills = getattr(profile, "skills", {}) or {}
        names = {str(k).strip().lower() for k in skills.keys()} if isinstance(skills, dict) else {str(x).strip().lower() for x in skills}
        coverage = len(names.intersection(target)) / max(len(target), 1)
        return round(total * min(0.75, coverage), 2)

