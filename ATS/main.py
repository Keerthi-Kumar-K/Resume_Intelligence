# ==========================================================
# ATS Final 1.0
# Main Pipeline
# File: ATS/main.py
# Part 1: Configuration, Imports, Loaders, and Helpers
# ==========================================================

from __future__ import annotations

import argparse
import logging
import sys
import time

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List, Optional


# ==========================================================
# PROJECT PATH SETUP
# ==========================================================

CURRENT_FILE = Path(__file__).resolve()
ATS_DIRECTORY = CURRENT_FILE.parent
PROJECT_DIRECTORY = ATS_DIRECTORY.parent

if str(PROJECT_DIRECTORY) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_DIRECTORY),
    )


# ==========================================================
# ATS MODULE IMPORTS
# ==========================================================

from ATS.engine.ats_engine import ATSRankingEngine
from ATS.engine.jd_parser import JDParser
from ATS.engine.report_generator import ATSReportGenerator
from ATS.engine.resume_parser import ResumeParser


# ==========================================================
# SUPPORTED FILE TYPES
# ==========================================================

SUPPORTED_RESUME_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
}

SUPPORTED_JOB_EXTENSIONS = {
    ".docx",
    ".doc",
    ".txt",
    ".pdf",
}


# ==========================================================
# DEFAULT DIRECTORIES
# ==========================================================

DEFAULT_RESUME_DIRECTORY = (
    PROJECT_DIRECTORY
    / "resumes"
)

DEFAULT_JOB_DIRECTORY = (
    PROJECT_DIRECTORY
    / "jobs"
)

DEFAULT_OUTPUT_DIRECTORY = (
    PROJECT_DIRECTORY
    / "output"
)

DEFAULT_LOG_DIRECTORY = (
    PROJECT_DIRECTORY
    / "logs"
)


# ==========================================================
# PIPELINE CONFIGURATION
# ==========================================================

@dataclass
class PipelineConfig:

    resume_directory: Path

    job_directory: Path

    output_directory: Path

    log_directory: Path

    output_filename: str

    recursive: bool = False

    stop_on_error: bool = False

    verbose: bool = False

    @property
    def output_path(self) -> Path:

        return (
            self.output_directory
            / self.output_filename
        )


# ==========================================================
# PROCESSING STATISTICS
# ==========================================================

@dataclass
class PipelineStatistics:

    resume_files_found: int = 0

    resume_profiles_created: int = 0

    resume_failures: int = 0

    job_files_found: int = 0

    job_profiles_created: int = 0

    job_failures: int = 0

    jobs_ranked: int = 0

    comparisons_completed: int = 0

    ranking_failures: int = 0

    report_generated: bool = False

    elapsed_seconds: float = 0.0


# ==========================================================
# COMMAND-LINE ARGUMENTS
# ==========================================================

def build_argument_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "ATS Final deterministic recruiter-style ranking pipeline."
        )
    )

    parser.add_argument(
        "--resumes",
        type=str,
        default=str(
            DEFAULT_RESUME_DIRECTORY
        ),
        help=(
            "Directory containing resume files."
        ),
    )

    parser.add_argument(
        "--jobs",
        type=str,
        default=str(
            DEFAULT_JOB_DIRECTORY
        ),
        help=(
            "Directory containing job-description files."
        ),
    )

    parser.add_argument(
        "--output-directory",
        type=str,
        default=str(
            DEFAULT_OUTPUT_DIRECTORY
        ),
        help=(
            "Directory where the Excel report will be saved."
        ),
    )

    parser.add_argument(
        "--output-file",
        type=str,
        default="",
        help=(
            "Output Excel filename. "
            "A timestamped filename is used when omitted."
        ),
    )

    parser.add_argument(
        "--log-directory",
        type=str,
        default=str(
            DEFAULT_LOG_DIRECTORY
        ),
        help=(
            "Directory where execution logs will be saved."
        ),
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help=(
            "Search resume and job directories recursively."
        ),
    )

    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help=(
            "Stop processing when a file fails."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Enable detailed console logging."
        ),
    )

    return parser


# ==========================================================
# CONFIGURATION CREATION
# ==========================================================

def create_pipeline_config(
    arguments: argparse.Namespace,
) -> PipelineConfig:

    output_filename = str(
        arguments.output_file or ""
    ).strip()

    if not output_filename:

        output_filename = (
            "ATS_Result_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            + ".xlsx"
        )

    if not output_filename.lower().endswith(
        ".xlsx"
    ):

        output_filename += ".xlsx"

    return PipelineConfig(
        resume_directory=Path(
            arguments.resumes
        ).expanduser().resolve(),
        job_directory=Path(
            arguments.jobs
        ).expanduser().resolve(),
        output_directory=Path(
            arguments.output_directory
        ).expanduser().resolve(),
        log_directory=Path(
            arguments.log_directory
        ).expanduser().resolve(),
        output_filename=output_filename,
        recursive=bool(
            arguments.recursive
        ),
        stop_on_error=bool(
            arguments.stop_on_error
        ),
        verbose=bool(
            arguments.verbose
        ),
    )


# ==========================================================
# DIRECTORY INITIALIZATION
# ==========================================================

def initialize_directories(
    config: PipelineConfig,
) -> None:

    config.resume_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    config.job_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    config.output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    config.log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ==========================================================
# LOGGING
# ==========================================================

def configure_logging(
    config: PipelineConfig,
) -> logging.Logger:

    log_filename = (
        "ATS_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".log"
    )

    log_path = (
        config.log_directory
        / log_filename
    )

    log_level = (
        logging.DEBUG
        if config.verbose
        else logging.INFO
    )

    logger = logging.getLogger(
        "ATS_V4"
    )

    logger.setLevel(
        log_level
    )

    logger.propagate = False

    if logger.handlers:

        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(
        sys.stdout
    )

    console_handler.setLevel(
        log_level
    )

    console_handler.setFormatter(
        formatter
    )

    file_handler = logging.FileHandler(
        log_path,
        encoding="utf-8",
    )

    file_handler.setLevel(
        logging.DEBUG
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    logger.addHandler(
        file_handler
    )

    logger.debug(
        "Logging initialized: %s",
        log_path,
    )

    return logger


# ==========================================================
# FILE DISCOVERY
# ==========================================================

def discover_files(
    directory: Path,
    supported_extensions: Iterable[str],
    recursive: bool = False,
) -> List[Path]:

    if not directory.exists():

        return []

    normalized_extensions = {
        str(extension).lower()
        for extension in supported_extensions
    }

    iterator = (
        directory.rglob("*")
        if recursive
        else directory.glob("*")
    )

    discovered_files = [
        path
        for path in iterator
        if (
            path.is_file()
            and path.suffix.lower()
            in normalized_extensions
            and not path.name.startswith("~$")
        )
    ]

    discovered_files.sort(
        key=lambda path: (
            path.name.lower(),
            str(path).lower(),
        )
    )

    return discovered_files


# ==========================================================
# PARSER INVOCATION ADAPTER
# ==========================================================

def invoke_parser(
    parser: Any,
    file_path: Path,
) -> Any:

    parser_methods = [
        "parse_file_many",
        "parse_file",
        "parse",
        "extract",
        "process",
    ]

    last_type_error: Optional[
        Exception
    ] = None

    for method_name in parser_methods:

        method = getattr(
            parser,
            method_name,
            None,
        )

        if not callable(method):

            continue

        try:

            return method(
                str(file_path)
            )

        except TypeError as error:

            last_type_error = error

            try:

                return method(
                    file_path
                )

            except TypeError as second_error:

                last_type_error = (
                    second_error
                )

    if callable(parser):

        try:

            return parser(
                str(file_path)
            )

        except TypeError:

            return parser(
                file_path
            )

    if last_type_error:

        raise last_type_error

    raise AttributeError(
        f"{parser.__class__.__name__} "
        "does not expose a supported parsing method."
    )


# ==========================================================
# PROFILE NORMALIZATION
# ==========================================================

def normalize_parser_result(
    parser_result: Any,
) -> List[Any]:

    if parser_result is None:

        return []

    if isinstance(
        parser_result,
        (
            list,
            tuple,
            set,
        ),
    ):

        return [
            profile
            for profile in parser_result
            if profile is not None
        ]

    return [
        parser_result
    ]


# ==========================================================
# RESUME PROFILE METADATA
# ==========================================================

def attach_resume_metadata(
    profile: Any,
    file_path: Path,
) -> Any:

    metadata_values = {
        "filename": file_path.name,
        "file_name": file_path.name,
        "file_path": str(
            file_path
        ),
        "source_path": str(
            file_path
        ),
    }

    for attribute, value in metadata_values.items():

        current_value = getattr(
            profile,
            attribute,
            None,
        )

        if current_value:

            continue

        try:

            setattr(
                profile,
                attribute,
                value,
            )

        except Exception:

            pass

    return profile


# ==========================================================
# JOB PROFILE METADATA
# ==========================================================

def attach_job_metadata(
    profile: Any,
    file_path: Path,
    profile_index: int,
) -> Any:

    fallback_job_id = (
        file_path.stem
        if profile_index == 1
        else (
            f"{file_path.stem}_"
            f"{profile_index}"
        )
    )

    metadata_values = {
        "source_file": file_path.name,
        "source_path": str(
            file_path
        ),
        "job_id": fallback_job_id,
    }

    for attribute, value in metadata_values.items():

        current_value = getattr(
            profile,
            attribute,
            None,
        )

        if current_value:

            continue

        try:

            setattr(
                profile,
                attribute,
                value,
            )

        except Exception:

            pass

    title = getattr(
        profile,
        "title",
        None,
    )

    if not title:

        try:

            setattr(
                profile,
                "title",
                file_path.stem.replace(
                    "_",
                    " ",
                ),
            )

        except Exception:

            pass

    return profile


# ==========================================================
# RESUME LOADING
# ==========================================================

def load_resume_profiles(
    resume_parser: ResumeParser,
    resume_files: List[Path],
    statistics: PipelineStatistics,
    logger: logging.Logger,
    stop_on_error: bool = False,
) -> List[Any]:

    resume_profiles: List[Any] = []

    statistics.resume_files_found = len(
        resume_files
    )

    for file_number, file_path in enumerate(
        resume_files,
        start=1,
    ):

        logger.info(
            "Parsing resume %s/%s: %s",
            file_number,
            len(resume_files),
            file_path.name,
        )

        try:

            parser_result = invoke_parser(
                parser=resume_parser,
                file_path=file_path,
            )

            profiles = normalize_parser_result(
                parser_result
            )

            if not profiles:

                raise ValueError(
                    "Resume parser returned no profile."
                )

            for profile in profiles:

                attach_resume_metadata(
                    profile=profile,
                    file_path=file_path,
                )

                resume_profiles.append(
                    profile
                )

                statistics.resume_profiles_created += 1

        except Exception as error:

            statistics.resume_failures += 1

            logger.exception(
                "Resume parsing failed for %s: %s",
                file_path,
                error,
            )

            if stop_on_error:

                raise

    return resume_profiles


# ==========================================================
# JOB LOADING
# ==========================================================

def load_job_profiles(
    jd_parser: JDParser,
    job_files: List[Path],
    statistics: PipelineStatistics,
    logger: logging.Logger,
    stop_on_error: bool = False,
) -> List[Any]:

    job_profiles: List[Any] = []

    statistics.job_files_found = len(
        job_files
    )

    for file_number, file_path in enumerate(
        job_files,
        start=1,
    ):

        logger.info(
            "Parsing job file %s/%s: %s",
            file_number,
            len(job_files),
            file_path.name,
        )

        try:

            parser_result = invoke_parser(
                parser=jd_parser,
                file_path=file_path,
            )

            profiles = normalize_parser_result(
                parser_result
            )

            if not profiles:

                raise ValueError(
                    "JD parser returned no job profiles."
                )

            for profile_index, profile in enumerate(
                profiles,
                start=1,
            ):

                attach_job_metadata(
                    profile=profile,
                    file_path=file_path,
                    profile_index=profile_index,
                )

                job_profiles.append(
                    profile
                )

                statistics.job_profiles_created += 1

        except Exception as error:

            statistics.job_failures += 1

            logger.exception(
                "Job parsing failed for %s: %s",
                file_path,
                error,
            )

            if stop_on_error:

                raise

    return job_profiles


# ==========================================================
# ENGINE INITIALIZATION
# ==========================================================

def initialize_resume_parser() -> ResumeParser:

    return ResumeParser()


def initialize_jd_parser() -> JDParser:

    return JDParser()


def initialize_ranking_engine() -> ATSRankingEngine:

    return ATSRankingEngine()


def initialize_report_generator(
    output_directory: Path,
) -> ATSReportGenerator:

    return ATSReportGenerator(
        output_directory=str(
            output_directory
        )
    )


# ==========================================================
# INPUT VALIDATION
# ==========================================================

def validate_pipeline_inputs(
    resume_files: List[Path],
    job_files: List[Path],
) -> None:

    if not resume_files:

        raise FileNotFoundError(
            "No supported resume files were found."
        )

    if not job_files:

        raise FileNotFoundError(
            "No supported job-description files "
            "were found."
        )


# ==========================================================
# TIME FORMATTER
# ==========================================================

def format_duration(
    seconds: float,
) -> str:

    seconds = max(
        float(seconds),
        0.0,
    )

    if seconds < 60:

        return f"{seconds:.2f} seconds"

    minutes, remaining_seconds = divmod(
        seconds,
        60,
    )

    if minutes < 60:

        return (
            f"{int(minutes)} minutes "
            f"{remaining_seconds:.2f} seconds"
        )

    hours, remaining_minutes = divmod(
        minutes,
        60,
    )

    return (
        f"{int(hours)} hours "
        f"{int(remaining_minutes)} minutes "
        f"{remaining_seconds:.2f} seconds"
    )


# ==========================================================
# PART 2
# ==========================================================
#
# Part 2 will add:
#
# - execute_ranking_pipeline()
# - generate_excel_report()
# - print_execution_summary()
# - run_pipeline()
# - main()
# - if __name__ == "__main__"
#
# ==========================================================
# ==========================================================
# ATS Final 1.0
# Main Pipeline
# File: ATS/main.py
# Part 2: Execution, Ranking, Reporting, and Entry Point
# ==========================================================


# ==========================================================
# RANKING PIPELINE
# ==========================================================

def execute_ranking_pipeline(
    ranking_engine: ATSRankingEngine,
    resume_profiles: List[Any],
    job_profiles: List[Any],
    statistics: PipelineStatistics,
    logger: logging.Logger,
    stop_on_error: bool = False,
) -> List[Any]:

    ranking_results: List[Any] = []

    for job_number, job_profile in enumerate(
        job_profiles,
        start=1,
    ):

        job_name = str(
            getattr(
                job_profile,
                "title",
                "",
            )
            or getattr(
                job_profile,
                "job_id",
                "",
            )
            or f"Job {job_number}"
        )

        logger.info(
            "Ranking resumes for job %s/%s: %s",
            job_number,
            len(job_profiles),
            job_name,
        )

        try:

            ranking_result = (
                ranking_engine.rank_resumes(
                    resume_profiles=resume_profiles,
                    job_profile=job_profile,
                )
            )

            ranking_results.append(
                ranking_result
            )

            statistics.jobs_ranked += 1

            statistics.comparisons_completed += len(
                getattr(
                    ranking_result,
                    "rankings",
                    [],
                )
                or []
            )

            logger.info(
                "Completed ranking for %s | "
                "Best Resume: %s | "
                "Best Score: %.2f",
                job_name,
                getattr(
                    ranking_result,
                    "best_resume",
                    "",
                ),
                float(
                    getattr(
                        ranking_result,
                        "best_score",
                        0.0,
                    )
                    or 0.0
                ),
            )

        except Exception as error:

            statistics.ranking_failures += 1

            logger.exception(
                "Ranking failed for job %s: %s",
                job_name,
                error,
            )

            if stop_on_error:

                raise

    return ranking_results


# ==========================================================
# REPORT GENERATION
# ==========================================================

def generate_excel_report(
    report_generator: ATSReportGenerator,
    ranking_results: List[Any],
    output_path: Path,
    statistics: PipelineStatistics,
    logger: logging.Logger,
) -> str:

    if not ranking_results:

        raise ValueError(
            "No ranking results are available "
            "for report generation."
        )

    logger.info(
        "Generating Excel report: %s",
        output_path,
    )

    report_path = report_generator.generate(
        ranking_results=ranking_results,
        output_file=str(
            output_path
        ),
    )

    statistics.report_generated = True

    logger.info(
        "Excel report generated successfully: %s",
        report_path,
    )

    return report_path


# ==========================================================
# EXECUTION SUMMARY
# ==========================================================

def print_execution_summary(
    statistics: PipelineStatistics,
    report_path: Optional[str],
    logger: logging.Logger,
) -> None:

    separator = "=" * 64

    logger.info(separator)
    logger.info("ATS FINAL EXECUTION SUMMARY")
    logger.info(separator)

    logger.info(
        "Resume files found       : %s",
        statistics.resume_files_found,
    )

    logger.info(
        "Resume profiles created  : %s",
        statistics.resume_profiles_created,
    )

    logger.info(
        "Resume failures          : %s",
        statistics.resume_failures,
    )

    logger.info(
        "Job files found          : %s",
        statistics.job_files_found,
    )

    logger.info(
        "Job profiles created     : %s",
        statistics.job_profiles_created,
    )

    logger.info(
        "Job parsing failures     : %s",
        statistics.job_failures,
    )

    logger.info(
        "Jobs ranked              : %s",
        statistics.jobs_ranked,
    )

    logger.info(
        "Comparisons completed    : %s",
        statistics.comparisons_completed,
    )

    logger.info(
        "Ranking failures         : %s",
        statistics.ranking_failures,
    )

    logger.info(
        "Report generated         : %s",
        statistics.report_generated,
    )

    logger.info(
        "Execution time           : %s",
        format_duration(
            statistics.elapsed_seconds
        ),
    )

    if report_path:

        logger.info(
            "Output report           : %s",
            report_path,
        )

    logger.info(separator)


# ==========================================================
# PIPELINE EXECUTION
# ==========================================================

def run_pipeline(
    config: PipelineConfig,
) -> int:

    start_time = time.perf_counter()

    statistics = PipelineStatistics()

    report_path: Optional[str] = None

    initialize_directories(
        config
    )

    logger = configure_logging(
        config
    )

    logger.info(
        "Starting ATS Final pipeline."
    )

    logger.info(
        "Resume directory: %s",
        config.resume_directory,
    )

    logger.info(
        "Job directory: %s",
        config.job_directory,
    )

    logger.info(
        "Output directory: %s",
        config.output_directory,
    )

    try:

        resume_files = discover_files(
            directory=(
                config.resume_directory
            ),
            supported_extensions=(
                SUPPORTED_RESUME_EXTENSIONS
            ),
            recursive=config.recursive,
        )

        job_files = discover_files(
            directory=config.job_directory,
            supported_extensions=(
                SUPPORTED_JOB_EXTENSIONS
            ),
            recursive=config.recursive,
        )

        logger.info(
            "Discovered %s resume files.",
            len(resume_files),
        )

        logger.info(
            "Discovered %s job files.",
            len(job_files),
        )

        validate_pipeline_inputs(
            resume_files=resume_files,
            job_files=job_files,
        )

        resume_parser = (
            initialize_resume_parser()
        )

        jd_parser = (
            initialize_jd_parser()
        )

        ranking_engine = (
            initialize_ranking_engine()
        )

        report_generator = (
            initialize_report_generator(
                output_directory=(
                    config.output_directory
                )
            )
        )

        resume_profiles = load_resume_profiles(
            resume_parser=resume_parser,
            resume_files=resume_files,
            statistics=statistics,
            logger=logger,
            stop_on_error=(
                config.stop_on_error
            ),
        )

        if not resume_profiles:

            raise RuntimeError(
                "No resume profiles were created."
            )

        logger.info(
            "Created %s resume profiles.",
            len(resume_profiles),
        )

        job_profiles = load_job_profiles(
            jd_parser=jd_parser,
            job_files=job_files,
            statistics=statistics,
            logger=logger,
            stop_on_error=(
                config.stop_on_error
            ),
        )

        if not job_profiles:

            raise RuntimeError(
                "No job profiles were created."
            )

        logger.info(
            "Created %s job profiles.",
            len(job_profiles),
        )

        ranking_results = (
            execute_ranking_pipeline(
                ranking_engine=ranking_engine,
                resume_profiles=resume_profiles,
                job_profiles=job_profiles,
                statistics=statistics,
                logger=logger,
                stop_on_error=(
                    config.stop_on_error
                ),
            )
        )

        if not ranking_results:

            raise RuntimeError(
                "No ranking results were generated."
            )

        report_path = generate_excel_report(
            report_generator=report_generator,
            ranking_results=ranking_results,
            output_path=config.output_path,
            statistics=statistics,
            logger=logger,
        )

        return_code = 0

    except KeyboardInterrupt:

        logger.warning(
            "ATS pipeline was interrupted by the user."
        )

        return_code = 130

    except Exception as error:

        logger.exception(
            "ATS pipeline failed: %s",
            error,
        )

        return_code = 1

    finally:

        statistics.elapsed_seconds = (
            time.perf_counter()
            - start_time
        )

        print_execution_summary(
            statistics=statistics,
            report_path=report_path,
            logger=logger,
        )

    return return_code


# ==========================================================
# MAIN ENTRY POINT
# ==========================================================

def main() -> int:

    argument_parser = (
        build_argument_parser()
    )

    arguments = (
        argument_parser.parse_args()
    )

    config = create_pipeline_config(
        arguments
    )

    return run_pipeline(
        config
    )


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
