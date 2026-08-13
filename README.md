# Resume Tailor — Local Ollama Version

This project reads your ATS `Summary` sheet, selects jobs below the configured score threshold, maps each job to its full JD, selects the best LaTeX base resume, asks Ollama for a structured content patch, validates the patch, writes a copied `.tex`, and optionally compiles a PDF.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

Install Ollama and pull a small model:

```bash
ollama pull qwen2.5:3b
```

For PDF compilation, install MiKTeX or TeX Live and confirm this works:

```bash
latexmk -v
```

## 2. Add LaTeX templates

The included `templates/azure_databricks.tex` comes from the supplied sample.

Add these files using the exact names below:

```text
templates/snowflake.tex
templates/informatica_abinitio.tex
```

The mapping is defined in `config.py`. Missing templates are safely skipped.

## 3. Verify the evidence bank

Review `data/resume_evidence.json`. Remove anything that is not accurate. Add only facts, tools, responsibilities, and metrics that you can defend.

## 4. Run a five-job test

```bash
python main.py \
  --ats-excel "C:/path/ATS_Result_20260805_162355.xlsx" \
  --filtered-jd "C:/path/Filtered_JDs_20260805_132521.docx" \
  --threshold 80 \
  --minimum-score 45 \
  --limit 5
```

Windows CMD users can edit and run `run_example.bat`.

To generate only `.tex` files:

```bash
python main.py --ats-excel "...xlsx" --filtered-jd "...docx" --no-compile
```

## 5. Output

Each run creates:

```text
outputs/Tailored_Resumes_YYYYMMDD_HHMMSS/
  tailoring_summary.csv
  tailoring_summary.json
  JOB_ID_JOB_NAME/
    job_input.json
    ollama_prompt.json
    proposed_patch.json
    validation.json
    tailored_resume.tex
    tailored_resume.pdf
    latex_compile.log
```

## Important behavior

- Jobs with score `>= 80` are ignored.
- Jobs below `--minimum-score` are ignored because very low scores often indicate role mismatch.
- Only the summary, skills, and latest two experience bullet blocks are changed.
- Employer names, dates, education, certifications, and older experiences remain untouched.
- Unsupported JD requirements are reported rather than inserted.
- The master LaTeX template is never overwritten.

## JD mapping

The JD reader first matches by `Job ID`, then exact normalized URL, then conservative Job ID containment. If your filtered JD document uses a different format, update only `engine/jd_reader.py`.

## Next integration

After validating the generated PDFs, connect your existing ATS engine as a subprocess to re-score each tailored PDF. The current version deliberately stops before that step because your ATS `main.py` invocation and input arguments were not supplied.
