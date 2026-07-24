from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ExperienceProfile:

    total_years: float = 0.0

    seniority: str = "Unknown"

    skill_experience: Dict[str, float] = field(default_factory=dict)

    companies: List[str] = field(default_factory=list)

    job_titles: List[str] = field(default_factory=list)

    confidence: float = 0.0