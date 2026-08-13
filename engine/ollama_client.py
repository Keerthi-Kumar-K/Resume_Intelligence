from __future__ import annotations

import json
from typing import Any

import requests

from config import (
    OLLAMA_KEEP_ALIVE,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_TEMPERATURE,
    OLLAMA_TIMEOUT_SECONDS,
    OLLAMA_URL,
)


# ==========================================================
# SUMMARY JSON SCHEMA
# ==========================================================

SUMMARY_SCHEMA = {

    "type": "object",

    "properties": {

        "summary_bullets": {

            "type": "array",

            "items": {
                "type": "string"
            },

            "minItems": 4,
            "maxItems": 7,
        },

        "change_notes": {

            "type": "array",

            "items": {
                "type": "string"
            },
        },
    },

    "required": [
        "summary_bullets",
        "change_notes",
    ],
}


# ==========================================================
# EXPERIENCE JSON SCHEMA
# ==========================================================

EXPERIENCE_SCHEMA = {

    "type": "object",

    "properties": {

        "bullets": {

            "type": "array",

            "items": {
                "type": "string"
            },

            # Main.py can safely fill missing bullets
            # from the original resume.
            "minItems": 4,
            "maxItems": 10,
        },

        "change_notes": {

            "type": "array",

            "items": {
                "type": "string"
            },
        },
    },

    "required": [
        "bullets",
        "change_notes",
    ],
}


# ==========================================================
# SYSTEM PROMPT — SUMMARY
# ==========================================================

SUMMARY_SYSTEM_PROMPT = """
You are a resume summary-tailoring engine.

Your job is to improve semantic alignment with a target job
description without changing factual experience.

Use only the information explicitly supplied in the prompt.

Never invent:
- technologies
- tools
- experience
- employers
- clients
- certifications
- responsibilities
- projects
- metrics
- percentages
- dates
- years
- achievements

Do not generate technical skills.
Technical skills are handled separately by deterministic Python.

Preserve existing metrics exactly.

Return only valid JSON conforming to the requested schema.

Do not return Markdown.
Do not return LaTeX.
""".strip()


# ==========================================================
# SYSTEM PROMPT — EXPERIENCE
# ==========================================================

EXPERIENCE_SYSTEM_PROMPT = """
You are a resume experience-tailoring engine.

You are given evidence for exactly ONE employer.

Rewrite, reorder, and prioritize only the evidence supplied for
that employer so it aligns naturally with the target job.

Never infer facts from another employer.

Never invent:
- technologies
- tools
- responsibilities
- metrics
- percentages
- employers
- clients
- dates
- projects
- achievements
- domains

Preserve existing metrics exactly.

Do not include:
- employer name
- role title
- employment dates

inside experience bullets because these already exist in the
resume template.

Return only valid JSON conforming to the requested schema.

Do not return Markdown.
Do not return LaTeX.
""".strip()


# ==========================================================
# GENERIC OLLAMA REQUEST
# ==========================================================

def _call_ollama(
    user_prompt: str,
    system_prompt: str,
    schema: dict[str, Any],
    num_predict: int,
) -> dict[str, Any]:

    payload = {

        "model":
            OLLAMA_MODEL,

        "messages": [

            {
                "role":
                    "system",

                "content":
                    system_prompt,
            },

            {
                "role":
                    "user",

                "content":
                    user_prompt,
            },
        ],

        "stream":
            False,

        "format":
            schema,

        "keep_alive":
            OLLAMA_KEEP_ALIVE,

        "options": {

            "temperature":
                OLLAMA_TEMPERATURE,

            "num_ctx":
                OLLAMA_NUM_CTX,

            "num_predict":
                num_predict,
        },
    }

    response = requests.post(

        OLLAMA_URL,

        json=payload,

        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data
        .get(
            "message",
            {},
        )
        .get(
            "content",
            "",
        )
    )

    if not content:

        raise RuntimeError(
            "Ollama returned an empty response."
        )

    try:

        parsed = json.loads(
            content
        )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            "Ollama returned invalid JSON:\n"
            f"{content[:1500]}"
        ) from error

    return parsed


# ==========================================================
# GENERATE SUMMARY
# ==========================================================

def generate_summary(
    prompt: str,
) -> dict[str, Any]:

    return _call_ollama(

        user_prompt=prompt,

        system_prompt=SUMMARY_SYSTEM_PROMPT,

        schema=SUMMARY_SCHEMA,

        num_predict=750,
    )


# ==========================================================
# GENERATE EXPERIENCE
# ==========================================================

def generate_experience(
    prompt: str,
) -> dict[str, Any]:

    return _call_ollama(

        user_prompt=prompt,

        system_prompt=EXPERIENCE_SYSTEM_PROMPT,

        schema=EXPERIENCE_SCHEMA,

        num_predict=900,
    )