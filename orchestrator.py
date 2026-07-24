import subprocess
import time
from pathlib import Path
from pipeline import JOBS

status = {}

PROJECT_ROOT = Path(__file__).resolve().parent


def run_job(job_id):
    job = JOBS[job_id]

    # Check dependencies
    for dep in job["depends"]:
        if status.get(dep) != "SUCCESS":
            print(f"[SKIPPED] {job['name']} (Dependency '{dep}' failed)")
            status[job_id] = "SKIPPED"
            return

    print(f"\n[RUNNING] {job['name']}")

    start = time.time()

    try:
        script_path = PROJECT_ROOT / job["script"]

        subprocess.run(
            ["python", str(script_path)],
            check=True,
            cwd=PROJECT_ROOT
        )

        elapsed = time.time() - start

        print(f"[SUCCESS] {job['name']} ({elapsed:.1f}s)")
        status[job_id] = "SUCCESS"

    except subprocess.CalledProcessError:
        print(f"[FAILED] {job['name']}")
        status[job_id] = "FAILED"


def main():
    print("=" * 60)
    print("CAREER AUTOMATION PIPELINE")
    print("=" * 60)

    for job in JOBS:
        run_job(job)

    print()
    print("=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)

    for job in JOBS:
        print(f"{JOBS[job]['name']:<20} : {status.get(job)}")


if __name__ == "__main__":
    main()
