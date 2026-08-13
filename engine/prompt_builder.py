from __future__ import annotations

import json

from engine.excel_reader import ATSJob
from engine.latex_parser import ResumeSections


# ==========================================================
# SUMMARY PROMPT
# ==========================================================

def build_summary_prompt(
    job: ATSJob,
    jd_text: str,
    sections: ResumeSections,
    evidence: dict,
) -> str:

    payload = {

        "task": (
            "Tailor only the PROFESSIONAL SUMMARY "
            "for the target job."
        ),

        "rules": [

            "Use only facts supported by the existing resume "
            "or approved evidence.",

            "Do not invent technologies, skills, metrics, "
            "domains, certifications, responsibilities, "
            "clients, employers, dates, or achievements.",

            "Preserve existing metrics exactly.",

            "Do not create new percentages, counts, years, "
            "durations, multipliers, or monetary values.",

            "Use job-description terminology only when it "
            "accurately represents existing experience.",

            "Prioritize job-relevant approved experience.",

            "Do not keyword-stuff.",

            "Do not mention unsupported JD requirements.",

            "Keep the candidate positioned as an experienced "
            "data engineering professional.",

            "Return 4-7 concise bullets.",

            "Return plain text only.",

            "Do not generate LaTeX.",

            "Return JSON only.",
        ],

        "job": {

            "job_id":
                job.job_id,

            "job_name":
                job.job_name,

            "job_url":
                job.job_url,

            "original_ats_score":
                job.best_score,

            "matched_required_skills":
                job.matched_required_skills,

            "missing_required_skills":
                job.missing_required_skills,

            "ats_evidence_summary":
                job.evidence_summary,

            "job_description":
                jd_text,
        },

        "current_summary":
            sections.summary_bullets,

        "approved_evidence": {

            "candidate":
                evidence.get(
                    "candidate",
                    {},
                ),

            "approved_tools":
                evidence.get(
                    "global_approved_tools",
                    [],
                ),

            "approved_capabilities":
                evidence.get(
                    "global_approved_capabilities",
                    [],
                ),

            "approved_metrics":
                evidence.get(
                    "approved_metrics",
                    [],
                ),
        },

        "required_output_schema": {

            "summary_bullets": [
                "plain text bullet"
            ],

            "change_notes": [
                "brief explanation"
            ],
        },
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )


# ==========================================================
# ASSURANT PROMPT
# ==========================================================

def build_experience_1_prompt(
    job: ATSJob,
    jd_text: str,
    sections: ResumeSections,
    evidence: dict,
) -> str:

    role_evidence = (
        evidence
        .get("experience", {})
        .get("assurant", {})
    )

    payload = {

        "task": (
            "Tailor ONLY the Assurant experience bullets "
            "for the target job."
        ),

        "critical_rule": (
            "You have access only to Assurant evidence. "
            "Do not infer or invent facts from any other employer."
        ),

        "rules": [

            "Use only Assurant evidence supplied here.",

            "Do not infer facts from another employer.",

            "Do not mention Community Dreams Foundation.",

            "Do not mention payroll.",

            "Do not mention headcount.",

            "Do not mention attrition.",

            "Do not mention workforce planning.",

            "Do not mention time-to-hire.",

            "Do not mention HRMS.",

            "Do not mention HR source systems.",

            "Do not invent any tool, technology, responsibility, "
            "metric, domain, client, project, or achievement.",

            "Use only tools supported by the Assurant evidence "
            "or original Assurant bullets.",

            "Use only capabilities supported by the Assurant "
            "evidence or original Assurant bullets.",

            "Preserve existing metrics exactly.",

            "Do not invent new numbers.",

            "Do not include employer name, role title, "
            "or employment dates inside bullets.",

            "Prioritize job-relevant Assurant evidence.",

            "Reorder and naturally rephrase supported bullets.",

            "Do not keyword-stuff.",

            "Return 6-10 bullets.",

            "Return plain text only.",

            "Do not generate LaTeX.",

            "Return JSON only.",
        ],

        "job": {

            "job_name":
                job.job_name,

            "job_description":
                jd_text,
        },

        "assurant_evidence": {

            "role":
                role_evidence.get(
                    "role",
                    "Senior Data Engineer",
                ),

            "dates":
                role_evidence.get(
                    "dates",
                    "",
                ),

            "approved_tools":
                role_evidence.get(
                    "approved_tools",
                    [],
                ),

            "approved_capabilities":
                role_evidence.get(
                    "approved_capabilities",
                    [],
                ),

            "original_bullets":
                sections.experience_1_bullets,
        },

        "required_output_schema": {

            "bullets": [
                "Assurant responsibility or achievement"
            ],

            "change_notes": [
                "brief explanation"
            ],
        },
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )


# ==========================================================
# COMMUNITY DREAMS PROMPT
# ==========================================================

def build_experience_2_prompt(
    job: ATSJob,
    jd_text: str,
    sections: ResumeSections,
    evidence: dict,
) -> str:

    role_evidence = (
        evidence
        .get("experience", {})
        .get("community_dreams", {})
    )

    payload = {

        "task": (
            "Tailor ONLY the Community Dreams Foundation "
            "experience bullets for the target job."
        ),

        "critical_rule": (
            "You have access only to Community Dreams evidence. "
            "Do not infer or invent facts from any other employer."
        ),

        "rules": [

            "Use only Community Dreams evidence supplied here.",

            "Do not infer facts from another employer.",

            "Do not mention Assurant.",

            "Do not mention warranty claims.",

            "Do not mention claims adjudication.",

            "Do not mention device protection.",

            "Do not mention insurance fraud.",

            "Do not mention actuarial analysis.",

            "Do not mention policy data.",

            "Do not mention PCI-DSS unless it is explicitly "
            "supported by supplied Community Dreams evidence.",

            "Do not invent any tool, technology, responsibility, "
            "metric, domain, client, project, or achievement.",

            "Use only tools supported by Community Dreams "
            "evidence or original Community Dreams bullets.",

            "Use only capabilities supported by Community Dreams "
            "evidence or original Community Dreams bullets.",

            "Preserve existing metrics exactly.",

            "Do not invent new numbers.",

            "Do not include employer name, role title, "
            "or employment dates inside bullets.",

            "Prioritize job-relevant Community Dreams evidence.",

            "Reorder and naturally rephrase supported bullets.",

            "Do not keyword-stuff.",

            "Return 5-9 bullets.",

            "Return plain text only.",

            "Do not generate LaTeX.",

            "Return JSON only.",
        ],

        "job": {

            "job_name":
                job.job_name,

            "job_description":
                jd_text,
        },

        "community_dreams_evidence": {

            "role":
                role_evidence.get(
                    "role",
                    "Data Engineer",
                ),

            "dates":
                role_evidence.get(
                    "dates",
                    "",
                ),

            "approved_tools":
                role_evidence.get(
                    "approved_tools",
                    [],
                ),

            "approved_capabilities":
                role_evidence.get(
                    "approved_capabilities",
                    [],
                ),

            "original_bullets":
                sections.experience_2_bullets,
        },

        "required_output_schema": {

            "bullets": [
                "Community Dreams responsibility or achievement"
            ],

            "change_notes": [
                "brief explanation"
            ],
        },
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )