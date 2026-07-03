# Next Task

## Next Stage Goal

Perform a commit-readiness and dirty-working-tree audit for the current
repository state.

The next session should decide what belongs in the current commit, what is
generated output, what is unrelated prior work, and what should remain
unstaged. This task is an audit and staging plan only unless the user
explicitly asks to stage or commit.

## Files Allowed To Modify

For the audit report only:

- `docs/CURRENT_STATE.md`
- `docs/VALIDATION.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

If the user explicitly asks for a commit or staging changes, follow their
instruction and avoid reverting unrelated work.

## Files And Ranges Not To Modify By Default

- Do not modify code, workflow, schema, CI, tests, data, fixtures, or configs
  during the audit.
- Do not fix P1/P2/P3 issues during this task.
- Do not run real GEO/SRA network tests unless explicitly requested.
- Do not delete generated files or clean the working tree without explicit
  approval.
- Do not stage or commit files unless explicitly requested.

## Required Start Reads

Read these first:

- `AGENTS.md`
- `README.md`
- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/CHANGELOG.md`
- `docs/VALIDATION.md`
- `docs/NEXT_TASK.md`

Then inspect the actual file state; do not rely on handoff text alone.

## Implementation Steps

1. Record current branch, HEAD, and `git status --short`.
2. Group tracked modified files by category:
   - P0 default-entry repair;
   - previous stage workflow/scripts/tests/resource docs;
   - generated outputs or markers;
   - handoff Markdown;
   - unknown or unrelated changes.
3. Group untracked files by category:
   - docs/handoff files;
   - metadata templates;
   - workflow envs/rules/scripts;
   - tests;
   - generated markers;
   - unknown files.
4. Identify files that should likely be staged together for the P0 repair.
5. Identify files that require user confirmation before staging.
6. Produce a concise commit-readiness report.
7. Stop and wait for user confirmation before staging, committing, cleaning, or
   implementing any fixes.

## Validation Commands

This audit does not require rerunning tests by default. If validation is needed
because files changed after the last recorded run, use:

```bash
python -m compileall -q workflow scripts tests
python -m unittest discover -s tests/unit -p "test_*.py" -v
pytest tests/unit -q
python -m unittest discover -s tests/integration -p "test_*.py" -v
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1 --printshellcmds
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --forceall all_full
snakemake --snakefile workflow/Snakefile --cores 1 --configfile tests/fixtures/config/test_config.yaml
```

If tests are not rerun, explicitly state that the latest validation status is
from `docs/VALIDATION.md`.

## Completion Standard

- Current dirty working tree is categorized.
- Candidate staging set for the P0 repair is listed.
- Ambiguous or generated files needing user confirmation are listed.
- No files are staged, committed, deleted, or reverted without explicit user
  confirmation.

## Stop Conditions

- Stop if the user asks only for audit results.
- Stop before staging or committing.
- Stop before deleting generated files.
- Stop before starting real-data validation.
- Stop before implementing P1/P2/P3 fixes.

## Do Not Handle Opportunistically

- Do not fix hard-coded config paths.
- Do not configure Conda strict channel priority.
- Do not add real GEO/SRA secrets or accessions.
- Do not run native R/Bioconductor production analyses.
- Do not refactor workflow rules or scripts.
