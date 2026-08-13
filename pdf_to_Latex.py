import argparse
import re
from pathlib import Path

import fitz  # PyMuPDF


# ==========================================================
# LATEX TEMPLATE
# ==========================================================

LATEX_HEADER = r"""\documentclass[a4paper,10pt]{article}

\usepackage[
    left=0.65in,
    right=0.65in,
    top=0.60in,
    bottom=0.60in
]{geometry}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}

\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{longtable}
\usepackage{array}
\usepackage{booktabs}

\hypersetup{
    colorlinks=true,
    urlcolor=blue,
    linkcolor=blue
}

\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}

\setlist[itemize]{
    leftmargin=18pt,
    itemsep=4pt,
    topsep=3pt,
    parsep=0pt
}

\titleformat{\section}
{\normalsize\bfseries}
{}
{0pt}
{}

\titlespacing{\section}
{0pt}
{8pt}
{4pt}

\begin{document}

"""

LATEX_FOOTER = r"""
\end{document}
"""


# ==========================================================
# COMMON RESUME SECTION HEADINGS
# ==========================================================

SECTION_HEADINGS = {
    "professional summary",
    "summary",
    "career summary",
    "executive summary",
    "technical summary",
    "technical skills",
    "skills",
    "core competencies",
    "certifications",
    "professional experience",
    "work experience",
    "experience",
    "education",
    "projects",
    "academic projects",
    "achievements",
    "awards",
}


# ==========================================================
# TEXT EXTRACTION
# ==========================================================

def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from a text-based PDF.

    This does not perform OCR. Scanned/image-only PDFs may produce
    little or no usable text.
    """

    document = fitz.open(pdf_path)

    pages = []

    try:
        for page in document:
            text = page.get_text("text", sort=True)

            if text:
                pages.append(text)

    finally:
        document.close()

    return "\n".join(pages)


# ==========================================================
# TEXT CLEANING
# ==========================================================

def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "--")
    text = text.replace("\u2022", "•")
    text = text.replace("\uf0b7", "•")

    # Remove repeated spaces while preserving line breaks.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


# ==========================================================
# LATEX ESCAPING
# ==========================================================

def escape_latex(text: str) -> str:
    """
    Escape characters that have special meaning in LaTeX.
    """

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

    escaped = []

    for character in text:
        escaped.append(replacements.get(character, character))

    return "".join(escaped)


# ==========================================================
# LINE CLASSIFICATION
# ==========================================================

def normalized_heading(line: str) -> str:
    value = line.strip().rstrip(":").strip().lower()
    return re.sub(r"\s+", " ", value)


def is_section_heading(line: str) -> bool:
    normalized = normalized_heading(line)

    if normalized in SECTION_HEADINGS:
        return True

    # Headings such as PROFESSIONAL SUMMARY or TECHNICAL SKILLS.
    if (
        line.isupper()
        and 2 <= len(line.split()) <= 6
        and len(line) <= 60
    ):
        return True

    return False


def is_bullet(line: str) -> bool:
    bullet_patterns = (
        "•",
        "- ",
        "* ",
        "▪",
        "●",
        "○",
        "➢",
        "",
    )

    return line.startswith(bullet_patterns)


def remove_bullet_marker(line: str) -> str:
    line = re.sub(r"^[•▪●○➢*]\s*", "", line)
    line = re.sub(r"^-\s+", "", line)

    return line.strip()


def looks_like_contact_line(line: str) -> bool:
    lower = line.lower()

    return (
        "@" in line
        or "linkedin.com" in lower
        or re.search(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", line)
        is not None
    )


def looks_like_date_or_role_line(line: str) -> bool:
    date_pattern = (
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"[a-z]*['.\s-]*\d{2,4}\b"
    )

    lower = line.lower()

    return (
        re.search(date_pattern, lower) is not None
        or lower.startswith("client:")
        or lower.startswith("role:")
        or lower.startswith("environment:")
        or lower.startswith("responsibilities:")
    )


# ==========================================================
# RESUME PARSING
# ==========================================================

def join_wrapped_lines(lines: list[str]) -> list[str]:
    """
    Join lines that appear to be continuations of the previous line.
    """

    output = []
    current = ""

    for raw_line in lines:
        line = normalize_line(raw_line)

        if not line:
            if current:
                output.append(current)
                current = ""

            output.append("")
            continue

        if (
            is_section_heading(line)
            or is_bullet(line)
            or looks_like_date_or_role_line(line)
        ):
            if current:
                output.append(current)
                current = ""

            output.append(line)
            continue

        if not current:
            current = line
            continue

        # Preserve likely name/contact lines separately.
        if looks_like_contact_line(line):
            output.append(current)
            current = line
            continue

        # Join normal wrapped text.
        current = f"{current} {line}"

    if current:
        output.append(current)

    return output


def create_latex_body(text: str) -> str:
    raw_lines = text.splitlines()
    lines = join_wrapped_lines(raw_lines)

    output = []
    itemize_open = False
    first_content_line = True

    for line in lines:
        line = line.strip()

        if not line:
            if itemize_open:
                output.append(r"\end{itemize}")
                itemize_open = False

            output.append("")
            continue

        if first_content_line:
            output.extend(
                [
                    r"\begin{center}",
                    rf"{{\LARGE \textbf{{{escape_latex(line)}}}}} \\",
                    r"\end{center}",
                    r"\hrule",
                    r"\vspace{6pt}",
                    "",
                ]
            )

            first_content_line = False
            continue

        if is_section_heading(line):
            if itemize_open:
                output.append(r"\end{itemize}")
                itemize_open = False

            heading = line.rstrip(":").strip()

            output.append(
                rf"\section*{{{escape_latex(heading.upper())}:}}"
            )

            continue

        if is_bullet(line):
            if not itemize_open:
                output.append(r"\begin{itemize}")
                itemize_open = True

            bullet_text = remove_bullet_marker(line)

            output.append(
                rf"    \item {escape_latex(bullet_text)}"
            )

            continue

        if itemize_open:
            output.append(r"\end{itemize}")
            itemize_open = False

        if looks_like_contact_line(line):
            output.append(
                rf"\begin{{center}}{escape_latex(line)}\end{{center}}"
            )

        elif looks_like_date_or_role_line(line):
            output.append(
                rf"\textbf{{{escape_latex(line)}}} \\"
            )

        else:
            output.append(
                f"{escape_latex(line)}"
            )

    if itemize_open:
        output.append(r"\end{itemize}")

    return "\n".join(output)


# ==========================================================
# AUTO-TAILORING MARKERS
# ==========================================================

def add_tailoring_markers(latex_body: str) -> str:
    """
    Add markers around sections that the future tailoring system
    is allowed to replace.
    """

    marker_map = {
        "PROFESSIONAL SUMMARY": (
            "% BEGIN_AUTO_SUMMARY",
            "% END_AUTO_SUMMARY",
        ),
        "TECHNICAL SKILLS": (
            "% BEGIN_AUTO_SKILLS",
            "% END_AUTO_SKILLS",
        ),
    }

    lines = latex_body.splitlines()
    output = []

    active_end_marker = None

    for line in lines:
        heading_match = re.match(
            r"\\section\*\{(.+?):?\}",
            line.strip(),
            re.IGNORECASE,
        )

        if heading_match:
            if active_end_marker:
                output.append(active_end_marker)
                output.append("")
                active_end_marker = None

            heading = (
                heading_match.group(1)
                .rstrip(":")
                .strip()
                .upper()
            )

            if heading in marker_map:
                start_marker, end_marker = marker_map[heading]

                output.append(start_marker)
                active_end_marker = end_marker

        output.append(line)

    if active_end_marker:
        output.append(active_end_marker)

    return "\n".join(output)


# ==========================================================
# PDF TO LATEX CONVERSION
# ==========================================================

def convert_pdf(pdf_path: Path, output_folder: Path) -> Path:
    text = extract_pdf_text(pdf_path)

    if not text.strip():
        raise ValueError(
            "No readable text was extracted. "
            "The PDF may be scanned or image-based."
        )

    cleaned_text = clean_text(text)
    latex_body = create_latex_body(cleaned_text)
    latex_body = add_tailoring_markers(latex_body)

    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / f"{pdf_path.stem}.tex"

    latex_document = (
        LATEX_HEADER
        + latex_body
        + "\n"
        + LATEX_FOOTER
    )

    output_path.write_text(
        latex_document,
        encoding="utf-8",
    )

    return output_path


def convert_folder(
    input_folder: Path,
    output_folder: Path,
) -> None:

    pdf_files = sorted(input_folder.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {input_folder}")
        return

    print(f"PDF files found: {len(pdf_files)}")
    print(f"LaTeX output folder: {output_folder}")
    print("=" * 70)

    success_count = 0
    failure_count = 0

    for index, pdf_path in enumerate(pdf_files, start=1):
        print(f"[{index}/{len(pdf_files)}] {pdf_path.name}")

        try:
            output_path = convert_pdf(
                pdf_path=pdf_path,
                output_folder=output_folder,
            )

            print(f"    Created: {output_path.name}")
            success_count += 1

        except Exception as error:
            print(f"    Failed: {error}")
            failure_count += 1

    print("=" * 70)
    print(f"Converted successfully: {success_count}")
    print(f"Failed: {failure_count}")


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Convert text-based PDF resumes into editable "
            "ATS-friendly LaTeX files."
        )
    )

    parser.add_argument(
        "--input-folder",
        required=True,
        help="Folder containing PDF resumes.",
    )

    parser.add_argument(
        "--output-folder",
        required=True,
        help="Folder where generated LaTeX files will be saved.",
    )

    arguments = parser.parse_args()

    input_folder = Path(
        arguments.input_folder
    ).expanduser().resolve()

    output_folder = Path(
        arguments.output_folder
    ).expanduser().resolve()

    if not input_folder.exists():
        raise FileNotFoundError(
            f"Input folder does not exist: {input_folder}"
        )

    if not input_folder.is_dir():
        raise NotADirectoryError(
            f"Input path is not a folder: {input_folder}"
        )

    convert_folder(
        input_folder=input_folder,
        output_folder=output_folder,
    )


if __name__ == "__main__":
    main()