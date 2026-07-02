# Resource, log, and benchmark policy

Every executable Snakemake rule must declare:

- `input`
- `output`
- `log`
- `benchmark`
- `threads`
- `resources` with `mem_mb`, `runtime_min`, and `disk_mb`

Defaults live in `config/config.yaml`. Rule-specific values may reference those defaults
but must not contain absolute paths.

Recommended paths:

- log: `logs/{module}/{dataset}/{rule}.{wildcards}.log`
- benchmark: `benchmarks/{module}/{dataset}/{rule}.{wildcards}.tsv`
- provenance: `resources/provenance/{analysis_id}/`

Errors must state the cause, the affected dataset or sample, and a suggested user action.
Warnings and critical errors must never silently mutate reviewed input.
