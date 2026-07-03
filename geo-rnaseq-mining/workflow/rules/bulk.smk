import csv
import json
import shlex
from collections import defaultdict
from pathlib import Path


BULK_RESULT_ROOT = "results/per_dataset"
BULK_ENABLED = bool(config["bulk"].get("enabled", False))
BULK_MANIFEST = config["geo"]["metadata_reviewed_file"]


def bulk_missing(value):
    return value is None or str(value) in {"", "NA", "N/A", "null", "None"}


def load_active_bulk_rows(path):
    grouped = defaultdict(list)
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            data_type = row.get("data_type", "").lower()
            if (
                row.get("include") == "true"
                and row.get("review_status") == "confirmed"
                and "bulk" in data_type
                and "pseudobulk" not in data_type
            ):
                grouped[row["dataset_id"]].append(row)
    return dict(grouped)


BULK_ROWS_BY_DATASET = load_active_bulk_rows(
    BULK_MANIFEST
)
BULK_DATASETS = sorted(BULK_ROWS_BY_DATASET) if BULK_ENABLED else []
BULK_ROW_BY_SAMPLE = {
    (dataset_id, row["sample_id"]): row
    for dataset_id, rows in BULK_ROWS_BY_DATASET.items()
    for row in rows
}
BULK_SAMPLE_IDS = {
    dataset_id: [row["sample_id"] for row in rows]
    for dataset_id, rows in BULK_ROWS_BY_DATASET.items()
}


def bulk_branch(dataset_id):
    rows = BULK_ROWS_BY_DATASET[dataset_id]
    has_matrix = any(not bulk_missing(row.get("matrix_path")) for row in rows)
    has_fastq = any(
        not bulk_missing(row.get("fastq_r1"))
        or not bulk_missing(row.get("fastq_r2"))
        for row in rows
    )
    if has_matrix and not has_fastq:
        return "matrix"
    if has_fastq and not has_matrix:
        return "fastq"
    raise ValueError(
        f"Dataset {dataset_id} must use exactly one bulk entry branch."
    )


def bulk_row(wildcards):
    return BULK_ROW_BY_SAMPLE[(wildcards.dataset, wildcards.sample)]


def bulk_fastq_r1(wildcards):
    return bulk_row(wildcards)["fastq_r1"]


def bulk_fastq_r2(wildcards):
    value = bulk_row(wildcards).get("fastq_r2", "NA")
    return [] if bulk_missing(value) else [value]


def bulk_fastq_inputs(wildcards):
    return [bulk_fastq_r1(wildcards), *bulk_fastq_r2(wildcards)]


def bulk_fastq_read_args(wildcards):
    row = bulk_row(wildcards)
    r1 = shlex.quote(row["fastq_r1"])
    r2 = row.get("fastq_r2", "NA")
    if not bulk_missing(r2):
        return f"-1 {r1} -2 {shlex.quote(r2)}"
    return f"-r {r1}"


def bulk_star_read_command(wildcards):
    reads = bulk_fastq_inputs(wildcards)
    return "--readFilesCommand zcat" if any(
        str(path).lower().endswith(".gz") for path in reads
    ) else ""


def bulk_paired_featurecounts(wildcards):
    return (
        "-p --countReadPairs"
        if str(bulk_row(wildcards).get("library_layout", "")).upper() == "PAIRED"
        else ""
    )


def bulk_matrix_path(dataset_id):
    paths = {
        row["matrix_path"]
        for row in BULK_ROWS_BY_DATASET[dataset_id]
        if not bulk_missing(row.get("matrix_path"))
    }
    if len(paths) != 1:
        raise ValueError(
            f"Dataset {dataset_id} must reference exactly one bulk count matrix."
        )
    return next(iter(paths))


def bulk_reference_input(key):
    def resolve_reference(wildcards):
        value = config["references"].get(key)
        if bulk_missing(value):
            raise ValueError(
                f"Reference field {key!r} is required for dataset "
                f"{wildcards.dataset}."
            )
        return value

    return resolve_reference


def bulk_fastqc_inputs_for_dataset(wildcards):
    return [
        f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/qc/fastqc/{sample}"
        for sample in BULK_SAMPLE_IDS[wildcards.dataset]
    ]


def bulk_salmon_quant_files(wildcards):
    return [
        f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/quantification/salmon/{sample}/quant.sf"
        for sample in BULK_SAMPLE_IDS[wildcards.dataset]
    ]


def bulk_salmon_meta_files(wildcards):
    return [
        f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/quantification/salmon/{sample}/aux_info/meta_info.json"
        for sample in BULK_SAMPLE_IDS[wildcards.dataset]
    ]


def bulk_featurecount_files(wildcards):
    return [
        f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/quantification/featurecounts/{sample}/counts.tsv"
        for sample in BULK_SAMPLE_IDS[wildcards.dataset]
    ]


def bulk_sample_id_args(wildcards):
    return " ".join(
        shlex.quote(sample) for sample in BULK_SAMPLE_IDS[wildcards.dataset]
    )


def bulk_source_counts(wildcards):
    branch = bulk_branch(wildcards.dataset)
    if branch == "matrix":
        return bulk_matrix_path(wildcards.dataset)
    method = config["bulk"]["quantification_method"]
    if method == "salmon_tximport":
        return (
            f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/"
            "quantification/salmon_tximport/gene_counts.tsv"
        )
    if method == "star_featurecounts":
        return (
            f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/"
            "quantification/star_featurecounts/gene_counts.tsv"
        )
    raise ValueError(f"Unsupported bulk quantification method: {method}")


def bulk_quantification_dependencies(wildcards):
    if bulk_branch(wildcards.dataset) == "matrix":
        return []
    method = config["bulk"]["quantification_method"]
    if method == "salmon_tximport":
        return bulk_salmon_meta_files(wildcards)
    return [
        f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/alignment/star/{sample}/Log.final.out"
        for sample in BULK_SAMPLE_IDS[wildcards.dataset]
    ]


def bulk_multiqc_dependency(wildcards):
    if bulk_branch(wildcards.dataset) == "fastq":
        return [
            f"{BULK_RESULT_ROOT}/{wildcards.dataset}/bulk/qc/multiqc/multiqc_report.html"
        ]
    return []


BULK_TARGETS = expand(
    f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/.complete",
    dataset=BULK_DATASETS,
)


rule bulk_fastqc:
    input:
        reads=bulk_fastq_inputs
    output:
        report_dir=directory(
            f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/fastqc/{{sample}}"
        )
    log:
        f"logs/bulk/{{dataset}}/fastqc/{{sample}}.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/fastqc/{{sample}}.tsv"
    conda:
        "../envs/bulk-fastqc.yaml"
    threads: config["resources"]["bulk"]["threads"]
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    shell:
        """
        mkdir -p {output.report_dir:q}
        fastqc --threads {threads} --outdir {output.report_dir:q} {input.reads:q} \
          > {log:q} 2>&1
        fastqc --version > {output.report_dir:q}/software_version.txt 2>&1
        """


rule bulk_multiqc:
    input:
        fastqc=bulk_fastqc_inputs_for_dataset
    output:
        report=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/multiqc/multiqc_report.html",
        data=directory(
            f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/multiqc/multiqc_data"
        ),
        version=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/multiqc/software_version.txt"
    log:
        f"logs/bulk/{{dataset}}/multiqc.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/multiqc.tsv"
    conda:
        "../envs/bulk-fastqc.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        output_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/multiqc"
    shell:
        """
        mkdir -p {params.output_dir:q}
        multiqc --force --outdir {params.output_dir:q} \
          --filename multiqc_report.html {input.fastqc:q} > {log:q} 2>&1
        multiqc --version > {output.version:q} 2>&1
        """


rule bulk_salmon_quant:
    input:
        index=bulk_reference_input("salmon_index"),
        reads=bulk_fastq_inputs
    output:
        quant=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon/{{sample}}/quant.sf",
        meta=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon/{{sample}}/aux_info/meta_info.json",
        version=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon/{{sample}}/software_version.txt"
    log:
        f"logs/bulk/{{dataset}}/salmon/{{sample}}.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/salmon/{{sample}}.tsv"
    conda:
        "../envs/bulk-salmon.yaml"
    threads: config["resources"]["bulk"]["threads"]
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        reads=bulk_fastq_read_args,
        libtype=config["bulk"]["salmon_libtype"],
        output_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon/{{sample}}",
        bias_flags=" ".join(
            [
                "--validateMappings"
                if config["bulk"]["salmon"].get("validate_mappings", True)
                else "",
                "--seqBias" if config["bulk"]["salmon"].get("seq_bias", True) else "",
                "--gcBias" if config["bulk"]["salmon"].get("gc_bias", True) else "",
                *config["bulk"]["salmon"].get("extra_args", []),
            ]
        )
    shell:
        """
        mkdir -p {params.output_dir:q}
        salmon quant --index {input.index:q} --libType {params.libtype:q} \
          {params.reads} {params.bias_flags} --threads {threads} \
          --output {params.output_dir:q} > {log:q} 2>&1
        salmon --version > {output.version:q} 2>&1
        """


rule bulk_tximport:
    input:
        quants=bulk_salmon_quant_files,
        metadata=bulk_salmon_meta_files,
        manifest=BULK_MANIFEST,
        tx2gene=bulk_reference_input("tx2gene")
    output:
        counts=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon_tximport/gene_counts.tsv",
        unrounded=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon_tximport/gene_estimated_counts_unrounded.tsv",
        abundance=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon_tximport/gene_abundance.tsv",
        length=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon_tximport/gene_length.tsv",
        summary=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon_tximport/tximport_summary.tsv",
        session=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon_tximport/session_info.txt"
    log:
        f"logs/bulk/{{dataset}}/tximport.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/tximport.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        quant_root=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/salmon"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_tximport.R \
          --manifest {input.manifest:q} \
          --dataset-id {wildcards.dataset:q} \
          --quant-root {params.quant_root:q} \
          --tx2gene {input.tx2gene:q} \
          --counts {output.counts:q} \
          --unrounded-counts {output.unrounded:q} \
          --abundance {output.abundance:q} \
          --length {output.length:q} \
          --summary {output.summary:q} \
          --session-info {output.session:q} \
          > {log:q} 2>&1
        """


rule bulk_star_align:
    input:
        index=bulk_reference_input("star_index"),
        reads=bulk_fastq_inputs
    output:
        bam=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/alignment/star/{{sample}}/Aligned.sortedByCoord.out.bam",
        final_log=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/alignment/star/{{sample}}/Log.final.out",
        star_log=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/alignment/star/{{sample}}/Log.out",
        version=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/alignment/star/{{sample}}/software_version.txt"
    log:
        f"logs/bulk/{{dataset}}/star/{{sample}}.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/star/{{sample}}.tsv"
    conda:
        "../envs/bulk-star-featurecounts.yaml"
    threads: config["resources"]["bulk"]["threads"]
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        prefix=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/alignment/star/{{sample}}/",
        read_command=bulk_star_read_command,
        extra=" ".join(config["bulk"]["star"].get("extra_args", []))
    shell:
        """
        mkdir -p {params.prefix:q}
        STAR --genomeDir {input.index:q} --readFilesIn {input.reads:q} \
          {params.read_command} --runThreadN {threads} \
          --outSAMtype BAM SortedByCoordinate \
          --outFileNamePrefix {params.prefix:q} {params.extra} \
          > {log:q} 2>&1
        STAR --version > {output.version:q} 2>&1
        """


rule bulk_featurecounts:
    input:
        bam=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/alignment/star/{{sample}}/Aligned.sortedByCoord.out.bam",
        gtf=bulk_reference_input("gtf")
    output:
        raw=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/featurecounts/{{sample}}/featurecounts.raw.tsv",
        summary=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/featurecounts/{{sample}}/featurecounts.raw.tsv.summary",
        counts=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/featurecounts/{{sample}}/counts.tsv",
        version=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/featurecounts/{{sample}}/software_version.txt"
    log:
        f"logs/bulk/{{dataset}}/featurecounts/{{sample}}.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/featurecounts/{{sample}}.tsv"
    conda:
        "../envs/bulk-star-featurecounts.yaml"
    threads: config["resources"]["bulk"]["threads"]
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        paired=bulk_paired_featurecounts,
        strand=config["bulk"]["featurecounts_strand"],
        extra=" ".join(config["bulk"]["featurecounts"].get("extra_args", []))
    shell:
        """
        mkdir -p $(dirname {output.raw:q})
        featureCounts -a {input.gtf:q} -o {output.raw:q} \
          -T {threads} -s {params.strand} \
          {params.paired} {params.extra} {input.bam:q} > {log:q} 2>&1
        featureCounts -v > {output.version:q} 2>&1
        python workflow/scripts/normalize_featurecounts.py \
          --input {output.raw:q} --sample-id {wildcards.sample:q} \
          --output {output.counts:q} >> {log:q} 2>&1
        """


rule bulk_merge_featurecounts:
    input:
        counts=bulk_featurecount_files
    output:
        counts=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/quantification/star_featurecounts/gene_counts.tsv"
    log:
        f"logs/bulk/{{dataset}}/merge_featurecounts.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/merge_featurecounts.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        sample_ids=bulk_sample_id_args
    shell:
        """
        python workflow/scripts/merge_bulk_counts.py \
          --inputs {input.counts:q} --sample-ids {params.sample_ids} \
          --output {output.counts:q} > {log:q} 2>&1
        """


rule prepare_bulk_dataset:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        config="config/config.yaml",
        manifest=BULK_MANIFEST,
        counts=bulk_source_counts
    output:
        counts=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/input/raw_counts.tsv",
        metadata=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/input/sample_metadata.tsv",
        validation=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/input/input_validation.tsv",
        provenance=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/provenance/input_provenance.json"
    log:
        f"logs/bulk/{{dataset}}/prepare_dataset.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/prepare_dataset.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_bulk_dataset.py \
          --config {input.config:q} --manifest {input.manifest:q} \
          --dataset-id {wildcards.dataset:q} --counts-input {input.counts:q} \
          --output-counts {output.counts:q} \
          --output-metadata {output.metadata:q} \
          --output-validation {output.validation:q} \
          --output-provenance {output.provenance:q} \
          > {log:q} 2>&1
        """


rule collect_bulk_quant_metrics:
    input:
        config="config/config.yaml",
        manifest=BULK_MANIFEST,
        quantification=bulk_quantification_dependencies,
        multiqc=bulk_multiqc_dependency,
        prepared=rules.prepare_bulk_dataset.output.counts
    output:
        metrics=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/quantification_metrics.tsv"
    log:
        f"logs/bulk/{{dataset}}/collect_quant_metrics.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/collect_quant_metrics.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        bulk_root=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk"
    shell:
        """
        python workflow/scripts/collect_bulk_quant_metrics.py \
          --config {input.config:q} --manifest {input.manifest:q} \
          --dataset-id {wildcards.dataset:q} \
          --bulk-root {params.bulk_root:q} \
          --output {output.metrics:q} > {log:q} 2>&1
        """


rule bulk_sample_qc:
    input:
        counts=rules.prepare_bulk_dataset.output.counts,
        metadata=rules.prepare_bulk_dataset.output.metadata,
        config="config/config.yaml"
    output:
        marker=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level/.complete",
        metrics=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level/sample_qc_metrics.tsv",
        outliers=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level/outlier_report.tsv",
        pca=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level/pca.png",
        distance=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level/sample_distance_heatmap.png",
        correlation=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level/correlation_heatmap.png",
        clustering=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level/hierarchical_clustering.png"
    log:
        f"logs/bulk/{{dataset}}/sample_qc.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/sample_qc.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        output_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/qc/sample_level"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_bulk_qc.R \
          --counts {input.counts:q} --metadata {input.metadata:q} \
          --config {input.config:q} --dataset-id {wildcards.dataset:q} \
          --output-dir {params.output_dir:q} > {log:q} 2>&1
        """


rule bulk_deseq2:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        design_validation=rules.validate_analysis_design.output.validation,
        counts=rules.prepare_bulk_dataset.output.counts,
        metadata=rules.prepare_bulk_dataset.output.metadata,
        qc=rules.bulk_sample_qc.output.marker,
        config="config/config.yaml",
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN
    output:
        marker=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/deseq2/.complete",
        manifest=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/deseq2/results_manifest.tsv",
        effects=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/deseq2/effect_direction_summary.tsv",
        session=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/deseq2/session_info.txt"
    log:
        f"logs/bulk/{{dataset}}/deseq2.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/deseq2.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: config["resources"]["bulk"]["threads"]
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        output_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/deseq2"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_bulk_deseq2.R \
          --counts {input.counts:q} --metadata {input.metadata:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --config {input.config:q} --dataset-id {wildcards.dataset:q} \
          --output-dir {params.output_dir:q} > {log:q} 2>&1
        """


rule bulk_enrichment:
    input:
        deseq=rules.bulk_deseq2.output.marker,
        manifest=rules.bulk_deseq2.output.manifest,
        config="config/config.yaml"
    output:
        marker=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/enrichment/.complete",
        status=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/enrichment/enrichment_status.tsv",
        optional=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/enrichment/optional_modules_status.tsv",
        session=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/enrichment/session_info.txt"
    log:
        f"logs/bulk/{{dataset}}/enrichment.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/enrichment.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        deseq_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/deseq2",
        output_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/enrichment"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_bulk_enrichment.R \
          --config {input.config:q} --dataset-id {wildcards.dataset:q} \
          --deseq-dir {params.deseq_dir:q} \
          --output-dir {params.output_dir:q} > {log:q} 2>&1
        """


rule bulk_optional_modules:
    input:
        deseq=rules.bulk_deseq2.output.marker,
        manifest=rules.bulk_deseq2.output.manifest,
        metadata=rules.prepare_bulk_dataset.output.metadata,
        config="config/config.yaml"
    output:
        marker=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/optional_modules/.complete",
        status=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/optional_modules/optional_modules_status.tsv",
        session=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/optional_modules/session_info.txt"
    log:
        f"logs/bulk/{{dataset}}/optional_modules.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/optional_modules.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: config["resources"]["bulk"]["threads"]
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        deseq_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/deseq2",
        output_dir=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/optional_modules"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_bulk_optional_modules.R \
          --config {input.config:q} --dataset-id {wildcards.dataset:q} \
          --deseq-dir {params.deseq_dir:q} \
          --metadata {input.metadata:q} \
          --output-dir {params.output_dir:q} > {log:q} 2>&1
        """


rule bulk_single_dataset_analysis:
    input:
        prepared=rules.prepare_bulk_dataset.output.counts,
        quantification=rules.collect_bulk_quant_metrics.output.metrics,
        qc=rules.bulk_sample_qc.output.marker,
        deseq=rules.bulk_deseq2.output.marker,
        enrichment=rules.bulk_enrichment.output.marker,
        optional=rules.bulk_optional_modules.output.marker
    output:
        marker=f"{BULK_RESULT_ROOT}/{{dataset}}/bulk/.complete"
    log:
        f"logs/bulk/{{dataset}}/complete.log"
    benchmark:
        f"benchmarks/bulk/{{dataset}}/complete.tsv"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    run:
        Path(output.marker).parent.mkdir(parents=True, exist_ok=True)
        Path(output.marker).write_text(
            json.dumps(
                {
                    "dataset_id": wildcards.dataset,
                    "status": "complete",
                    "samples_removed_by_workflow": 0,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        Path(log[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(log[0]).write_text(
            f"Completed independent bulk analysis for {wildcards.dataset}.\n",
            encoding="utf-8",
        )
