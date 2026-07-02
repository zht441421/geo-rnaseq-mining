# Project reporting

The reporting module creates a project-level HTML inventory without changing
analysis results or authority files.

## Outputs

```text
results/report/
├── project_report.html
├── result_manifest.tsv
├── provenance.json
└── .complete
```

The manifest records every result artifact outside the report directory with
its size and SHA-256 digest. Provenance records hashes for reviewed manifests,
contrasts, dataset plans, ontology mappings, configuration, and validation
status so that a report can be traced to the exact authority inputs.

Validation errors and warnings are summarized in the HTML report. Reporting
does not reinterpret failed gates as successful analyses and does not claim
that missing result modules were run.

Enable `reporting.enabled` and run:

```bash
snakemake --profile profiles/local results/report/.complete
```
