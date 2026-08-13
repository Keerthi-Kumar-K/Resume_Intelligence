from __future__ import annotations

import argparse
import csv
import json
import re
import sys

from datetime import datetime
from pathlib import Path

from config import (
    DEFAULT_OUTPUT_DIR,
    EVIDENCE_FILE,
    MIN_SCORE_TO_TAILOR,
    RESUME_TEMPLATE_MAP,
    SCORE_THRESHOLD,
)

from engine.compiler import compile_tex

from engine.excel_reader import (
    ATSJob,
    read_jobs,
)

from engine.jd_reader import (
    build_jd_index,
    find_job_description,
)

from engine.latex_parser import (
    apply_patch,
    extract_sections,
    read_tex,
)

from engine.ollama_client import (
    generate_experience,
    generate_summary,
)

from engine.prompt_builder import (
    build_experience_1_prompt,
    build_experience_2_prompt,
    build_summary_prompt,
)

from engine.validator import (
    validate_latex,
    validate_patch,
)


# ==========================================================
# SAFE FILE/FOLDER NAME
# ==========================================================

def safe_name(
    value: str,
    max_length: int = 80,
) -> str:

    value = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        str(value),
    ).strip("._")

    return value[:max_length] or "job"


# ==========================================================
# WRITE JSON
# ==========================================================

def write_json(
    path: Path,
    data,
) -> None:

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# ==========================================================
# NORMALIZE TEXT FOR JD/SKILL MATCHING
# ==========================================================

def normalize_for_match(
    value: str,
) -> str:

    value = str(value).lower()

    value = value.replace(
        "\\&",
        " and ",
    )

    value = value.replace(
        "&",
        " and ",
    )

    value = value.replace(
        "\\textasciitilde",
        " ",
    )

    value = re.sub(
        r"\\textbf\{([^{}]+)\}",
        r"\1",
        value,
    )

    value = re.sub(
        r"\\[a-zA-Z]+",
        " ",
        value,
    )

    value = re.sub(
        r"[^a-z0-9+#./ -]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ==========================================================
# JD TERM ALIASES
# ==========================================================

SKILL_ALIASES = {

    "informatica powercenter": [
        "informatica",
        "powercenter",
    ],

    "ab initio": [
        "ab initio",
        "abinitio",
    ],

    "azure databricks": [
        "databricks",
        "azure databricks",
    ],

    "azure data factory": [
        "azure data factory",
        "adf",
    ],

    "adls": [
        "adls",
        "azure data lake",
    ],

    "amazon web services": [
        "aws",
        "amazon web services",
    ],

    "aws": [
        "aws",
        "amazon web services",
    ],

    "sql server": [
        "sql server",
        "microsoft sql server",
    ],

    "airflow": [
        "airflow",
        "apache airflow",
    ],

    "kafka": [
        "kafka",
        "apache kafka",
    ],

    "spark": [
        "spark",
        "apache spark",
        "pyspark",
        "spark sql",
    ],

    "snowflake": [
        "snowflake",
    ],

    "teradata": [
        "teradata",
    ],

    "oracle": [
        "oracle",
    ],

    "mysql": [
        "mysql",
        "my sql",
    ],

    "postgresql": [
        "postgresql",
        "postgres",
    ],

    "db2": [
        "db2",
    ],

    "power bi": [
        "power bi",
    ],

    "tableau": [
        "tableau",
    ],

    "python": [
        "python",
        "pyspark",
    ],

    "sql": [
        "sql",
        "t-sql",
        "spark sql",
    ],

    "etl": [
        "etl",
        "extract transform load",
    ],

    "data governance": [
        "data governance",
    ],

    "data lineage": [
        "data lineage",
        "lineage",
    ],

    "metadata management": [
        "metadata management",
        "metadata",
    ],

    "data quality": [
        "data quality",
        "validation",
        "reconciliation",
    ],

    "cdc": [
        "cdc",
        "change data capture",
    ],

    "incremental loading": [
        "incremental loading",
        "incremental load",
    ],

    "dimensional modeling": [
        "dimensional modeling",
        "dimension modeling",
    ],

    "scd": [
        "scd",
        "slowly changing dimension",
    ],

    "docker": [
        "docker",
    ],

    "jenkins": [
        "jenkins",
    ],

    "git": [
        "git",
        "github",
        "bitbucket",
    ],
}


# ==========================================================
# SCORE ONE SKILLS ROW AGAINST JD
# ==========================================================

def score_skill_row(
    row_text: str,
    jd_text: str,
) -> int:

    row_normalized = normalize_for_match(
        row_text
    )

    jd_normalized = normalize_for_match(
        jd_text
    )

    score = 0

    # ------------------------------------------------------
    # Strong phrase matching
    # ------------------------------------------------------

    for canonical, aliases in SKILL_ALIASES.items():

        row_has = any(
            alias in row_normalized
            for alias in aliases
        )

        jd_has = any(
            alias in jd_normalized
            for alias in aliases
        )

        if row_has and jd_has:
            score += 12

    # ------------------------------------------------------
    # Generic token overlap
    # ------------------------------------------------------

    tokens = [
        token.strip()
        for token in re.split(
            r"[,;/|]",
            row_normalized,
        )
        if token.strip()
    ]

    for token in tokens:

        if len(token) < 3:
            continue

        if token in jd_normalized:
            score += 3
            continue

        words = [
            word
            for word in token.split()
            if len(word) >= 4
        ]

        score += sum(
            1
            for word in words
            if word in jd_normalized
        )

    return score


# ==========================================================
# DETERMINISTIC SKILL REORDERING
# ==========================================================

def rank_skill_rows(
    skills_block: str,
    jd_text: str,
) -> str:
    """
    IMPORTANT:

    This function DOES NOT generate any skills.

    It keeps every original LaTeX skill row unchanged and
    only changes row order based on relevance to the JD.
    """

    pattern = re.compile(
        r"(\\textbf\{[^{}]+\}\s*&\s*.*?\\\\\s*\n\\hline)",
        re.DOTALL,
    )

    matches = list(
        pattern.finditer(
            skills_block
        )
    )

    if not matches:
        return skills_block

    ranked_rows = []

    for original_index, match in enumerate(
        matches
    ):

        row = match.group(1)

        score = score_skill_row(
            row,
            jd_text,
        )

        ranked_rows.append(
            (
                score,
                original_index,
                row,
            )
        )

    # Relevant rows first.
    # Original order preserved for equal scores.

    ranked_rows.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    first_start = matches[0].start()
    last_end = matches[-1].end()

    prefix = skills_block[
        :first_start
    ]

    suffix = skills_block[
        last_end:
    ]

    reordered_rows = "\n".join(
        row
        for _, _, row
        in ranked_rows
    )

    return (
        prefix
        + reordered_rows
        + suffix
    )


# ==========================================================
# NORMALIZE BULLET FOR DUPLICATE DETECTION
# ==========================================================

def normalize_bullet(
    bullet: str,
) -> str:

    value = str(
        bullet
    ).lower()

    value = re.sub(
        r"\\textbf\{([^{}]+)\}",
        r"\1",
        value,
    )

    value = value.replace(
        "\\textasciitilde",
        "",
    )

    value = re.sub(
        r"\\[a-zA-Z]+",
        " ",
        value,
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ==========================================================
# FILL MISSING BULLETS FROM ORIGINAL RESUME
# ==========================================================

def fill_bullets_from_original(
    generated: list[str],
    original: list[str],
    minimum: int,
    maximum: int,
) -> list[str]:
    """
    Ollama sometimes returns fewer bullets than requested.

    We NEVER ask Ollama to invent another one.

    Instead, copy unchanged original bullets until the
    minimum count is reached.
    """

    result = list(
        generated[:maximum]
    )

    existing = {
        normalize_bullet(
            bullet
        )
        for bullet in result
    }

    if len(result) >= minimum:
        return result

    for bullet in original:

        if len(result) >= minimum:
            break

        normalized = normalize_bullet(
            bullet
        )

        if not normalized:
            continue

        if normalized in existing:
            continue

        result.append(
            bullet
        )

        existing.add(
            normalized
        )

    return result[:maximum]


# ==========================================================
# BUILD FINAL PATCH
# ==========================================================

def build_final_patch(
    summary_response: dict,
    exp1_response: dict,
    exp2_response: dict,
    sections,
    jd_text: str,
) -> dict:

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    summary_bullets = summary_response.get(
        "summary_bullets",
        [],
    )

    # ------------------------------------------------------
    # Assurant
    # ------------------------------------------------------

    experience_1 = fill_bullets_from_original(

        generated=exp1_response.get(
            "bullets",
            [],
        ),

        original=sections.experience_1_bullets,

        minimum=6,

        maximum=10,
    )

    # ------------------------------------------------------
    # Community Dreams
    # ------------------------------------------------------

    experience_2 = fill_bullets_from_original(

        generated=exp2_response.get(
            "bullets",
            [],
        ),

        original=sections.experience_2_bullets,

        minimum=5,

        maximum=9,
    )

    # ------------------------------------------------------
    # Skills:
    # NO OLLAMA
    # ------------------------------------------------------

    skills_latex = rank_skill_rows(

        skills_block=sections.skills_block,

        jd_text=jd_text,
    )

    # ------------------------------------------------------
    # Notes
    # ------------------------------------------------------

    change_notes = []

    change_notes.extend(
        summary_response.get(
            "change_notes",
            [],
        )
    )

    change_notes.extend(
        exp1_response.get(
            "change_notes",
            [],
        )
    )

    change_notes.extend(
        exp2_response.get(
            "change_notes",
            [],
        )
    )

    change_notes.append(
        "Technical skills were preserved exactly from the "
        "base resume and only reordered using deterministic "
        "JD relevance scoring."
    )

    return {

        "summary_bullets":
            summary_bullets,

        # Kept for compatibility with older latex_parser
        "skills":
            [],

        "skills_latex":
            skills_latex,

        "experience_1_bullets":
            experience_1,

        "experience_2_bullets":
            experience_2,

        "unsupported_requirements":
            [],

        "change_notes":
            change_notes,
    }


# ==========================================================
# REPLACE SKILLS BLOCK
# ==========================================================

def replace_skills_block(
    latex_text: str,
    skills_latex: str,
) -> str:
    """
    Replace Technical Skills safely.

    Supports BOTH:

    1. Templates containing:
       % BEGIN_AUTO_SKILLS
       % END_AUTO_SKILLS

    2. Older templates without markers,
       where the section begins with:
       \\section*{TECHNICAL SKILLS:}
    """

    start_marker = "% BEGIN_AUTO_SKILLS"
    end_marker = "% END_AUTO_SKILLS"

    # ======================================================
    # METHOD 1 — AUTO MARKERS EXIST
    # ======================================================

    if (
        start_marker in latex_text
        and
        end_marker in latex_text
    ):

        pattern = (
            re.escape(start_marker)
            + r".*?"
            + re.escape(end_marker)
        )

        replacement = (
            start_marker
            + "\n"
            + skills_latex.strip()
            + "\n"
            + end_marker
        )

        updated, count = re.subn(
            pattern,
            lambda _: replacement,
            latex_text,
            count=1,
            flags=re.DOTALL,
        )

        if count == 1:
            return updated

    # ======================================================
    # METHOD 2 — FIND TECHNICAL SKILLS SECTION
    # ======================================================

    section_start = re.search(
        r"\\section\*\{TECHNICAL SKILLS:?\}",
        latex_text,
        flags=re.IGNORECASE,
    )

    if not section_start:

        raise ValueError(
            "Unable to locate TECHNICAL SKILLS section "
            "in LaTeX template."
        )

    start = section_start.start()

    # ======================================================
    # FIND END OF LONGTABLE
    # ======================================================

    longtable_end = latex_text.find(
        r"\end{longtable}",
        start,
    )

    if longtable_end == -1:

        raise ValueError(
            "TECHNICAL SKILLS section found, "
            "but \\end{longtable} was not found."
        )

    end = (
        longtable_end
        + len(
            r"\end{longtable}"
        )
    )

    # ======================================================
    # REPLACE ENTIRE SKILLS SECTION
    # ======================================================

    updated = (
        latex_text[:start]
        + skills_latex.strip()
        + "\n"
        + latex_text[end:]
    )

    return updated

# ==========================================================
# PROCESS ONE JOB
# ==========================================================

def process_job(
    job: ATSJob,
    jd_entries,
    evidence: dict,
    run_dir: Path,
    compile_pdf: bool,
) -> dict:

    result = {

        "job_id":
            job.job_id,

        "job_name":
            job.job_name,

        "job_url":
            job.job_url,

        "base_resume":
            job.best_resume,

        "original_score":
            job.best_score,

        "status":
            "started",

        "output_tex":
            "",

        "output_pdf":
            "",

        "message":
            "",
    }

    # ======================================================
    # TEMPLATE
    # ======================================================

    template_path = RESUME_TEMPLATE_MAP.get(
        job.best_resume
    )

    if template_path is None:

        result.update(

            status="skipped",

            message=(
                "No LaTeX template mapping "
                "for best resume."
            ),
        )

        return result

    template_path = Path(
        template_path
    )

    if not template_path.exists():

        result.update(

            status="skipped",

            message=(
                "Mapped LaTeX template is missing: "
                f"{template_path}"
            ),
        )

        return result

    # ======================================================
    # FIND JD
    # ======================================================

    jd_text = find_job_description(

        jd_entries,

        job.job_id,

        job.job_url,

        job.job_name,
    )

    if not jd_text:

        result.update(

            status="skipped",

            message=(
                "Could not map Job ID/URL "
                "to full JD."
            ),
        )

        return result

    # ======================================================
    # JOB OUTPUT FOLDER
    # ======================================================

    folder = (

        run_dir
        / (
            f"{safe_name(job.job_id)}_"
            f"{safe_name(job.job_name, 60)}"
        )
    )

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ======================================================
    # LOAD TEMPLATE
    # ======================================================

    base_tex = read_tex(
        template_path
    )

    sections = extract_sections(
        base_tex
    )

    # ======================================================
    # SAVE INPUT
    # ======================================================

    write_json(

        folder
        / "job_input.json",

        {

            "job":
                job.__dict__,

            "job_description":
                jd_text,

            "template":
                str(
                    template_path
                ),
        },
    )

    # ======================================================
    # CALL 1
    # SUMMARY ONLY
    # ======================================================

    summary_prompt = build_summary_prompt(

        job=job,

        jd_text=jd_text,

        sections=sections,

        evidence=evidence,
    )

    (
        folder
        / "prompt_01_summary.json"
    ).write_text(

        summary_prompt,

        encoding="utf-8",
    )

    summary_response = generate_summary(
        summary_prompt
    )

    write_json(

        folder
        / "response_01_summary.json",

        summary_response,
    )

    # ======================================================
    # CALL 2
    # ASSURANT ONLY
    # ======================================================

    exp1_prompt = build_experience_1_prompt(

        job=job,

        jd_text=jd_text,

        sections=sections,

        evidence=evidence,
    )

    (
        folder
        / "prompt_02_assurant.json"
    ).write_text(

        exp1_prompt,

        encoding="utf-8",
    )

    exp1_response = generate_experience(
        exp1_prompt
    )

    write_json(

        folder
        / "response_02_assurant.json",

        exp1_response,
    )

    # ======================================================
    # CALL 3
    # COMMUNITY DREAMS ONLY
    # ======================================================

    exp2_prompt = build_experience_2_prompt(

        job=job,

        jd_text=jd_text,

        sections=sections,

        evidence=evidence,
    )

    (
        folder
        / "prompt_03_community_dreams.json"
    ).write_text(

        exp2_prompt,

        encoding="utf-8",
    )

    exp2_response = generate_experience(
        exp2_prompt
    )

    write_json(

        folder
        / "response_03_community_dreams.json",

        exp2_response,
    )

    # ======================================================
    # MERGE
    # ======================================================

    patch = build_final_patch(

        summary_response=summary_response,

        exp1_response=exp1_response,

        exp2_response=exp2_response,

        sections=sections,

        jd_text=jd_text,
    )

    write_json(

        folder
        / "proposed_patch.json",

        patch,
    )

    # ======================================================
    # EVIDENCE VALIDATION
    # ======================================================

    validation_errors = validate_patch(

        patch,

        evidence,

        base_tex,
    )

    if validation_errors:

        write_json(

            folder
            / "validation.json",

            {

                "valid":
                    False,

                "errors":
                    validation_errors,
            },
        )

        result.update(

            status="rejected",

            message=(

                "Patch failed evidence validation: "

                + " | ".join(
                    validation_errors[:10]
                )
            ),
        )

        return result

    # ======================================================
    # APPLY SUMMARY / EXPERIENCE PATCHES
    # ======================================================

    tailored_tex = apply_patch(

        base_tex,

        patch,
    )

    # ======================================================
    # APPLY DETERMINISTIC SKILLS
    # ======================================================

    tailored_tex = replace_skills_block(

        tailored_tex,

        patch[
            "skills_latex"
        ],
    )

    # ======================================================
    # LATEX VALIDATION
    # ======================================================

    latex_errors = validate_latex(
        tailored_tex
    )

    if latex_errors:

        write_json(

            folder
            / "validation.json",

            {

                "valid":
                    False,

                "errors":
                    latex_errors,
            },
        )

        result.update(

            status="rejected",

            message=(

                "Generated LaTeX failed validation: "

                + " | ".join(
                    latex_errors
                )
            ),
        )

        return result

    # ======================================================
    # SAVE TEX
    # ======================================================

    tex_path = (

        folder
        / (
            f"Tailored_"
            f"{safe_name(job.job_id)}_"
            f"{safe_name(job.job_name, 55)}"
            f".tex"
        )
    )

    tex_path.write_text(

        tailored_tex,

        encoding="utf-8",
    )

    write_json(

        folder
        / "validation.json",

        {

            "valid":
                True,

            "errors":
                [],
        },
    )

    result[
        "output_tex"
    ] = str(
        tex_path
    )

    # ======================================================
    # COMPILE PDF
    # ======================================================

    if compile_pdf:

        success, compile_log, pdf_path = compile_tex(
            tex_path
        )

        (
            folder
            / "latex_compile.log"
        ).write_text(

            compile_log,

            encoding="utf-8",

            errors="replace",
        )

        if success and pdf_path:

            result.update(

                status="completed",

                output_pdf=str(
                    pdf_path
                ),

                message=(
                    "Tailored LaTeX and PDF created."
                ),
            )

        else:

            result.update(

                status="tex_created",

            message=(
                "Tailored LaTeX created; "
                "PDF compilation with pdflatex failed. "
                "Check latex_compile.log."
            ),
            )

    else:

        result.update(

            status="tex_created",

            message=(
                "Tailored LaTeX created."
            ),
        )

    return result


# ==========================================================
# COMMAND LINE ARGUMENTS
# ==========================================================

def parse_args():

    parser = argparse.ArgumentParser(

        description=(
            "Local truthful resume tailoring engine."
        )
    )

    parser.add_argument(

        "--ats-excel",

        required=True,

        type=Path,
    )

    parser.add_argument(

        "--filtered-jd",

        required=True,

        type=Path,
    )

    parser.add_argument(

        "--output-dir",

        type=Path,

        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(

        "--threshold",

        type=float,

        default=SCORE_THRESHOLD,
    )

    parser.add_argument(

        "--minimum-score",

        type=float,

        default=MIN_SCORE_TO_TAILOR,
    )

    parser.add_argument(

        "--limit",

        type=int,

        default=0,

        help=(
            "Process only first N eligible jobs. "
            "0 = all."
        ),
    )

    parser.add_argument(

        "--no-compile",

        action="store_true",

        help=(
            "Generate .tex only."
        ),
    )

    return parser.parse_args()


# ==========================================================
# MAIN
# ==========================================================

def main():

    args = parse_args()

    # ======================================================
    # EVIDENCE
    # ======================================================

    if not EVIDENCE_FILE.exists():

        print(

            f"Evidence file missing: "
            f"{EVIDENCE_FILE}",

            file=sys.stderr,
        )

        return 2

    evidence = json.loads(

        EVIDENCE_FILE.read_text(
            encoding="utf-8"
        )
    )

    # ======================================================
    # ATS JOBS
    # ======================================================

    jobs = read_jobs(

        args.ats_excel,

        args.threshold,

        args.minimum_score,
    )

    if args.limit > 0:

        jobs = jobs[
            :args.limit
        ]

    # ======================================================
    # JD INDEX
    # ======================================================

    jd_entries = build_jd_index(
        args.filtered_jd
    )

    # ======================================================
    # OUTPUT FOLDER
    # ======================================================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    run_dir = (

        args.output_dir
        / f"Tailored_Resumes_{timestamp}"
    )

    run_dir.mkdir(

        parents=True,

        exist_ok=True,
    )

    # ======================================================
    # START LOG
    # ======================================================

    print(
        f"Eligible jobs: {len(jobs)}"
    )

    print(
        f"JD blocks indexed: {len(jd_entries)}"
    )

    print(
        f"Output: {run_dir}"
    )

    print(
        "Tailoring mode: summary Ollama + deterministic skills + isolated experiences"
    )

    # ======================================================
    # PROCESS JOBS
    # ======================================================

    results = []

    for index, job in enumerate(
        jobs,
        start=1,
    ):

        print(

            f"[{index}/{len(jobs)}] "
            f"{job.job_id} | "
            f"{job.job_name} | "
            f"score={job.best_score:.2f}"
        )

        try:

            result = process_job(

                job=job,

                jd_entries=jd_entries,

                evidence=evidence,

                run_dir=run_dir,

                compile_pdf=(
                    not args.no_compile
                ),
            )

        except KeyboardInterrupt:

            print(
                "\nStopped by user."
            )

            break

        except Exception as error:

            result = {

                "job_id":
                    job.job_id,

                "job_name":
                    job.job_name,

                "job_url":
                    job.job_url,

                "base_resume":
                    job.best_resume,

                "original_score":
                    job.best_score,

                "status":
                    "error",

                "output_tex":
                    "",

                "output_pdf":
                    "",

                "message":
                    (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
            }

        results.append(
            result
        )

        print(

            f"    "
            f"{result['status']}: "
            f"{result['message']}"
        )

    # ======================================================
    # SUMMARY CSV
    # ======================================================

    summary_path = (

        run_dir
        / "tailoring_summary.csv"
    )

    fields = [

        "job_id",
        "job_name",
        "job_url",
        "base_resume",
        "original_score",
        "status",
        "output_tex",
        "output_pdf",
        "message",
    ]

    with summary_path.open(

        "w",

        newline="",

        encoding="utf-8-sig",

    ) as handle:

        writer = csv.DictWriter(

            handle,

            fieldnames=fields,
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    # ======================================================
    # SUMMARY JSON
    # ======================================================

    write_json(

        run_dir
        / "tailoring_summary.json",

        results,
    )

    print(
        f"Summary saved: {summary_path}"
    )

    return 0


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )