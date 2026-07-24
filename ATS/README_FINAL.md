# ATS Final 1.0

This is the consolidated final release. Replace the complete existing `ATS` folder.

## Run

```bash
python -m ATS.main
```

## Final architecture

- deterministic skill extraction and ontology inference
- BM25 and local sentence-transformer semantic matching
- role hierarchy and role-family compatibility
- dated project-block parsing
- platform specialization and platform-specific tenure
- evidence-weighted required and preferred skills
- target-relevant achievements and project complexity
- one authoritative final ranker and one set of weights
- no Ollama or external LLM calls

## Important scoring behavior

- Project/action evidence outranks a skills-list mention.
- Inferred skills receive partial credit only.
- Platform-specific roles use platform depth and specialization gates.
- Generic roles do not receive artificial platform penalties.
- Cross-platform experience remains transferable, but cannot fully offset a platform mismatch.
- Detailed Breakdown contains each final component only once.

## Validation

The package was compiled and run against the three supplied resumes and the supplied 65-job document. All 195 comparisons completed without ranking errors. The embedding model was replaced with a lightweight offline stub only for container validation; your configured local sentence-transformer remains unchanged.
