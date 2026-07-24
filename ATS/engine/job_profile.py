from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class JobProfile:
    job_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""

    raw_text: str = ""
    normalized_text: str = ""

    summary: str = ""
    responsibilities: str = ""
    qualifications: str = ""

    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)

    minimum_experience: float = 0.0
    maximum_experience: float = 0.0

    primary_role: str = ""
    role_confidence: float = 0.0
    role_scores: Dict[str, float] = field(default_factory=dict)

    primary_domain: str = ""
    domain_confidence: float = 0.0
    domain_scores: Dict[str, float] = field(default_factory=dict)

    seniority: str = "Unknown"

    mandatory_requirements: List[str] = field(default_factory=list)
    preferred_requirements: List[str] = field(default_factory=list)

    certifications: List[str] = field(default_factory=list)

    embedding = None