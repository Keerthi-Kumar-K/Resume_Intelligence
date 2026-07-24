# ==========================================================
# ATS V4.0
# BM25 Keyword Relevance Engine
# ==========================================================

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Sequence, Set


# ==========================================================
# RESULT MODEL
# ==========================================================

@dataclass
class BM25Result:
    """
    Stores the BM25 comparison result between a resume and a job description.
    """

    score: float = 0.0
    raw_score: float = 0.0

    matched_terms: List[str] = field(default_factory=list)
    missing_terms: List[str] = field(default_factory=list)

    query_terms: List[str] = field(default_factory=list)
    document_terms: List[str] = field(default_factory=list)

    match_count: int = 0
    query_term_count: int = 0
    coverage: float = 0.0


# ==========================================================
# BM25 ENGINE
# ==========================================================

class BM25Engine:
    """
    Lightweight BM25 relevance engine for comparing a resume against a job
    description.

    The engine accepts strings, dictionaries, dataclasses, or profile objects.
    It extracts their text, tokenizes it, calculates BM25 relevance, and
    returns a normalized score from 0 to 100.
    """

    DEFAULT_K1 = 1.5
    DEFAULT_B = 0.75

    MIN_TOKEN_LENGTH = 2

    STOP_WORDS: Set[str] = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "can",
        "could",
        "for",
        "from",
        "has",
        "have",
        "having",
        "he",
        "her",
        "hers",
        "him",
        "his",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "may",
        "must",
        "of",
        "on",
        "or",
        "our",
        "ours",
        "shall",
        "she",
        "should",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "they",
        "this",
        "those",
        "to",
        "us",
        "was",
        "we",
        "were",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
        "job",
        "role",
        "position",
        "candidate",
        "required",
        "preferred",
        "responsibility",
        "responsibilities",
        "requirement",
        "requirements",
        "experience",
        "years",
        "year",
        "work",
        "working",
        "strong",
        "excellent",
        "good",
        "knowledge",
        "skills",
        "skill",
        "ability",
        "including",
        "using",
        "tasks", "task", "project", "projects", "solution", "solutions",
        "support", "leadership", "communication", "collaboration",
        "training", "mentorship", "benefits", "employer", "apply",
        "privacy", "copyright", "recruiter", "posted", "company",
    }

    TEXT_ATTRIBUTE_NAMES: Sequence[str] = (
        "text",
        "raw_text",
        "cleaned_text",
        "normalized_text",
        "content",
        "description",
        "job_description",
        "resume_text",
        "summary",
        "professional_summary",
        "objective",
        "title",
        "job_name",
        "role",
        "roles",
        "skills",
        "required_skills",
        "preferred_skills",
        "technical_skills",
        "certifications",
        "projects",
        "responsibilities",
        "experience",
        "work_experience",
        "education",
    )

    def __init__(
        self,
        k1: float = DEFAULT_K1,
        b: float = DEFAULT_B,
        stop_words: Optional[Iterable[str]] = None,
    ) -> None:

        self.k1 = float(k1)
        self.b = float(b)

        self.stop_words = set(self.STOP_WORDS)

        if stop_words:
            self.stop_words.update(
                str(word).strip().lower()
                for word in stop_words
                if str(word).strip()
            )

    # ======================================================
    # PUBLIC COMPARISON METHODS
    # ======================================================

    def compare(
        self,
        resume: Any = None,
        job: Any = None,
        resume_text: Any = None,
        jd_text: Any = None,
        query_terms: Optional[Iterable[str]] = None,
        jd_skills: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> BM25Result:
        """
        Compare a resume with a job description.

        Parameters
        ----------
        resume:
            Resume text or resume profile object.

        job:
            Job-description text or job profile object.

        query_terms:
            Optional explicit query terms. When omitted, the terms are
            extracted from the job description.

        Returns
        -------
        BM25Result
            Normalized score and matched/missing keyword details.
        """

        # Backward compatibility with older ATS pipeline versions
        if resume is None:
            resume = resume_text

        if job is None:
            job = jd_text

        if query_terms is None and jd_skills:
            query_terms = jd_skills

        resume_text = self._extract_text(resume)
        job_text = self._extract_text(job)

        document_tokens = self.tokenize(resume_text)

        if query_terms is None:
            query_tokens = self.tokenize(job_text)
        else:
            query_tokens = self._normalize_query_terms(query_terms)

        return self.score_tokens(
            document_tokens=document_tokens,
            query_tokens=query_tokens,
        )

    def calculate_score(
        self,
        resume: Any,
        job: Any,
        query_terms: Optional[Iterable[str]] = None,
    ) -> float:
        """
        Return only the normalized BM25 score.
        """

        return self.compare(
            resume=resume,
            job=job,
            query_terms=query_terms,
        ).score

    def score(
        self,
        resume: Any,
        job: Any,
        query_terms: Optional[Iterable[str]] = None,
    ) -> float:
        """
        Alias for calculate_score().
        """

        return self.calculate_score(
            resume=resume,
            job=job,
            query_terms=query_terms,
        )

    def calculate_bm25_score(
        self,
        resume: Any,
        job: Any,
        query_terms: Optional[Iterable[str]] = None,
    ) -> float:
        """
        Compatibility alias used by some ATS pipeline versions.
        """

        return self.calculate_score(
            resume=resume,
            job=job,
            query_terms=query_terms,
        )

    # ======================================================
    # TOKEN-LEVEL SCORING
    # ======================================================

    def score_tokens(
        self,
        document_tokens: Sequence[str],
        query_tokens: Sequence[str],
    ) -> BM25Result:

        document_tokens = [
            token
            for token in document_tokens
            if token
        ]

        query_tokens = [
            token
            for token in query_tokens
            if token
        ]

        unique_query_terms = list(dict.fromkeys(query_tokens))
        unique_document_terms = list(dict.fromkeys(document_tokens))

        if not unique_query_terms:
            return BM25Result(
                score=0.0,
                raw_score=0.0,
                matched_terms=[],
                missing_terms=[],
                query_terms=[],
                document_terms=unique_document_terms,
                match_count=0,
                query_term_count=0,
                coverage=0.0,
            )

        if not document_tokens:
            return BM25Result(
                score=0.0,
                raw_score=0.0,
                matched_terms=[],
                missing_terms=unique_query_terms,
                query_terms=unique_query_terms,
                document_terms=[],
                match_count=0,
                query_term_count=len(unique_query_terms),
                coverage=0.0,
            )

        document_frequency = Counter(document_tokens)

        document_length = len(document_tokens)

        # In a resume-vs-JD comparison there is one target document.
        # To keep the inverse document-frequency calculation useful,
        # treat matched terms as appearing in one document in a
        # two-document reference corpus.
        corpus_size = 2
        average_document_length = max(document_length, 1)

        raw_score = 0.0
        maximum_possible_score = 0.0

        matched_terms: List[str] = []
        missing_terms: List[str] = []

        query_frequency = Counter(query_tokens)

        for term in unique_query_terms:

            term_frequency = document_frequency.get(term, 0)

            if term_frequency > 0:
                matched_terms.append(term)
                document_count = 1
            else:
                missing_terms.append(term)
                document_count = 0

            idf = math.log(
                1.0
                + (
                    corpus_size
                    - document_count
                    + 0.5
                )
                / (
                    document_count
                    + 0.5
                )
            )

            query_weight = 1.0 + math.log1p(
                max(query_frequency.get(term, 1) - 1, 0)
            )

            denominator = (
                term_frequency
                + self.k1
                * (
                    1.0
                    - self.b
                    + self.b
                    * (
                        document_length
                        / average_document_length
                    )
                )
            )

            if term_frequency > 0 and denominator > 0:
                term_score = (
                    idf
                    * (
                        term_frequency
                        * (
                            self.k1
                            + 1.0
                        )
                        / denominator
                    )
                    * query_weight
                )
            else:
                term_score = 0.0

            raw_score += term_score

            maximum_denominator = (
                1.0
                + self.k1
                * (
                    1.0
                    - self.b
                    + self.b
                )
            )

            maximum_term_score = (
                idf
                * (
                    1.0
                    * (
                        self.k1
                        + 1.0
                    )
                    / maximum_denominator
                )
                * query_weight
            )

            maximum_possible_score += maximum_term_score

        query_term_count = len(unique_query_terms)
        match_count = len(matched_terms)

        coverage = (
            match_count
            / query_term_count
            if query_term_count
            else 0.0
        )

        if maximum_possible_score > 0:
            normalized_bm25 = (
                raw_score
                / maximum_possible_score
            ) * 100.0
        else:
            normalized_bm25 = 0.0

        # BM25 relevance alone can become optimistic when repeated terms
        # exist in the resume. Blend it with unique query-term coverage.
        normalized_score = (
            normalized_bm25 * 0.65
            + coverage * 100.0 * 0.35
        )

        normalized_score = self._clamp(
            normalized_score,
            0.0,
            100.0,
        )

        return BM25Result(
            score=round(normalized_score, 2),
            raw_score=round(raw_score, 6),
            matched_terms=sorted(matched_terms),
            missing_terms=sorted(missing_terms),
            query_terms=unique_query_terms,
            document_terms=unique_document_terms,
            match_count=match_count,
            query_term_count=query_term_count,
            coverage=round(coverage * 100.0, 2),
        )

    # ======================================================
    # TOKENIZATION
    # ======================================================

    def tokenize(self, value: Any) -> List[str]:
        """
        Convert arbitrary text into normalized BM25 tokens.
        """

        text = self._extract_text(value)

        if not text:
            return []

        text = text.lower()

        text = self._normalize_technical_terms(text)

        tokens = re.findall(
            r"[a-z0-9]+(?:[+#.-][a-z0-9]+)*",
            text,
        )

        normalized_tokens: List[str] = []

        for token in tokens:

            token = token.strip("-.+")

            if not token:
                continue

            if len(token) < self.MIN_TOKEN_LENGTH:
                continue

            if token in self.stop_words:
                continue

            normalized_tokens.append(token)

        return normalized_tokens

    def _normalize_query_terms(
        self,
        query_terms: Iterable[str],
    ) -> List[str]:

        normalized: List[str] = []

        for term in query_terms:

            if term is None:
                continue

            term_text = str(term).strip()

            if not term_text:
                continue

            term_tokens = self.tokenize(term_text)

            if term_tokens:
                normalized.extend(term_tokens)

        return normalized

    @staticmethod
    def _normalize_technical_terms(text: str) -> str:
        """
        Preserve common technical concepts during tokenization.
        """

        replacements = {
            "spark sql": "spark_sql",
            "apache spark": "spark",
            "pyspark": "spark",
            "databricks lakehouse": "databricks",
            "delta live tables": "dlt",
            "azure databricks": "databricks",
            "aws glue": "glue",
            "amazon s3": "s3",
            "microsoft sql server": "sql_server",
            "ms sql server": "sql_server",
            "informatica powercenter": "informatica",
            "powercenter": "informatica",
            "ab initio": "ab_initio",
            "c sharp": "c#",
            "c-sharp": "c#",
            "c plus plus": "c++",
            "node js": "nodejs",
            "node.js": "nodejs",
            "power bi": "powerbi",
            "power-bi": "powerbi",
            "machine learning": "machine_learning",
            "deep learning": "deep_learning",
            "data engineering": "data_engineering",
            "data engineer": "data_engineer",
            "data warehouse": "data_warehouse",
            "data warehousing": "data_warehousing",
            "data lake": "data_lake",
            "delta lake": "delta_lake",
            "lake house": "lakehouse",
            "lake-house": "lakehouse",
            "master data management": "master_data_management",
            "business intelligence": "business_intelligence",
            "natural language processing": "natural_language_processing",
            "large language model": "large_language_model",
            "large language models": "large_language_models",
            "azure data factory": "azure_data_factory",
            "azure synapse": "azure_synapse",
            "amazon web services": "aws",
            "google cloud platform": "gcp",
            "structured query language": "sql",
            "extract transform load": "etl",
            "extract load transform": "elt",
            "continuous integration": "continuous_integration",
            "continuous deployment": "continuous_deployment",
            "ci cd": "ci_cd",
            "ci/cd": "ci_cd",
            "role based access control": "rbac",
            "change data capture": "cdc",
        }

        for source, target in replacements.items():
            text = text.replace(source, target)

        return text

    # ======================================================
    # TEXT EXTRACTION
    # ======================================================

    def _extract_text(
        self,
        value: Any,
        visited: Optional[Set[int]] = None,
    ) -> str:
        """
        Extract useful text from strings, lists, dictionaries, dataclasses,
        or arbitrary profile objects.
        """

        if value is None:
            return ""

        if visited is None:
            visited = set()

        if isinstance(value, str):
            return value

        if isinstance(value, bytes):
            try:
                return value.decode(
                    "utf-8",
                    errors="ignore",
                )
            except Exception:
                return ""

        if isinstance(value, (int, float, bool)):
            return str(value)

        object_id = id(value)

        if object_id in visited:
            return ""

        visited.add(object_id)

        if isinstance(value, dict):

            collected_values: List[str] = []

            preferred_keys = [
                key
                for key in self.TEXT_ATTRIBUTE_NAMES
                if key in value
            ]

            remaining_keys = [
                key
                for key in value.keys()
                if key not in preferred_keys
            ]

            for key in preferred_keys + remaining_keys:
                extracted = self._extract_text(
                    value.get(key),
                    visited,
                )

                if extracted:
                    collected_values.append(extracted)

            return " ".join(collected_values)

        if isinstance(value, (list, tuple, set, frozenset)):

            collected_values = [
                self._extract_text(item, visited)
                for item in value
            ]

            return " ".join(
                item
                for item in collected_values
                if item
            )

        collected_attributes: List[str] = []

        for attribute_name in self.TEXT_ATTRIBUTE_NAMES:

            if not hasattr(value, attribute_name):
                continue

            try:
                attribute_value = getattr(
                    value,
                    attribute_name,
                )
            except Exception:
                continue

            if callable(attribute_value):
                continue

            extracted = self._extract_text(
                attribute_value,
                visited,
            )

            if extracted:
                collected_attributes.append(extracted)

        if collected_attributes:
            return " ".join(collected_attributes)

        if hasattr(value, "__dict__"):

            try:
                return self._extract_text(
                    vars(value),
                    visited,
                )
            except Exception:
                pass

        try:
            return str(value)
        except Exception:
            return ""

    # ======================================================
    # HELPERS
    # ======================================================

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        return max(
            minimum,
            min(maximum, value),
        )


# ==========================================================
# DIRECT MODULE TEST
# ==========================================================

if __name__ == "__main__":

    sample_resume = """
    Senior Data Engineer with experience in Python, SQL, PySpark,
    Databricks, Azure Data Factory, Snowflake, ETL pipelines,
    Delta Lake, Apache Spark, Airflow and Power BI.
    """

    sample_job = """
    Seeking a Data Engineer with strong Python, SQL, PySpark,
    Databricks, Delta Lake, Azure Data Factory, Kafka,
    Airflow and Snowflake experience.
    """

    engine = BM25Engine()

    result = engine.compare(
        resume=sample_resume,
        job=sample_job,
    )

    print("BM25 score:", result.score)
    print("Coverage:", result.coverage)
    print("Matched terms:", result.matched_terms)
    print("Missing terms:", result.missing_terms)