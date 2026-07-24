# ==========================================================
# ATS V4.0
# Domain Intelligence Engine
# ==========================================================

import re

from dataclasses import dataclass, field

from ATS.config.domain_database import DOMAIN_DATABASE


@dataclass
class DomainResult:

    primary_domain: str = "Unknown"

    confidence: float = 0.0

    domain_scores: dict = field(default_factory=dict)

    matched_keywords: dict = field(default_factory=dict)


class DomainClassifier:

    def __init__(self):

        self.database = DOMAIN_DATABASE


    @staticmethod
    def normalize(text):

        text = text.lower()

        text = re.sub(r"\s+", " ", text)

        return text


    @staticmethod
    def contains(text, phrase):

        pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"

        return re.search(pattern, text) is not None


    def classify(self, text):

        text = self.normalize(text)

        scores = {}

        matched = {}

        for domain, data in self.database.items():

            keywords = data["keywords"]

            found = []

            for keyword in keywords:

                if self.contains(text, keyword):

                    found.append(keyword)

            if keywords:

                score = len(found) / len(keywords) * 100

            else:

                score = 0

            scores[domain] = round(score, 2)

            matched[domain] = found

        best_domain = max(scores, key=scores.get)

        return DomainResult(

            primary_domain=best_domain,

            confidence=scores[best_domain],

            domain_scores=scores,

            matched_keywords=matched

        )