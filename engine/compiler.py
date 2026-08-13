from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


# ==========================================================
# PDFLATEX COMPILER
# ==========================================================

PDFLATEX_COMMAND = [
    "pdflatex",
    "-interaction=nonstopmode",
    "-halt-on-error",
    "-file-line-error",
]


def compile_tex(
    tex_path: Path,
) -> tuple[bool, str, Path | None]:

    tex_path = Path(tex_path).resolve()

    # ------------------------------------------------------
    # CHECK TEX FILE
    # ------------------------------------------------------

    if not tex_path.exists():

        return (
            False,
            f"LaTeX file does not exist: {tex_path}",
            None,
        )

    # ------------------------------------------------------
    # CHECK PDFLATEX
    # ------------------------------------------------------

    executable = PDFLATEX_COMMAND[0]

    executable_path = shutil.which(executable)

    if executable_path is None:

        return (
            False,
            "'pdflatex' was not found in PATH. "
            "LaTeX file was created but PDF "
            "could not be compiled.",
            None,
        )

    # ------------------------------------------------------
    # OUTPUT PDF
    # ------------------------------------------------------

    pdf_path = tex_path.with_suffix(".pdf")

    # Delete stale PDF so we never mistake an old
    # compilation for a successful new one.

    if pdf_path.exists():

        try:
            pdf_path.unlink()
        except OSError:
            pass

    # ------------------------------------------------------
    # COMMAND
    # ------------------------------------------------------

    command = [
        executable_path,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        tex_path.name,
    ]

    logs = []

    # ------------------------------------------------------
    # RUN TWICE
    #
    # Two passes handle references / layout information
    # more reliably.
    # ------------------------------------------------------

    for pass_number in range(1, 3):

        try:

            result = subprocess.run(
                command,
                cwd=tex_path.parent,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )

        except subprocess.TimeoutExpired as error:

            logs.append(
                f"\n===== PDFLATEX PASS "
                f"{pass_number} TIMEOUT =====\n"
            )

            logs.append(
                str(error)
            )

            return (
                False,
                "\n".join(logs),
                None,
            )

        except Exception as error:

            logs.append(
                f"\n===== PDFLATEX PASS "
                f"{pass_number} EXCEPTION =====\n"
            )

            logs.append(
                f"{type(error).__name__}: {error}"
            )

            return (
                False,
                "\n".join(logs),
                None,
            )

        # --------------------------------------------------
        # SAVE OUTPUT
        # --------------------------------------------------

        logs.append(
            f"\n===== PDFLATEX PASS "
            f"{pass_number} =====\n"
        )

        logs.append(
            f"Command: {' '.join(command)}\n"
        )

        logs.append(
            f"Return code: {result.returncode}\n"
        )

        logs.append(
            "\n----- STDOUT -----\n"
        )

        logs.append(
            result.stdout or ""
        )

        logs.append(
            "\n----- STDERR -----\n"
        )

        logs.append(
            result.stderr or ""
        )

        # --------------------------------------------------
        # STOP IMMEDIATELY ON ERROR
        # --------------------------------------------------

        if result.returncode != 0:

            return (
                False,
                "\n".join(logs),
                None,
            )

    # ------------------------------------------------------
    # VERIFY PDF
    # ------------------------------------------------------

    if (
        pdf_path.exists()
        and pdf_path.stat().st_size > 0
    ):

        logs.append(
            "\n===== COMPILATION SUCCESSFUL =====\n"
        )

        logs.append(
            f"PDF: {pdf_path}\n"
        )

        return (
            True,
            "\n".join(logs),
            pdf_path,
        )

    # ------------------------------------------------------
    # PDF MISSING DESPITE SUCCESS RETURN CODE
    # ------------------------------------------------------

    logs.append(
        "\n===== COMPILATION FAILED =====\n"
    )

    logs.append(
        "pdflatex completed but the expected "
        "PDF file was not created.\n"
    )

    return (
        False,
        "\n".join(logs),
        None,
    )