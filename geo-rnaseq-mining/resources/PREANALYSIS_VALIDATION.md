# Formal pre-analysis validation

This module validates reviewed metadata and referenced input files without modifying
any user value. `validated_manifest.tsv` preserves every reviewed row, including
excluded rows, and only appends `validation_eligible` and
`validation_issue_count`.

## Severity behavior

| Severity | Behavior |
|---|---|
| `critical` | `enforce_validation_gate` stops the workflow after the HTML report is written |
| `error` | The affected `analysis_id` is added to `blocked_analysis_ids` |
| `warning` | Execution is allowed, but the warning is shown in the report |
| `info` | Audit record only |

Future formal analysis rules must call
`enforce_validation_gate.py --analysis-id <analysis_id>` before execution.

## Major checks and remediation

| Check ID | Meaning | Required action |
|---|---|---|
| `REVIEWED_MANIFEST_MISSING` | Reviewed manifest is absent | Restore and manually review the template |
| `DUPLICATE_SAMPLE_ID` | Analysis sample ID is not unique | Assign unique IDs without deleting excluded rows |
| `PENDING_SAMPLE_INCLUDED` | Pending sample has `include=true` | Confirm it or set `include=false` |
| `EXCLUDED_SAMPLE_INCLUDED` | Excluded sample is included | Retain the row and set `include=false` |
| `DUPLICATE_GSM_ID`, `DUPLICATE_SRR_ID` | Source identity maps to multiple samples | Resolve manually; never merge automatically |
| `INPUT_PATH_NOT_FOUND` | Reviewed path does not exist | Correct the reviewed relative path or restore the file |
| `INCOMPLETE_PAIRED_FASTQ` | Paired library lacks one mate | Supply both mates or correct layout |
| `COUNT_MATRIX_FORMAT_MISMATCH` | Bulk/pseudobulk matrix format is incompatible | Provide tabular raw counts |
| `COUNT_SAMPLE_COLUMNS_MISSING` | Matrix columns do not match `sample_id` | Correct matrix identity; reviewed IDs are not renamed |
| `NON_INTEGER_COUNT_MATRIX` | Fractional values found | Use raw integer counts, never TPM/FPKM/CPM/log values |
| `GROUP_MISSING` | Included sample has no group | Fill group manually |
| `SUBJECT_ID_MISSING` | Biological replicate unit is absent | Fill subject_id manually |
| `SUBJECT_GROUP_CONFLICT` | An unpaired subject has conflicting groups | Correct subject/group or define a paired design |
| `CONTRAST_GROUP_NOT_FOUND` | Numerator or denominator is absent | Correct the contrast without reversing direction automatically |
| `INSUFFICIENT_SUBJECT_REPLICATES` | Too few biological replicates | Add subjects, change threshold explicitly, or disable contrast |
| `INCOMPLETE_PAIR`, `PAIR_SUBJECT_CONFLICT` | Pairing is incomplete or inconsistent | Correct paired_group and subject_id manually |
| `DESIGN_FORMULA_INVALID` | Formula references invalid syntax/variables | Correct the confirmed formula |
| `DESIGN_MATRIX_NOT_FULL_RANK` | Model is unidentifiable | Resolve confounding; batch correction is not a repair |
| `ZERO_VARIANCE_COVARIATE` | Formula variable has no variation | Remove it explicitly or provide an estimable design |
| `SEVERE_MISSING_COVARIATE` | Missingness exceeds configured threshold | Complete metadata or revise formula; no imputation occurs |
| `PLANNED_DATASET_NOT_FOUND` | Plan references unknown dataset | Correct reviewed dataset_id |
| `VALIDATION_DATA_IN_DISCOVERY_MODEL` | Validation data contributes to discovery estimation | Use a separate/stratified validation analysis |
| `DATASET_GROUP_COMPLETE_CONFOUNDING` | Joint model cannot distinguish dataset from group | Stop and revise plan; no automatic Meta fallback |
| `DATASET_SAMPLE_SIZE_DOMINANCE` | One dataset dominates sample size | Review influence and interpretation |
| `INCOMPATIBLE_SPECIES_MERGED` | Merge group contains different species | Separate datasets |
| `INCOMPATIBLE_REFERENCE_GENOMES` | Reference builds differ or are unknown | Confirm compatible references explicitly |
| `INCOMPATIBLE_GENE_ID_SPACES` | Gene identifiers differ or are unknown | Harmonize derived matrices explicitly before analysis |
| `INCOMPATIBLE_DATA_TYPES_MERGED` | Different assay types are merged | Separate types or revise the reviewed plan |
| `META_DATASET_NOT_ESTIMABLE` | Dataset cannot estimate a Meta component | Add replication or exclude it explicitly |
| `SINGLE_CELL_SUBJECT_ID_MISSING` | Single-cell sample has no donor | Supply donor-level subject_id |
| `SUBJECT_ID_LOOKS_LIKE_BARCODE` | Barcode may be used as subject | Replace with biological donor ID |
| `PSEUDOBULK_INSUFFICIENT_DONORS` | Too few donors | Add donor-level replication |
| `INSUFFICIENT_CELLS_PER_CELLTYPE_SAMPLE` | Cell count below threshold | Review QC or exclude explicitly |
| `INSUFFICIENT_DONORS_PER_CELLTYPE_GROUP` | Cell type lacks donor replication | Do not treat cells as replicates |
| `CELLTYPE_ONE_TO_MANY_CONFLICT` | One author label maps to multiple targets | Resolve one reviewed mapping |
| `AUTHOR_LABEL_POSSIBLY_OVERWRITTEN` | Original label appears replaced | Restore author_label verbatim |

## Optional compatibility inputs

Per-dataset compatibility is supplied explicitly in `config.yaml`:

```yaml
validation:
  dataset_compatibility:
    GSE_A:
      species: Homo sapiens
      reference_genome: GRCh38
      gene_id_space: Ensembl_gene_id
```

For single-cell cell/donor sufficiency checks, set `celltype_metrics_file` to a
derived TSV with exactly:

```text
dataset_id  sample_id  subject_id  author_label  cell_count
```

This metrics file is derived evidence, not an authority file, and never replaces
the reviewed manifest or ontology.
