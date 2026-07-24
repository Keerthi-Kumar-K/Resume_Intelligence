# ==========================================================
# ATS V4.0
# Job Description Parser
# ==========================================================

import re
from pathlib import Path
from typing import Optional

from ATS.engine.domain_classifier import DomainClassifier
from ATS.engine.job_profile import JobProfile
from ATS.engine.job_splitter import JobSplitter
from ATS.engine.parser import Parser
from ATS.engine.role_classifier import RoleClassifier
from ATS.engine.skill_extractor import SkillExtractor


REQUIRED_SECTION_HEADERS = [
    "required qualifications",
    "minimum qualifications",
    "required skills",
    "must have skills",
    "must-have skills",
    "requirements",
    "qualifications",
]

PREFERRED_SECTION_HEADERS = [
    "preferred qualifications",
    "preferred skills",
    "nice to have",
    "nice-to-have",
    "desired skills",
    "bonus skills",
]

RESPONSIBILITY_SECTION_HEADERS = [
    "responsibilities",
    "job responsibilities",
    "key responsibilities",
    "what you will do",
    "what you'll do",
    "duties",
]

SUMMARY_SECTION_HEADERS = [
    "job summary",
    "position summary",
    "role summary",
    "overview",
    "about the role",
]

ALL_SECTION_HEADERS = (
    REQUIRED_SECTION_HEADERS
    + PREFERRED_SECTION_HEADERS
    + RESPONSIBILITY_SECTION_HEADERS
    + SUMMARY_SECTION_HEADERS
)

EXPERIENCE_RANGE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*"
    r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)",
    re.I,
)

MINIMUM_EXPERIENCE_PATTERN = re.compile(
    r"(?:minimum\s+of\s+|at\s+least\s+)?"
    r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)"
    r"(?:\s+of)?\s+(?:professional\s+)?experience",
    re.I,
)

GENERAL_YEARS_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)",
    re.I,
)

JOB_ID_PATTERNS = [
    re.compile(
        r"(?:job\s*id|position\s*id|requisition\s*id|req\s*id)"
        r"\s*[:#-]?\s*([a-z0-9/_-]+)",
        re.I,
    ),
]

URL_PATTERN = re.compile(
    r"https?://[^\s<>\"]+",
    re.I,
)

MANDATORY_MARKERS = [
    "must have",
    "must-have",
    "required",
    "mandatory",
    "minimum qualification",
    "minimum requirement",
    "essential",
]

PREFERRED_MARKERS = [
    "preferred",
    "nice to have",
    "nice-to-have",
    "desired",
    "bonus",
    "plus",
]

CERTIFICATION_MARKERS = [
    "certification",
    "certified",
    "certificate",
]


PORTAL_STOP_MARKERS = [
    "similar jobs",
    "create job alert",
    "create alert",
    "more jobs at",
    "search all similar jobs",
    "technology professionals",
    "copyright ©",
    "terms & conditions",
    "privacy policy",
]

PORTAL_NOISE_MARKERS = [
    "job search companies career resources",
    "dice job match score",
    "fitment dice",
    "employers have access to artificial intelligence",
    "by applying for this job",
]

SENIORITY_TITLE_MAP = {
    "intern": "Intern",
    "entry level": "Junior",
    "entry-level": "Junior",
    "junior": "Junior",
    "associate": "Junior",
    "mid level": "Mid",
    "mid-level": "Mid",
    "senior": "Senior",
    "sr.": "Senior",
    "sr ": "Senior",
    "lead": "Lead",
    "principal": "Principal",
    "architect": "Architect",
    "manager": "Manager",
    "director": "Director",
}


class JDParser:

    def __init__(self):
        self.skill_extractor = SkillExtractor()
        self.role_classifier = RoleClassifier()
        self.domain_classifier = DomainClassifier()
        self.job_splitter = JobSplitter()

    def parse_file(
        self,
        file_path,
        title: str = "",
        company: str = "",
        location: str = "",
        url: str = "",
        job_id: str = "",
    ) -> JobProfile:

        raw_text = Parser.read(file_path)

        if not title:
            title = Path(file_path).stem

        return self.parse_text(
            raw_text=raw_text,
            title=title,
            company=company,
            location=location,
            url=url,
            job_id=job_id,
        )


    def parse_file_many(self, file_path) -> list[JobProfile]:
        """
        Parse every job contained in a consolidated JD file.

        For a normal one-job file this returns a list containing one profile.
        For a consolidated Dice/portal export this returns one profile per job.
        """
        raw_text = Parser.read(file_path)
        source_name = Path(file_path).stem

        documents = self.job_splitter.split(raw_text)
        profiles = []

        for index, document in enumerate(documents, start=1):
            title = document.title or f"{source_name}_Job_{index:03d}"

            profile = self.parse_text(
                raw_text=document.raw_text,
                title=title,
                company=document.company,
                location=document.location,
                url=document.url,
                job_id=document.job_id,
            )

            # Useful traceability fields without requiring JobProfile changes.
            setattr(profile, "source_file", str(file_path))
            setattr(profile, "source_job_index", index)

            profiles.append(profile)

        return profiles

    def parse_text_many(self, raw_text: str, source_name: str = "Job") -> list[JobProfile]:
        documents = self.job_splitter.split(raw_text)
        profiles = []

        for index, document in enumerate(documents, start=1):
            profiles.append(
                self.parse_text(
                    raw_text=document.raw_text,
                    title=document.title or f"{source_name}_{index:03d}",
                    company=document.company,
                    location=document.location,
                    url=document.url,
                    job_id=document.job_id,
                )
            )

        return profiles

    def parse_text(
        self,
        raw_text: str,
        title: str = "",
        company: str = "",
        location: str = "",
        url: str = "",
        job_id: str = "",
    ) -> JobProfile:

        profile = JobProfile()

        profile.raw_text = self.clean_job_text(str(raw_text or ""))
        profile.normalized_text = self.normalize(profile.raw_text)

        profile.title = title.strip()
        profile.company = company.strip()
        profile.location = location.strip()
        profile.url = url.strip()
        profile.job_id = job_id.strip()

        if not profile.url:
            profile.url = self.extract_url(profile.raw_text)

        if not profile.job_id:
            profile.job_id = self.extract_job_id(profile.raw_text)

        profile.summary = self.extract_section(
            profile.raw_text,
            SUMMARY_SECTION_HEADERS,
        )

        profile.responsibilities = self.extract_section(
            profile.raw_text,
            RESPONSIBILITY_SECTION_HEADERS,
        )

        profile.qualifications = self.extract_qualification_text(
            profile.raw_text
        )

        (
            profile.minimum_experience,
            profile.maximum_experience,
        ) = self.extract_experience_requirements(
            profile.qualifications or profile.raw_text
        )

        profile.seniority = self.detect_seniority(
            profile.title,
            profile.minimum_experience,
        )

        temporary_skill_profile = self.build_skill_profile(profile)

        self.skill_extractor.extract(temporary_skill_profile)

        extracted_skills = temporary_skill_profile.skills

        (
            profile.required_skills,
            profile.preferred_skills,
        ) = self.classify_skills(
            profile.raw_text,
            extracted_skills,
        )

        # When portal formatting has no recognizable qualification headings,
        # retain extracted JD skills instead of returning empty score inputs.
        if not profile.required_skills and extracted_skills:
            profile.required_skills = sorted(
                {getattr(v, "name", k) for k, v in extracted_skills.items()}
            )

        profile.mandatory_requirements = self.extract_requirement_lines(
            profile.raw_text,
            MANDATORY_MARKERS,
        )

        profile.preferred_requirements = self.extract_requirement_lines(
            profile.raw_text,
            PREFERRED_MARKERS,
        )

        profile.certifications = self.extract_certifications(
            profile.raw_text
        )

        role_result = self.role_classifier.classify(
            title=profile.title,
            description=profile.raw_text,
            extracted_skills=extracted_skills,
        )

        profile.primary_role = role_result.primary_role
        profile.role_confidence = role_result.confidence
        profile.role_scores = role_result.role_scores

        domain_result = self.domain_classifier.classify(
            profile.raw_text
        )

        profile.primary_domain = domain_result.primary_domain
        profile.domain_confidence = domain_result.confidence
        profile.domain_scores = domain_result.domain_scores

        return profile

    @staticmethod
    def clean_job_text(text: str) -> str:
        """Remove portal navigation, advertisements, and similar-job content."""
        raw = str(text or "").replace("\r\n", "\n")
        lower = raw.lower()

        stop_positions = [
            lower.find(marker)
            for marker in PORTAL_STOP_MARKERS
            if lower.find(marker) >= 0
        ]
        if stop_positions:
            raw = raw[:min(stop_positions)]

        cleaned_lines = []
        for line in raw.splitlines():
            normalized = re.sub(r"\s+", " ", line).strip()
            if not normalized:
                continue
            lowered = normalized.lower()
            if any(marker in lowered for marker in PORTAL_NOISE_MARKERS):
                continue
            cleaned_lines.append(normalized)

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def normalize(text: str) -> str:

        text = str(text or "").lower()
        text = text.replace("–", "-")
        text = text.replace("—", "-")
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def extract_section(
        self,
        text: str,
        target_headers: list,
    ) -> str:

        lines = text.splitlines()

        start_index: Optional[int] = None
        captured_lines = []

        normalized_headers = {
            self.normalize_header(header)
            for header in target_headers
        }

        all_headers = {
            self.normalize_header(header)
            for header in ALL_SECTION_HEADERS
        }

        for index, line in enumerate(lines):

            normalized_line = self.normalize_header(line)

            if normalized_line in normalized_headers:
                start_index = index + 1
                break

        if start_index is None:
            return ""

        for line in lines[start_index:]:

            normalized_line = self.normalize_header(line)

            if (
                normalized_line in all_headers
                and normalized_line not in normalized_headers
            ):
                break

            captured_lines.append(line)

        return "\n".join(captured_lines).strip()

    def extract_qualification_text(self, text: str) -> str:

        required = self.extract_section(
            text,
            REQUIRED_SECTION_HEADERS,
        )

        preferred = self.extract_section(
            text,
            PREFERRED_SECTION_HEADERS,
        )

        sections = [
            section
            for section in [required, preferred]
            if section
        ]

        return "\n".join(sections).strip()

    @staticmethod
    def normalize_header(text: str) -> str:

        text = str(text or "").strip().lower()
        text = re.sub(r"[:\-–—]+$", "", text)
        text = re.sub(r"[^a-z0-9\s']", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def extract_url(text: str) -> str:

        match = URL_PATTERN.search(text or "")

        if not match:
            return ""

        return match.group(0).rstrip(".,);]")

    @staticmethod
    def extract_job_id(text: str) -> str:

        for pattern in JOB_ID_PATTERNS:

            match = pattern.search(text or "")

            if match:
                return match.group(1).strip()

        return ""

    @staticmethod
    def extract_experience_requirements(
        text: str,
    ) -> tuple[float, float]:

        range_match = EXPERIENCE_RANGE_PATTERN.search(text or "")

        if range_match:

            minimum = float(range_match.group(1))
            maximum = float(range_match.group(2))

            return minimum, maximum

        minimum_match = MINIMUM_EXPERIENCE_PATTERN.search(
            text or ""
        )

        if minimum_match:

            minimum = float(minimum_match.group(1))

            return minimum, minimum

        values = [
            float(value)
            for value in GENERAL_YEARS_PATTERN.findall(text or "")
        ]

        reasonable_values = [
            value
            for value in values
            if 0 < value <= 30
        ]

        if not reasonable_values:
            return 0.0, 0.0

        minimum = max(reasonable_values)

        return minimum, minimum

    @staticmethod
    def detect_seniority(
        title: str,
        minimum_experience: float,
    ) -> str:

        normalized_title = str(title or "").lower()

        for phrase, seniority in SENIORITY_TITLE_MAP.items():

            if phrase in normalized_title:
                return seniority

        if minimum_experience < 2:
            return "Junior"

        if minimum_experience < 5:
            return "Mid"

        if minimum_experience < 8:
            return "Senior"

        if minimum_experience < 12:
            return "Lead"

        return "Architect"

    @staticmethod
    def build_skill_profile(job_profile: JobProfile):

        class TemporarySkillProfile:
            summary = ""
            experience = ""
            projects = ""
            skills_section = ""
            certifications = ""
            skills = {}

        temporary_profile = TemporarySkillProfile()

        temporary_profile.summary = job_profile.summary
        temporary_profile.experience = job_profile.responsibilities
        temporary_profile.projects = ""
        temporary_profile.skills_section = job_profile.raw_text
        temporary_profile.certifications = "\n".join(
            job_profile.certifications
            if isinstance(job_profile.certifications, list)
            else [str(job_profile.certifications or "")]
        )

        return temporary_profile

    def classify_skills(
        self,
        text: str,
        extracted_skills: dict,
    ) -> tuple[list, list]:

        required_text = self.extract_section(
            text,
            REQUIRED_SECTION_HEADERS,
        )

        preferred_text = self.extract_section(
            text,
            PREFERRED_SECTION_HEADERS,
        )

        required_normalized = self.normalize(required_text)
        preferred_normalized = self.normalize(preferred_text)

        required_skills = []
        preferred_skills = []

        for skill_name, skill_profile in extracted_skills.items():

            canonical_name = getattr(
                skill_profile,
                "name",
                skill_name,
            )

            aliases = self.get_skill_aliases(skill_name)

            required_found = any(
                self.contains_phrase(
                    required_normalized,
                    alias,
                )
                for alias in aliases
            )

            preferred_found = any(
                self.contains_phrase(
                    preferred_normalized,
                    alias,
                )
                for alias in aliases
            )

            if required_found:
                required_skills.append(canonical_name)

            elif preferred_found:
                preferred_skills.append(canonical_name)

            else:
                required_skills.append(canonical_name)

        return (
            sorted(set(required_skills)),
            sorted(set(preferred_skills)),
        )

    def get_skill_aliases(self, skill_name: str) -> list:

        skill_data = self.skill_extractor.skills.get(
            str(skill_name).strip().lower(),
            {},
        )

        aliases = skill_data.get(
            "aliases",
            [],
        )

        canonical = skill_data.get(
            "canonical",
            skill_name,
        )

        return list(
            {
                str(skill_name).lower(),
                str(canonical).lower(),
                *[
                    str(alias).lower()
                    for alias in aliases
                ],
            }
        )

    @staticmethod
    def contains_phrase(
        text: str,
        phrase: str,
    ) -> bool:

        if not text or not phrase:
            return False

        pattern = (
            rf"(?<!\w)"
            rf"{re.escape(phrase.lower())}"
            rf"(?!\w)"
        )

        return re.search(
            pattern,
            text.lower(),
            flags=re.I,
        ) is not None

    @staticmethod
    def extract_requirement_lines(
        text: str,
        markers: list,
    ) -> list:

        results = []

        for line in str(text or "").splitlines():

            cleaned_line = re.sub(
                r"^[\s•*\-–—\d.)]+",
                "",
                line,
            ).strip()

            normalized_line = cleaned_line.lower()

            if not cleaned_line:
                continue

            if any(
                marker in normalized_line
                for marker in markers
            ):
                results.append(cleaned_line)

        return list(dict.fromkeys(results))

    @staticmethod
    def extract_certifications(text: str) -> list:

        certifications = []

        for line in str(text or "").splitlines():

            cleaned_line = re.sub(
                r"^[\s•*\-–—\d.)]+",
                "",
                line,
            ).strip()

            normalized_line = cleaned_line.lower()

            if not cleaned_line:
                continue

            if any(
                marker in normalized_line
                for marker in CERTIFICATION_MARKERS
            ):
                certifications.append(cleaned_line)

        return list(dict.fromkeys(certifications))