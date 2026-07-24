import re
from pathlib import Path

from ATS.engine.parser import Parser
from ATS.engine.resume_profile import ResumeProfile


SECTION_HEADERS = {
    "summary": [
        "professional summary",
        "summary",
        "profile",
    ],
    "experience": [
        "experience",
        "professional experience",
        "work experience",
    ],
    "projects": [
        "projects",
        "project experience",
    ],
    "skills": [
        "technical skills",
        "skills",
        "technologies",
    ],
    "education": [
        "education",
    ],
    "certifications": [
        "certifications",
        "licenses",
    ],
}


class ResumeParser:

    def __init__(self):
        pass

    def parse(self, resume_path):

        profile = ResumeProfile()

        profile.filename = Path(resume_path).name
        profile.raw_text = Parser.read(resume_path)

        self.extract_sections(profile)

        return profile

    def extract_sections(self, profile):

        text = profile.raw_text.lower()

        profile.summary = self.extract_block(
            text,
            SECTION_HEADERS["summary"],
        )

        profile.experience = self.extract_block(
            text,
            SECTION_HEADERS["experience"],
        )

        profile.projects = self.extract_block(
            text,
            SECTION_HEADERS["projects"],
        )

        profile.skills_section = self.extract_block(
            text,
            SECTION_HEADERS["skills"],
        )

        profile.education = self.extract_block(
            text,
            SECTION_HEADERS["education"],
        )

        profile.certifications = self.extract_block(
            text,
            SECTION_HEADERS["certifications"],
        )

    def extract_block(self, text, headers):

        start = None
        end = len(text)

        for h in headers:

            m = re.search(
                rf"\b{re.escape(h)}\b",
                text,
                re.IGNORECASE,
            )

            if m:
                start = m.end()
                break

        if start is None:
            return ""

        positions = []

        for values in SECTION_HEADERS.values():

            for h in values:

                m = re.search(
                    rf"\b{re.escape(h)}\b",
                    text[start:],
                    re.IGNORECASE,
                )

                if m:
                    positions.append(start + m.start())

        if positions:
            end = min(positions)

        return text[start:end].strip()