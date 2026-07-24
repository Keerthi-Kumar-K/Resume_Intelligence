from dataclasses import dataclass


@dataclass
class SkillProfile:

    name: str

    frequency: int = 0

    summary_mentions: int = 0

    experience_mentions: int = 0

    project_mentions: int = 0

    skills_mentions: int = 0

    certification_mentions: int = 0

    estimated_years: float = 0

    confidence: float = 0

    recent: bool = False

    primary: bool = False
    
