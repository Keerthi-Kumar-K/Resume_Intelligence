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
    generate_summary_skills,
)

from engine.prompt_builder import (
    build_experience_1_prompt,
    build_experience_2_prompt,
    build_summary_skills_prompt,
)

from engine.validator import (
    validate_latex,
    validate_patch,
)


# ==========================================================
# HELPERS
# ==========================================================

def safe_name(
    value: str,
    max_length: int = 80,
) -> str:

    cleaned = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        str(
            value
        ),
    ).strip(
        "._"
    )

    return (
        cleaned[:max_length]
        or "job"
    )


def write_json(
    path: Path,
    data: object,
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
# MERGE THREE MODEL RESPONSES
# ==========================================================

def merge_patches(
    summary_skills: dict,
    experience_1: dict,
    experience_2: dict,
) -> dict:

    change_notes = []

    change_notes.extend(
        summary_skills.get(
            "change_notes",
            [],
        )
    )

    change_notes.extend(
        experience_1.get(
            "change_notes",
            [],
        )
    )

    change_notes.extend(
        experience_2.get(
            "change_notes",
            [],
        )
    )

    return {

        "summary_bullets":
            summary_skills.get(
                "summary_bullets",
                [],
            ),

        "skills":
            summary_skills.get(
                "skills",
                [],
            ),

        "experience_1_bullets":
            experience_1.get(
                "bullets",
                [],
            ),

        "experience_2_bullets":
            experience_2.get(
                "bullets",
                [],
            ),

        "unsupported_requirements":
            summary_skills.get(
                "unsupported_requirements",
                [],
            ),

        "change_notes":
            change_notes,
    }


# ==========================================================
# PROCESS ONE JOB
# ==========================================================

def process_job(
    job: ATSJob,
    jd_entries: list[dict[str, str]],
    evidence: dict,
    run_dir: Path,
    compile_pdf: bool,
) -> dict[str, object]:

    result: dict[str, object] = {

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
    # JD MAPPING
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
                "Could not map the Job ID/URL "
                "to a full JD block."
            ),
        )

        return result

    # ======================================================
    # JOB FOLDER
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
    # BASE LATEX
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
    # CALL 1:
    # SUMMARY + SKILLS
    # ======================================================

    summary_prompt = build_summary_skills_prompt(

        job=job,

        jd_text=jd_text,

        sections=sections,

        evidence=evidence,
    )

    (
        folder
        / "prompt_01_summary_skills.json"
    ).write_text(

        summary_prompt,

        encoding="utf-8",
    )

    summary_skills = generate_summary_skills(
        summary_prompt
    )

    write_json(

        folder
        / "response_01_summary_skills.json",

        summary_skills,
    )

    # ======================================================
    # CALL 2:
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

    experience_1 = generate_experience(
        exp1_prompt
    )

    write_json(

        folder
        / "response_02_assurant.json",

        experience_1,
    )

    # ======================================================
    # CALL 3:
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

    experience_2 = generate_experience(
        exp2_prompt
    )

    write_json(

        folder
        / "response_03_community_dreams.json",

        experience_2,
    )

    # ======================================================
    # MERGE
    # ======================================================

    patch = merge_patches(

        summary_skills=summary_skills,

        experience_1=experience_1,

        experience_2=experience_2,
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
                    validation_errors[:8]
                )
            ),
        )

        return result

    # ======================================================
    # APPLY TO LATEX
    # ======================================================

    tailored_tex = apply_patch(

        base_tex,

        patch,
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

    tex_filename = (

        f"Tailored_"
        f"{safe_name(job.job_id)}_"
        f"{safe_name(job.job_name, 55)}"
        f".tex"
    )

    tex_path = (
        folder
        / tex_filename
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
                    "Tailored LaTeX and PDF created "
                    "using isolated 3-call tailoring."
                ),
            )

        else:

            result.update(

                status="tex_created",

                message=(
                    "LaTeX created successfully; "
                    "PDF compilation failed or "
                    "latexmk is unavailable."
                ),
            )

    else:

        result.update(

            status="tex_created",

            message=(
                "Tailored LaTeX created; "
                "PDF compilation disabled."
            ),
        )

    return result


# ==========================================================
# ARGUMENTS
# ==========================================================

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(

        description=(
            "Create truthful job-specific LaTeX "
            "resume variants using isolated Ollama calls."
        )
    )

    parser.add_argument(

        "--ats-excel",

        required=True,

        type=Path,

        help=(
            "ATS result .xlsx containing "
            "the Summary sheet."
        ),
    )

    parser.add_argument(

        "--filtered-jd",

        required=True,

        type=Path,

        help=(
            "Filtered JD .docx or .txt "
            "used as ATS input."
        ),
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
            "Process first N eligible jobs; "
            "0 means all."
        ),
    )

    parser.add_argument(

        "--no-compile",

        action="store_true",

        help=(
            "Create .tex files without "
            "running latexmk."
        ),
    )

    return parser.parse_args()


# ==========================================================
# MAIN
# ==========================================================

def main() -> int:

    args = parse_args()

    # ======================================================
    # EVIDENCE
    # ======================================================

    if not EVIDENCE_FILE.exists():

        print(

            f"Evidence file not found: "
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
    # OUTPUT
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
        "Tailoring mode: 3 isolated Ollama calls/job"
    )

    # ======================================================
    # RUN
    # ======================================================

    results: list[
        dict[str, object]
    ] = []

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
                "Stopped by user. "
                "Partial results will be saved."
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
            f"    {result['status']}: "
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