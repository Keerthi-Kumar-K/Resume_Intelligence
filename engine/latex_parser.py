from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResumeSections:
    summary_bullets: list[str]
    skills_block: str
    experience_1_bullets: list[str]
    experience_2_bullets: list[str]


ITEM_PATTERN = re.compile(r"\\item\s+(.*?)(?=\n\s*\\item\s+|\n\s*\\end\{itemize\})", re.DOTALL)


def read_tex(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"LaTeX template not found: {path}")
    return path.read_text(encoding="utf-8")


def _extract_itemize_after(text: str, start_pattern: str, occurrence: int = 1) -> list[str]:
    matches = list(re.finditer(start_pattern, text, flags=re.IGNORECASE | re.DOTALL))
    if len(matches) < occurrence:
        raise ValueError(f"Could not find LaTeX section matching: {start_pattern}")

    start = matches[occurrence - 1].end()
    itemize_start = text.find("\\begin{itemize}", start)
    itemize_end = text.find("\\end{itemize}", itemize_start)
    if itemize_start < 0 or itemize_end < 0:
        raise ValueError("Could not locate itemize block in LaTeX template.")

    block = text[itemize_start:itemize_end + len("\\end{itemize}")]
    return [re.sub(r"\s+", " ", item.strip()) for item in ITEM_PATTERN.findall(block)]


def extract_sections(text: str) -> ResumeSections:
    summary = _extract_itemize_after(text, r"\\section\*\{PROFESSIONAL SUMMARY:\}")

    skills_match = re.search(
        r"(\\section\*\{TECHNICAL SKILLS:\}.*?\\end\{longtable\})",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not skills_match:
        raise ValueError("Could not locate TECHNICAL SKILLS longtable.")

    exp1 = _extract_itemize_after(text, r"\\section\*\{PROFESSIONAL EXPERIENCE:\}.*?\\textbf\{Responsibilities:\}")

    first_end = text.find("\\end{itemize}", text.find("\\section*{PROFESSIONAL EXPERIENCE:}"))
    if first_end < 0:
        raise ValueError("Could not locate first experience block.")
    exp2 = _extract_itemize_after(text[first_end + len("\\end{itemize}"):], r"\\textbf\{Responsibilities:\}")

    return ResumeSections(
        summary_bullets=summary,
        skills_block=skills_match.group(1),
        experience_1_bullets=exp1,
        experience_2_bullets=exp2,
    )


def escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    result = []
    for character in text:
        result.append(replacements.get(character, character))
    return "".join(result)


def format_itemize(bullets: list[str]) -> str:
    lines = ["\\begin{itemize}"]
    for bullet in bullets:
        lines.append(f"    \\item {escape_latex(bullet.strip())}")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def _replace_first_itemize_after(text: str, start_pattern: str, bullets: list[str], offset: int = 0) -> str:
    match = re.search(start_pattern, text[offset:], flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"Cannot replace section; marker not found: {start_pattern}")

    start_search = offset + match.end()
    block_start = text.find("\\begin{itemize}", start_search)
    block_end = text.find("\\end{itemize}", block_start)
    if block_start < 0 or block_end < 0:
        raise ValueError("Cannot replace section; itemize block not found.")

    block_end += len("\\end{itemize}")
    return text[:block_start] + format_itemize(bullets) + text[block_end:]


def apply_patch(text: str, patch: dict) -> str:
    updated = _replace_first_itemize_after(
        text,
        r"\\section\*\{PROFESSIONAL SUMMARY:\}",
        patch["summary_bullets"],
    )

    updated = _replace_first_itemize_after(
        updated,
        r"\\section\*\{PROFESSIONAL EXPERIENCE:\}.*?\\textbf\{Responsibilities:\}",
        patch["experience_1_bullets"],
    )

    first_exp_start = updated.find("\\section*{PROFESSIONAL EXPERIENCE:}")
    first_exp_end = updated.find("\\end{itemize}", first_exp_start)
    updated = _replace_first_itemize_after(
        updated,
        r"\\textbf\{Responsibilities:\}",
        patch["experience_2_bullets"],
        offset=first_exp_end + len("\\end{itemize}"),
    )

    # Skills are supplied as category/value pairs. Rebuild the existing longtable
    # while preserving the original section heading and table dimensions.
    skills_rows = []
    for row in patch["skills"]:
        category = escape_latex(row["category"])
        values = ", ".join(escape_latex(value) for value in row["values"])
        skills_rows.extend([
            "\\hline",
            f"\\textbf{{{category}}} & {values} \\\\",
        ])

    skills_block = "\n".join([
        "\\section*{TECHNICAL SKILLS:}",
        "\\renewcommand{\\arraystretch}{1.15}",
        "\\begin{longtable}{|p{0.2\\textwidth}|p{0.75\\textwidth}|}",
        *skills_rows,
        "\\hline",
        "\\end{longtable}",
    ])

    updated, count = re.subn(
        r"\\section\*\{TECHNICAL SKILLS:\}.*?\\end\{longtable\}",
        lambda _: skills_block,
        updated,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if count != 1:
        raise ValueError("Could not replace TECHNICAL SKILLS section.")

    return updated
