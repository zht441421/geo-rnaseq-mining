# Expression data entry and download

This module identifies technical entry points only. It never assigns case/control
groups and never changes reviewed `data_type`.

## Safe defaults

Both download switches are `false` by default:

```yaml
data_entry:
  supplementary_download_enabled: false
  supplementary_allowlist: []
  sra_download_enabled: false
```

Supplementary downloads require both `supplementary_download_enabled: true` and
an explicit allowlist match. SRA runs are taken only from confirmed,
`include=true` reviewed manifest rows.

## Classification policy

- Local files are classified from file content, magic bytes, HDF5 structure,
  Matrix Market headers, FASTQ records, and matrix values.
- Remote supplementary names produce only unverified hints.
- Raw bulk count candidates must be numeric, non-negative, and integer.
- TPM/FPKM/CPM/log-like/non-integer matrices are marked
  `exploratory_only_no_deseq2`.
- H5AD is recognized structurally, but its raw count layer remains a manual review
  requirement.
- A detected bulk/single-cell family conflict with reviewed `data_type` is written
  as `error:data_type_file_conflict`; the reviewed value is not replaced.

## SRA behavior

For each reviewed SRR:

1. `prefetch` downloads into `data/sra/{SRR}/`.
2. `vdb-validate` validates the archive.
3. `fasterq-dump --split-files` is used for reviewed paired-end runs.
4. `pigz` compresses outputs and `pigz -t` checks gzip integrity.
5. FASTQ structure and paired record counts are checked.
6. JSON marker files store size and SHA-256; verified files are reused.
7. Logs are stored separately as `logs/sra/{SRR}.prefetch.log` and
   `logs/sra/{SRR}.fasterq.log`.

## Commands

Inventory without enabling downloads:

```bash
snakemake --profile profiles/local results/compatibility/data_inventory.tsv
```

Optional real SRA integration test:

```bash
RUN_SRA_NETWORK_TESTS=1 \
SRA_TEST_ACCESSION=<small-reviewed-SRR> \
SRA_TEST_LAYOUT=SINGLE \
python -m unittest tests.integration.test_sra_optional -v
```

The test defaults to a `100M` prefetch limit and requires SRA Toolkit plus pigz.
