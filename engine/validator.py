from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any


# ==========================================================
# NUMBER PATTERN
# ==========================================================

NUMBER_PATTERN = re.compile(

    r"(?<!\w)"
    r"(?:"
    r"\d{4}"                       # years
    r"|"
    r"\d+(?:\.\d+)?%"             # 45%, 98.5%
    r"|"
    r"\d+(?:\.\d+)?[MK]\+?"       # 1M+, 50M+
    r"|"
    r"\d+(?:\.\d+)?[xX](?!\w)"    # 3x
    r"|"
    r"\d+(?:\.\d+)?"              # normal numbers
    r")"
    r"(?!\w)",

    re.IGNORECASE,
)


# ==========================================================
# NORMALIZATION
# ==========================================================

def _normalize(
    value: str,
) -> str:

    if value is None:
        return ""

    value = str(value).strip().lower()

    # Normalize escaped percentage
    value = value.replace(
        "\\%",
        "%",
    )

    # Remove LaTeX approximation token
    value = value.replace(
        "\\textasciitilde",
        "",
    )

    # Normalize spacing
    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


# ==========================================================
# GENERATED TEXT
# ==========================================================

def _all_generated_text(
    patch: dict[str, Any],
) -> str:
    """
    Return ONLY model-generated textual areas.

    Technical skills are excluded because the current
    architecture preserves the original technical skills
    and only reorders them deterministically.
    """

    values: list[str] = []

    values.extend(
        patch.get(
            "summary_bullets",
            [],
        )
    )

    values.extend(
        patch.get(
            "experience_1_bullets",
            [],
        )
    )

    values.extend(
        patch.get(
            "experience_2_bullets",
            [],
        )
    )

    return "\n".join(
        str(value)
        for value in values
    )


# ==========================================================
# APPROVED NUMBERS
# ==========================================================

def _approved_numbers(
    evidence: dict,
    source_text: str,
) -> set[str]:
    """
    Build the set of numeric claims already supported by:

    1. Original resume LaTeX
    2. Approved evidence JSON

    Conservative variants are also allowed.

    Example:
        1M+  -> 1M allowed
        50M+ -> 50M allowed

    But:
        1M+ does NOT allow 2M
        99.5% does NOT allow 100%
    """

    evidence_text = json.dumps(
        evidence,
        ensure_ascii=False,
    )

    combined = (
        source_text
        + "\n"
        + evidence_text
    )

    numbers = NUMBER_PATTERN.findall(
        combined
    )

    approved: set[str] = set()

    for number in numbers:

        normalized = _normalize(
            number
        )

        approved.add(
            normalized
        )

        # --------------------------------------------------
        # Allow removal of trailing "+" only.
        #
        # 1M+  -> 1M
        # 50M+ -> 50M
        # --------------------------------------------------

        if normalized.endswith("+"):

            approved.add(
                normalized[:-1]
            )

    return approved


# ==========================================================
# STRUCTURE VALIDATION
# ==========================================================

def _validate_structure(
    patch: dict[str, Any],
    errors: list[str],
) -> None:

    required_keys = [

        "summary_bullets",

        "skills",

        "skills_latex",

        "experience_1_bullets",

        "experience_2_bullets",

        "unsupported_requirements",

        "change_notes",
    ]

    for key in required_keys:

        if key not in patch:

            errors.append(
                f"Missing patch key: {key}"
            )

    if errors:
        return

    # ------------------------------------------------------
    # Fields expected to be lists
    # ------------------------------------------------------

    list_fields = [

        "summary_bullets",

        "skills",

        "experience_1_bullets",

        "experience_2_bullets",

        "unsupported_requirements",

        "change_notes",
    ]

    for key in list_fields:

        if not isinstance(
            patch.get(key),
            list,
        ):

            errors.append(
                f"Patch field must be a list: {key}"
            )

    # ------------------------------------------------------
    # Deterministic LaTeX skills block
    # ------------------------------------------------------

    if not isinstance(
        patch.get(
            "skills_latex"
        ),
        str,
    ):

        errors.append(
            "skills_latex must be a string."
        )


# ==========================================================
# COUNT VALIDATION
# ==========================================================

def _validate_counts(
    patch: dict[str, Any],
    errors: list[str],
) -> None:

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    summary_count = len(
        patch.get(
            "summary_bullets",
            [],
        )
    )

    if not (
        4 <= summary_count <= 7
    ):

        errors.append(
            "Summary must contain 4-7 bullets."
        )

    # ------------------------------------------------------
    # Assurant
    # ------------------------------------------------------

    exp1_count = len(
        patch.get(
            "experience_1_bullets",
            [],
        )
    )

    if not (
        6 <= exp1_count <= 10
    ):

        errors.append(
            "Experience 1 must contain 6-10 bullets."
        )

    # ------------------------------------------------------
    # Community Dreams
    # ------------------------------------------------------

    exp2_count = len(
        patch.get(
            "experience_2_bullets",
            [],
        )
    )

    if not (
        5 <= exp2_count <= 9
    ):

        errors.append(
            "Experience 2 must contain 5-9 bullets."
        )

    # IMPORTANT:
    #
    # Skills count is NOT validated.
    #
    # Technical skills are preserved from the original
    # template and only reordered by Python.


# ==========================================================
# DUPLICATE BULLETS
# ==========================================================

def _validate_duplicates(
    patch: dict[str, Any],
    errors: list[str],
) -> None:

    for key in [

        "summary_bullets",

        "experience_1_bullets",

        "experience_2_bullets",

    ]:

        bullets = patch.get(
            key,
            [],
        )

        normalized = [

            _normalize(
                bullet
            )

            for bullet in bullets
        ]

        counts = Counter(
            normalized
        )

        duplicates = [

            bullet

            for bullet, count
            in counts.items()

            if (
                bullet
                and
                count > 1
            )
        ]

        if duplicates:

            errors.append(
                f"Duplicate bullets in {key}: "
                f"{duplicates}"
            )


# ==========================================================
# BULLET LENGTH
# ==========================================================

def _validate_bullet_lengths(
    patch: dict[str, Any],
    errors: list[str],
) -> None:

    for key in [

        "summary_bullets",

        "experience_1_bullets",

        "experience_2_bullets",

    ]:

        for bullet in patch.get(
            key,
            [],
        ):

            text = str(
                bullet
            )

            if len(text) > 450:

                errors.append(
                    f"Bullet exceeds 450 characters "
                    f"in {key}: "
                    f"{text[:100]}..."
                )


# ==========================================================
# NUMERIC VALIDATION
# ==========================================================

def _validate_numbers(
    patch: dict[str, Any],
    evidence: dict,
    source_text: str,
    errors: list[str],
) -> None:

    allowed_numbers = _approved_numbers(
        evidence,
        source_text,
    )

    generated_text = _all_generated_text(
        patch
    )

    generated_numbers = NUMBER_PATTERN.findall(
        generated_text
    )

    for number in generated_numbers:

        normalized = _normalize(
            number
        )

        # --------------------------------------------------
        # Ignore meaningless accidental 1x
        # --------------------------------------------------

        if normalized.endswith("x"):

            try:

                multiplier = float(
                    normalized[:-1]
                )

                if multiplier < 2:
                    continue

            except ValueError:
                pass

        # --------------------------------------------------
        # Exact or conservative approved metric
        # --------------------------------------------------

        if normalized not in allowed_numbers:

            errors.append(
                "Unapproved numeric claim detected: "
                f"{number}"
            )


# ==========================================================
# EXPERIENCE ISOLATION
# ==========================================================

def _validate_experience_isolation(
    patch: dict[str, Any],
    errors: list[str],
) -> None:

    # ======================================================
    # ASSURANT
    # ======================================================

    assurant_text = " ".join(
        patch.get(
            "experience_1_bullets",
            [],
        )
    ).lower()

    community_only_phrases = [

        "payroll",

        "headcount",

        "attrition",

        "time-to-hire",

        "time to hire",

        "workforce planning",

        "workforce dashboard",

        "workforce analytics",

        "employee master",

        "employee data",

        "compensation dimension",

        "salary band",

        "job grade",

        "hr source",

        "hrms",

        "cost-per-hire",

        "cost per hire",
    ]

    for phrase in community_only_phrases:

        if phrase in assurant_text:

            errors.append(
                "Experience isolation violation: "
                "Assurant contains "
                "Community Dreams/HRMS fact: "
                f"{phrase}"
            )

    # ======================================================
    # COMMUNITY DREAMS
    # ======================================================

    community_text = " ".join(
        patch.get(
            "experience_2_bullets",
            [],
        )
    ).lower()

    assurant_only_phrases = [

        "warranty claim",

        "warranty claims",

        "warranty analytics",

        "claims adjudication",

        "claim approval",

        "claims approval",

        "device protection",

        "fraud detection",

        "fraud pattern",

        "fraud hit rate",

        "policy data",

        "insurance program",

        "insurance claims",

        "actuarial",

        "pci-dss",
    ]

    for phrase in assurant_only_phrases:

        if phrase in community_text:

            errors.append(
                "Experience isolation violation: "
                "Community Dreams contains "
                "Assurant/insurance fact: "
                f"{phrase}"
            )


# ==========================================================
# EMPLOYER / DATE HEADER VALIDATION
# ==========================================================

def _validate_no_headers(
    patch: dict[str, Any],
    errors: list[str],
) -> None:

    patterns = [

        r"\bsenior data engineer at\b",

        r"\bdata engineer at\b",

        r"\bassurant\s*\(",

        r"\bcommunity dreams\s*\(",

        r"\bjul\s+20\d{2}\b",

        r"\bsep\s+20\d{2}\b",

        r"\bpresent\s*\)",
    ]

    for key in [

        "experience_1_bullets",

        "experience_2_bullets",

    ]:

        bullets = patch.get(
            key,
            [],
        )

        for bullet in bullets:

            text = str(
                bullet
            ).lower()

            for pattern in patterns:

                if re.search(
                    pattern,
                    text,
                ):

                    errors.append(
                        "Experience bullet contains "
                        "employer/role/date header text: "
                        f"{str(bullet)[:120]}"
                    )

                    break


# ==========================================================
# SKILLS LATEX STRUCTURE VALIDATION
# ==========================================================

def _validate_skills_latex(
    patch: dict[str, Any],
    errors: list[str],
) -> None:
    """
    Technical skills are deterministic.

    No individual skill evidence validation is required because
    the contents come directly from the selected base template.

    We only verify that the LaTeX block is structurally present.
    """

    skills_latex = patch.get(
        "skills_latex",
        "",
    )

    if not skills_latex:

        errors.append(
            "skills_latex is empty."
        )

        return

    if "\\section*" not in skills_latex:

        errors.append(
            "skills_latex missing section declaration."
        )

    if "\\begin{longtable}" not in skills_latex:

        errors.append(
            "skills_latex missing longtable start."
        )

    if "\\end{longtable}" not in skills_latex:

        errors.append(
            "skills_latex missing longtable end."
        )

    if "\\textbf{" not in skills_latex:

        errors.append(
            "skills_latex contains no skill categories."
        )


# ==========================================================
# MAIN PATCH VALIDATOR
# ==========================================================

def validate_patch(
    patch: dict[str, Any],
    evidence: dict,
    source_text: str,
) -> list[str]:

    errors: list[str] = []

    # ------------------------------------------------------
    # Structure
    # ------------------------------------------------------

    _validate_structure(
        patch,
        errors,
    )

    if errors:

        return errors

    # ------------------------------------------------------
    # Required counts
    # ------------------------------------------------------

    _validate_counts(
        patch,
        errors,
    )

    # ------------------------------------------------------
    # Duplicate bullets
    # ------------------------------------------------------

    _validate_duplicates(
        patch,
        errors,
    )

    # ------------------------------------------------------
    # Bullet lengths
    # ------------------------------------------------------

    _validate_bullet_lengths(
        patch,
        errors,
    )

    # ------------------------------------------------------
    # Numeric hallucination protection
    # ------------------------------------------------------

    _validate_numbers(
        patch,
        evidence,
        source_text,
        errors,
    )

    # ------------------------------------------------------
    # Employer isolation
    # ------------------------------------------------------

    _validate_experience_isolation(
        patch,
        errors,
    )

    # ------------------------------------------------------
    # No role/date duplication
    # ------------------------------------------------------

    _validate_no_headers(
        patch,
        errors,
    )

    # ------------------------------------------------------
    # Deterministic technical skills structure
    # ------------------------------------------------------

    _validate_skills_latex(
        patch,
        errors,
    )

    return errors


# ==========================================================
# LATEX VALIDATION
# ==========================================================

def validate_latex(
    text: str,
) -> list[str]:

    errors: list[str] = []

    # ------------------------------------------------------
    # BRACES
    # ------------------------------------------------------

    if text.count(
        "{"
    ) != text.count(
        "}"
    ):

        errors.append(
            "Unbalanced LaTeX braces."
        )

    # ------------------------------------------------------
    # ITEMIZE
    # ------------------------------------------------------

    if text.count(
        "\\begin{itemize}"
    ) != text.count(
        "\\end{itemize}"
    ):

        errors.append(
            "Unbalanced itemize environments."
        )

    # ------------------------------------------------------
    # LONGTABLE
    # ------------------------------------------------------

    if text.count(
        "\\begin{longtable}"
    ) != text.count(
        "\\end{longtable}"
    ):

        errors.append(
            "Unbalanced longtable environments."
        )

    # ------------------------------------------------------
    # DOCUMENT
    # ------------------------------------------------------

    if "\\begin{document}" not in text:

        errors.append(
            "Missing \\begin{document}."
        )

    if "\\end{document}" not in text:

        errors.append(
            "Missing \\end{document}."
        )

    return errors