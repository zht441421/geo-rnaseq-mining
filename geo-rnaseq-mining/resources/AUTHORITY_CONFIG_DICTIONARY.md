# Reviewed authority configuration dictionary

These four TSV files are the only authoritative inputs for formal analysis:

1. `metadata/reviewed/sample_manifest.tsv`
2. `config/contrasts.tsv`
3. `config/dataset_plan.tsv`
4. `config/celltype_ontology.tsv`

The validator reads them as UTF-8 TSV, requires the exact ordered headers, rejects
extra columns and surrounding whitespace, and verifies that file SHA-256 values do
not change during validation. It never fills, rewrites, sorts, filters, or normalizes
reviewed values.

Use lowercase `true` and `false` for booleans. Use `NA` only for fields that are
not applicable or are intentionally unresolved. Do not use `NA` for required IDs,
contrast direction, design formula, or analysis strategy.

## sample_manifest.tsv

| Field | Meaning | Legal values / requirements |
|---|---|---|
| `dataset_id` | Workflow dataset identifier | Required; must match `dataset_plan.tsv` when a plan exists |
| `gse_id` | Original GEO series accession | Required string |
| `gsm_id` | Original GEO sample accession | Required string |
| `srx_id` | Original SRA experiment accession | String or `NA` |
| `srr_id` | Original SRA run accession | String or `NA` |
| `sample_id` | Unique analysis sample identifier | Required and globally unique, including excluded rows |
| `subject_id` | Biological replicate unit | Required for any `data_type` containing `pseudobulk` |
| `include` | Whether formal analysis may use the row | Exactly `true` or `false` |
| `group` | Human-confirmed analysis group | User-defined string |
| `condition` | Human-confirmed biological/clinical condition | User-defined string |
| `tissue` | Human-confirmed tissue | User-defined string |
| `batch` | Human-confirmed batch | User-defined string or `NA` |
| `sex` | Human-confirmed sex metadata | User-defined string or `NA` |
| `age` | Original/reviewed age representation | String; units must be retained in notes if needed |
| `timepoint` | Human-confirmed timepoint | User-defined string or `NA` |
| `treatment` | Human-confirmed treatment | User-defined string or `NA` |
| `paired_group` | Human-confirmed pairing identifier | User-defined string or `NA` |
| `data_type` | Human-confirmed assay/data unit | Required string; pseudobulk values must contain `pseudobulk` |
| `library_layout` | Reviewed library layout | Source-preserving string such as `PAIRED`, `SINGLE`, or `NA` |
| `matrix_path` | Reviewed matrix path | Relative path or `NA` |
| `fastq_r1` | Reviewed read-1 path | Relative path or `NA` |
| `fastq_r2` | Reviewed read-2 path | Relative path or `NA` |
| `notes` | General review notes | Free text without tabs/newlines |
| `reviewer_note` | Reviewer rationale or audit note | Free text without tabs/newlines |
| `review_status` | Review state | `pending`, `confirmed`, or `excluded` |

Cross-field rules:

- `include=true` requires `review_status=confirmed`.
- `review_status=excluded` requires `include=false`.
- Excluded rows remain in the file and still require a unique `sample_id`.
- The validator never infers `subject_id`, pairing, group, batch, or data type.

## contrasts.tsv

| Field | Meaning | Legal values / requirements |
|---|---|---|
| `contrast_id` | Unique contrast identifier | Required and globally unique |
| `analysis_id` | Analysis identifier | Required; must exist in `dataset_plan.tsv` |
| `data_scope` | Analysis family | `bulk`, `scrna_pseudobulk`, `bulk_meta`, `scrna_meta`, `cell_proportion` |
| `numerator` | Numerator group | Required; must differ from denominator |
| `denominator` | Denominator/reference group | Required; must differ from numerator |
| `subset_column` | Optional subset column | Column name or `NA` |
| `subset_value` | Optional subset value | Value or `NA` |
| `design_formula` | Exact user-confirmed formula | Required and cannot be `NA` |
| `paired` | Whether design is paired | Exactly `true` or `false` |
| `min_replicates_per_group` | Required replicate threshold | Integer greater than or equal to 1 |
| `enabled` | Whether contrast should run | Exactly `true` or `false` |
| `notes` | Contrast rationale | Free text |

The program validates these values but never chooses or reverses numerator,
denominator, design formula, or paired state.

## dataset_plan.tsv

| Field | Meaning | Legal values / requirements |
|---|---|---|
| `analysis_id` | Analysis identifier | Required |
| `dataset_id` | Dataset identifier | Required |
| `include` | Whether the dataset participates | Exactly `true` or `false` |
| `role` | Dataset role | `discovery`, `validation`, `supplementary` |
| `merge_group` | Explicit merge grouping | User-defined string or `NA` |
| `analysis_strategy` | Exact user-selected strategy | `joint_model`, `per_dataset_meta`, `stratified_validation`, `independent_only` |
| `reference_dataset` | Explicit reference dataset | Dataset ID or `NA` |
| `notes` | Planning rationale | Free text |

The `(analysis_id, dataset_id)` pair must be unique. The program does not switch
strategies when a requested strategy is inconvenient; later compatibility checks
must stop with an error instead.

## celltype_ontology.tsv

| Field | Meaning | Legal values / requirements |
|---|---|---|
| `dataset_id` | Dataset identifier | Required; must occur in manifest or dataset plan when those are populated |
| `author_label` | Original author-provided label | Required, preserved verbatim, unique within dataset |
| `harmonized_level1` | Broad harmonized label | User-confirmed string or `NA` |
| `harmonized_level2` | Intermediate harmonized label | User-confirmed string or `NA` |
| `harmonized_level3` | Fine harmonized label | User-confirmed string or `NA` |
| `mapping_method` | Mapping provenance | Required string, for example `manual_author_review` |
| `confidence` | Mapping confidence | `high`, `medium`, or `low` |
| `review_status` | Review state | `pending`, `confirmed`, or `excluded` |
| `notes` | Mapping rationale | Free text |

`author_label` is never replaced by a harmonized value.

## Error examples

```text
[INVALID_BOOLEAN] metadata/reviewed/sample_manifest.tsv:2 field='include'
value='TRUE': Boolean fields accept only lowercase 'true' or 'false'.
Suggested action: Replace the value explicitly with true or false; do not leave it unknown.
```

```text
[SCHEMA_VIOLATION] metadata/reviewed/sample_manifest.tsv:2 field='<row>'
value='': 'confirmed' was expected.
Suggested action: Correct the reviewed TSV explicitly according to the field dictionary.
```

```text
[DUPLICATE_SAMPLE_ID] metadata/reviewed/sample_manifest.tsv:4 field='sample_id'
value='SAMPLE_01': Duplicate key; first observed on line 2.
Suggested action: Assign unique reviewed identifiers; excluded rows must remain but still need unique keys.
```

```text
[IDENTICAL_CONTRAST_GROUPS] config/contrasts.tsv:2 field='numerator,denominator'
value='case': Numerator and denominator must be different.
Suggested action: Confirm contrast direction and enter two distinct group labels.
```
