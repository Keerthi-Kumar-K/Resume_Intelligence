# ==========================================================
# ATS V4.1
# Consolidated Job Description Splitter
# ==========================================================

import re
from dataclasses import dataclass
from typing import List


@dataclass
class JobDocument:
    raw_text: str
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    job_id: str = ""


class JobSplitter:
    """
    Splits a consolidated Dice/portal export into individual job descriptions.

    The splitter uses job URLs as the strongest boundary because every scraped
    job should have one unique URL. It also supports common textual markers such
    as 'Apply Now', 'Job #', 'Job ID', 'Position ID', and 'Dice ID'.
    """

    URL_RE = re.compile(
        r"https?://(?:www\.)?(?:dice\.com|indeed\.com|linkedin\.com|ziprecruiter\.com)"
        r"/[^\s<>\"]+",
        re.I,
    )

    GENERIC_URL_RE = re.compile(r"https?://[^\s<>\"]+", re.I)

    JOB_ID_PATTERNS = [
        re.compile(
            r"(?:job\s*#|job\s*id|position\s*id|requisition\s*id|req\s*id|dice\s*id)"
            r"\s*[:#-]?\s*([a-z0-9/_-]+)",
            re.I,
        ),
    ]

    START_MARKERS = [
        re.compile(r"(?im)^\s*job\s*url\s*[:\-]\s*(https?://\S+)\s*$"),
        re.compile(r"(?im)^\s*apply\s+now\s*$"),
        re.compile(r"(?im)^\s*job\s*#\s*[:\-]?\s*[a-z0-9/_-]+\s*$"),
        re.compile(r"(?im)^\s*(?:job|position|requisition|req)\s*id\s*[:#-]"),
    ]

    TITLE_PATTERNS = [
        re.compile(r"(?im)^\s*job\s*title\s*[:\-]\s*(.+?)\s*$"),
        re.compile(r"(?im)^\s*position\s*title\s*[:\-]\s*(.+?)\s*$"),
        re.compile(r"(?im)^\s*title\s*[:\-]\s*(.+?)\s*$"),
    ]

    COMPANY_PATTERNS = [
        re.compile(r"(?im)^\s*company\s*[:\-]\s*(.+?)\s*$"),
        re.compile(r"(?im)^\s*employer\s*[:\-]\s*(.+?)\s*$"),
    ]

    LOCATION_PATTERNS = [
        re.compile(r"(?im)^\s*location\s*[:\-]\s*(.+?)\s*$"),
    ]

    def split(self, text: str) -> List[JobDocument]:
        text = self._clean_text(text)
        if not text:
            return []

        chunks = self._split_by_urls(text)

        if len(chunks) <= 1:
            chunks = self._split_by_markers(text)

        if len(chunks) <= 1:
            return [self._build_document(text)]

        jobs = []
        seen = set()

        for chunk in chunks:
            chunk = chunk.strip()
            if not self._looks_like_job(chunk):
                continue

            job = self._build_document(chunk)
            key = (
                job.url.lower(),
                job.job_id.lower(),
                self._normalize(job.title),
            )

            if key in seen:
                continue

            seen.add(key)
            jobs.append(job)

        return jobs or [self._build_document(text)]

    def _split_by_urls(self, text: str) -> List[str]:
        matches = list(self.URL_RE.finditer(text))

        if len(matches) < 2:
            matches = list(self.GENERIC_URL_RE.finditer(text))

        if len(matches) < 2:
            return [text]

        starts = []
        for match in matches:
            start = self._find_job_start(text, match.start())
            if not starts or start > starts[-1]:
                starts.append(start)

        starts = sorted(set(starts))
        if len(starts) < 2:
            return [text]

        chunks = []
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

        return chunks

    def _split_by_markers(self, text: str) -> List[str]:
        positions = []

        for pattern in self.START_MARKERS:
            positions.extend(match.start() for match in pattern.finditer(text))

        positions = sorted(set(positions))

        if len(positions) < 2:
            return [text]

        chunks = []
        for index, start in enumerate(positions):
            end = positions[index + 1] if index + 1 < len(positions) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

        return chunks

    @staticmethod
    def _find_job_start(text: str, url_start: int) -> int:
        """
        Keep a small header block immediately before the URL. This preserves
        title/company lines when the exporter writes metadata before the URL.
        """
        line_start = text.rfind("\n", 0, url_start)
        search_start = max(0, url_start - 1200)
        prefix = text[search_start:url_start]

        header_patterns = [
            r"(?im)^job\s*title\s*[:\-]",
            r"(?im)^position\s*title\s*[:\-]",
            r"(?im)^company\s*[:\-]",
            r"(?im)^job\s*#\s*[:\-]?",
            r"(?im)^job\s*id\s*[:\-]?",
        ]

        candidate = None
        for pattern in header_patterns:
            found = list(re.finditer(pattern, prefix))
            if found:
                absolute = search_start + found[-1].start()
                candidate = absolute if candidate is None else min(candidate, absolute)

        return candidate if candidate is not None else max(0, line_start + 1)

    def _build_document(self, text: str) -> JobDocument:
        return JobDocument(
            raw_text=text.strip(),
            title=self._extract_first(text, self.TITLE_PATTERNS) or self._infer_title(text),
            company=self._extract_first(text, self.COMPANY_PATTERNS),
            location=self._extract_first(text, self.LOCATION_PATTERNS),
            url=self._extract_url(text),
            job_id=self._extract_job_id(text),
        )

    @staticmethod
    def _extract_first(text: str, patterns) -> str:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_url(self, text: str) -> str:
        match = self.URL_RE.search(text) or self.GENERIC_URL_RE.search(text)
        return match.group(0).rstrip(".,);]") if match else ""

    def _extract_job_id(self, text: str) -> str:
        for pattern in self.JOB_ID_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _infer_title(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        ignored = (
            "http://",
            "https://",
            "job search",
            "apply now",
            "job details",
            "skills",
            "summary",
            "posted ",
            "updated ",
            "full time",
            "contract",
            "dice id",
            "position id",
            "job id",
            "job #",
        )

        for line in lines[:25]:
            low = line.lower()
            if any(low.startswith(value) for value in ignored):
                continue
            if 3 <= len(line) <= 160:
                return line

        return ""

    @staticmethod
    def _looks_like_job(text: str) -> bool:
        low = text.lower()
        signals = [
            "job description",
            "responsibilities",
            "required qualifications",
            "required skills",
            "qualifications",
            "apply now",
            "job details",
            "position id",
            "job id",
            "dice id",
        ]
        return len(text) >= 250 and sum(signal in low for signal in signals) >= 1

    @staticmethod
    def _clean_text(text: str) -> str:
        text = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "").strip().lower())
