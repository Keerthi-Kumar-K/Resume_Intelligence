from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ResumeProfile:

    filename: str = ""

    raw_text: str = ""

    summary: str = ""

    experience: str = ""

    projects: str = ""

    skills_section: str = ""

    certifications: str = ""

    education: str = ""

    years_experience: float = 0.0

    detected_roles: List[str] = field(default_factory=list)

    domains: List[str] = field(default_factory=list)

    certifications_found: List[str] = field(default_factory=list)

    skills: Dict = field(default_factory=dict)

    embedding = None