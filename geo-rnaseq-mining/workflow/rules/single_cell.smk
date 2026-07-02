import csv
import json
from collections import defaultdict
from pathlib import Path


SINGLE_CELL_ROOT = "results/per_dataset"
PSEUDOBULK_ROOT = "results/per_dataset"
MERGED_PSEUDOBULK_ROOT = "results/merged_analysis/scrna_pseudobulk"
META_PSEUDOBULK_ROOT = "results/meta_analysis/scrna_pseudobulk"
SINGLE_CELL_ENABLED = bool(config["single_cell"].get("enabled", False))
SINGLE_CELL_DOWNSTREAM_ENABLED = bool(
    config["single_cell"].get("downstream_analysis_enabled", False)
)


def load_active_single_cell_rows(path):
    grouped = defaultdict(list)
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            data_type = row.get("data_type", "").lower()
            if (
                row.get("include") == "true"
                and row.get("review_status") == "confirmed"
                and any(
                    term in data_type
                    for term in ("scrna", "snrna", "single_cell", "single-cell")
                )
            ):
                grouped[row["dataset_id"]].append(row)
    return dict(grouped)


SINGLE_CELL_ROWS = load_active_single_cell_rows(
    config["geo"]["metadata_reviewed_file"]
)
SINGLE_CELL_DATASETS = (
    sorted(SINGLE_CELL_ROWS) if SINGLE_CELL_ENABLED else []
)
SINGLE_CELL_PREPROCESS_TARGETS = expand(
    f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/preprocessing/.complete",
    dataset=SINGLE_CELL_DATASETS,
)
SINGLE_CELL_ANALYSIS_TARGETS = (
    expand(
        f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/.complete",
        dataset=SINGLE_CELL_DATASETS,
    )
    if SINGLE_CELL_DOWNSTREAM_ENABLED
    else []
)


def load_single_cell_plan(path):
    grouped = defaultdict(list)
    if not Path(path).exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("include") == "true":
                grouped[row["analysis_id"]].append(row)
    return dict(grouped)


SINGLE_CELL_PLAN = load_single_cell_plan(config["multi_dataset"]["dataset_plan_file"])
SINGLE_CELL_PSEUDOBULK_ANALYSES = (
    sorted(
        analysis_id
        for analysis_id, rows in SINGLE_CELL_PLAN.items()
        if {row.get("dataset_id") for row in rows}.issubset(set(SINGLE_CELL_DATASETS))
        and {row.get("analysis_strategy") for row in rows}
        <= {"joint_model", "per_dataset_meta", "stratified_validation", "independent_only"}
    )
    if SINGLE_CELL_DOWNSTREAM_ENABLED
    else []
)
SINGLE_CELL_PSEUDOBULK_STRATEGY = {
    analysis_id: next(iter({row["analysis_strategy"] for row in rows}), "invalid")
    for analysis_id, rows in SINGLE_CELL_PLAN.items()
}


def single_cell_pseudobulk_analysis_target(analysis_id):
    strategy = SINGLE_CELL_PSEUDOBULK_STRATEGY[analysis_id]
    if strategy == "joint_model":
        return f"{MERGED_PSEUDOBULK_ROOT}/{analysis_id}/joint_model/.complete"
    if strategy == "per_dataset_meta":
        return f"{META_PSEUDOBULK_ROOT}/{analysis_id}/per_dataset_meta/.complete"
    if strategy == "stratified_validation":
        return f"{META_PSEUDOBULK_ROOT}/{analysis_id}/stratified_validation/.complete"
    if strategy == "independent_only":
        return f"{MERGED_PSEUDOBULK_ROOT}/{analysis_id}/independent_only/.complete"
    raise ValueError(f"Unsupported single-cell pseudobulk strategy: {strategy}")


SINGLE_CELL_PSEUDOBULK_MULTI_TARGETS = [
    single_cell_pseudobulk_analysis_target(analysis_id)
    for analysis_id in SINGLE_CELL_PSEUDOBULK_ANALYSES
]
SINGLE_CELL_TARGETS = (
    SINGLE_CELL_PREPROCESS_TARGETS
    + SINGLE_CELL_ANALYSIS_TARGETS
    + SINGLE_CELL_PSEUDOBULK_MULTI_TARGETS
)


def single_cell_input_paths(wildcards):
    paths = {
        row["matrix_path"]
        for row in SINGLE_CELL_ROWS[wildcards.dataset]
        if row.get("matrix_path") not in {"", "NA", "N/A", "null", "None"}
    }
    return sorted(paths)


rule preprocess_single_cell_dataset:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        entries=single_cell_input_paths,
        config="config/config.yaml",
        manifest=config["geo"]["metadata_reviewed_file"]
    output:
        marker=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/preprocessing/.complete",
        pre_qc=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/objects/pre_qc.h5ad",
        post_qc=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/objects/post_qc.h5ad",
        clustered=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/objects/clustered.h5ad",
        qc=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/qc/cell_qc.tsv",
        thresholds=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/qc/sample_thresholds.tsv",
        sample_summary=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/qc/sample_summary.tsv",
        doublet_status=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/qc/doublet_status.tsv",
        ambient_status=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/qc/ambient_rna_status.tsv",
        markers=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/markers/cluster_markers.tsv",
        composition=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/markers/cluster_sample_composition.tsv",
        author_composition=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/markers/cluster_author_label_composition.tsv",
        suggestions=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/markers/suggested_annotations.tsv",
        qc_plot=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/plots/qc_by_sample.png",
        pca_plot=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/plots/pca_unintegrated.png",
        umap_plot=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/plots/umap.png",
        dotplot=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/plots/marker_dotplot.png",
        provenance=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/provenance/preprocessing.json"
    log:
        "logs/single_cell/{dataset}/preprocessing.log"
    benchmark:
        "benchmarks/single_cell/{dataset}/preprocessing.tsv"
    conda:
        "../envs/python-single-cell.yaml"
    threads: config["resources"]["single_cell"]["threads"]
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    shell:
        """
        python workflow/scripts/preprocess_single_cell_dataset.py \
          --config {input.config:q} --manifest {input.manifest:q} \
          --dataset-id {wildcards.dataset:q} \
          --output-marker {output.marker:q} \
          --output-pre-qc {output.pre_qc:q} \
          --output-post-qc {output.post_qc:q} \
          --output-clustered {output.clustered:q} \
          --output-qc {output.qc:q} \
          --output-thresholds {output.thresholds:q} \
          --output-sample-summary {output.sample_summary:q} \
          --output-doublet-status {output.doublet_status:q} \
          --output-ambient-status {output.ambient_status:q} \
          --output-markers {output.markers:q} \
          --output-composition {output.composition:q} \
          --output-author-composition {output.author_composition:q} \
          --output-suggestions {output.suggestions:q} \
          --output-qc-plot {output.qc_plot:q} \
          --output-pca-plot {output.pca_plot:q} \
          --output-umap-plot {output.umap_plot:q} \
          --output-dotplot {output.dotplot:q} \
          --output-provenance {output.provenance:q} > {log:q} 2>&1
        """


rule prepare_single_cell_pseudobulk:
    input:
        clustered=rules.preprocess_single_cell_dataset.output.clustered,
        config="config/config.yaml",
        ontology=config["single_cell"]["celltype_ontology_file"]
    output:
        counts=f"{PSEUDOBULK_ROOT}/{{dataset}}/pseudobulk/input/raw_counts.tsv",
        metadata=f"{PSEUDOBULK_ROOT}/{{dataset}}/pseudobulk/input/sample_metadata.tsv",
        metrics=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/qc/celltype_metrics.tsv",
        provenance=f"{PSEUDOBULK_ROOT}/{{dataset}}/pseudobulk/provenance/pseudobulk.json"
    log:
        "logs/single_cell/{dataset}/prepare_pseudobulk.log"
    benchmark:
        "benchmarks/single_cell/{dataset}/prepare_pseudobulk.tsv"
    conda:
        "../envs/python-single-cell.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_single_cell_pseudobulk.py \
          --config {input.config:q} --ontology {input.ontology:q} \
          --dataset-id {wildcards.dataset:q} \
          --clustered {input.clustered:q} \
          --output-counts {output.counts:q} \
          --output-metadata {output.metadata:q} \
          --output-metrics {output.metrics:q} \
          --output-provenance {output.provenance:q} > {log:q} 2>&1
        """


rule single_cell_pseudobulk_deseq2:
    input:
        counts=rules.prepare_single_cell_pseudobulk.output.counts,
        metadata=rules.prepare_single_cell_pseudobulk.output.metadata,
        metrics=rules.prepare_single_cell_pseudobulk.output.metrics,
        config="config/config.yaml",
        contrasts="config/contrasts.tsv",
        dataset_plan="config/dataset_plan.tsv"
    output:
        marker=f"{PSEUDOBULK_ROOT}/{{dataset}}/pseudobulk/deseq2/.complete",
        session=f"{PSEUDOBULK_ROOT}/{{dataset}}/pseudobulk/deseq2/session_info.txt"
    log:
        "logs/single_cell/{dataset}/pseudobulk_deseq2.log"
    benchmark:
        "benchmarks/single_cell/{dataset}/pseudobulk_deseq2.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: config["resources"]["single_cell"]["threads"]
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    params:
        output_dir=f"{PSEUDOBULK_ROOT}/{{dataset}}/pseudobulk/deseq2"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_single_cell_pseudobulk_deseq2.R \
          --counts {input.counts:q} --metadata {input.metadata:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --config {input.config:q} --dataset-id {wildcards.dataset:q} \
          --output-dir {params.output_dir:q} > {log:q} 2>&1
        """


def pseudobulk_analysis_dataset_markers(wildcards):
    return [
        f"{PSEUDOBULK_ROOT}/{row['dataset_id']}/pseudobulk/deseq2/.complete"
        for row in SINGLE_CELL_PLAN[wildcards.analysis]
    ]


def pseudobulk_analysis_input_markers(wildcards):
    return [
        f"{PSEUDOBULK_ROOT}/{row['dataset_id']}/pseudobulk/input/raw_counts.tsv"
        for row in SINGLE_CELL_PLAN[wildcards.analysis]
    ]


rule prepare_joint_pseudobulk:
    input:
        datasets=pseudobulk_analysis_input_markers,
        config="config/config.yaml",
        dataset_plan=config["multi_dataset"]["dataset_plan_file"],
        contrasts="config/contrasts.tsv"
    output:
        counts=f"{MERGED_PSEUDOBULK_ROOT}/{{analysis}}/joint_model/input/raw_counts.tsv",
        metadata=f"{MERGED_PSEUDOBULK_ROOT}/{{analysis}}/joint_model/input/sample_metadata.tsv",
        provenance=f"{MERGED_PSEUDOBULK_ROOT}/{{analysis}}/joint_model/input/provenance.json"
    log:
        "logs/single_cell/{analysis}/prepare_joint_pseudobulk.log"
    benchmark:
        "benchmarks/single_cell/{analysis}/prepare_joint_pseudobulk.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_joint_pseudobulk.py \
          --config {input.config:q} \
          --dataset-plan {input.dataset_plan:q} \
          --contrasts {input.contrasts:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-counts {output.counts:q} \
          --output-metadata {output.metadata:q} \
          --output-provenance {output.provenance:q} > {log:q} 2>&1
        """


rule pseudobulk_joint_model:
    input:
        counts=rules.prepare_joint_pseudobulk.output.counts,
        metadata=rules.prepare_joint_pseudobulk.output.metadata,
        config="config/config.yaml",
        dataset_plan=config["multi_dataset"]["dataset_plan_file"],
        contrasts="config/contrasts.tsv"
    output:
        marker=f"{MERGED_PSEUDOBULK_ROOT}/{{analysis}}/joint_model/.complete",
        manifest=f"{MERGED_PSEUDOBULK_ROOT}/{{analysis}}/joint_model/results_manifest.tsv"
    log:
        "logs/single_cell/{analysis}/pseudobulk_joint_model.log"
    benchmark:
        "benchmarks/single_cell/{analysis}/pseudobulk_joint_model.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: config["resources"]["single_cell"]["threads"]
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    params:
        output_dir=f"{MERGED_PSEUDOBULK_ROOT}/{{analysis}}/joint_model"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_single_cell_pseudobulk_deseq2.R \
          --counts {input.counts:q} --metadata {input.metadata:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --config {input.config:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-dir {params.output_dir:q} > {log:q} 2>&1
        """


rule pseudobulk_per_dataset_meta:
    input:
        datasets=pseudobulk_analysis_dataset_markers,
        config="config/config.yaml",
        dataset_plan=config["multi_dataset"]["dataset_plan_file"],
        contrasts="config/contrasts.tsv"
    output:
        marker=f"{META_PSEUDOBULK_ROOT}/{{analysis}}/per_dataset_meta/.complete",
        manifest=f"{META_PSEUDOBULK_ROOT}/{{analysis}}/per_dataset_meta/results_manifest.tsv"
    log:
        "logs/single_cell/{analysis}/pseudobulk_meta.log"
    benchmark:
        "benchmarks/single_cell/{analysis}/pseudobulk_meta.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    params:
        output_dir=f"{META_PSEUDOBULK_ROOT}/{{analysis}}/per_dataset_meta"
    shell:
        """
        python workflow/scripts/run_pseudobulk_meta_analysis.py \
          --config {input.config:q} \
          --dataset-plan {input.dataset_plan:q} \
          --contrasts {input.contrasts:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-dir {params.output_dir:q} \
          --mode meta > {log:q} 2>&1
        """


rule pseudobulk_stratified_validation:
    input:
        datasets=pseudobulk_analysis_dataset_markers,
        config="config/config.yaml",
        dataset_plan=config["multi_dataset"]["dataset_plan_file"],
        contrasts="config/contrasts.tsv"
    output:
        marker=f"{META_PSEUDOBULK_ROOT}/{{analysis}}/stratified_validation/.complete",
        manifest=f"{META_PSEUDOBULK_ROOT}/{{analysis}}/stratified_validation/results_manifest.tsv"
    log:
        "logs/single_cell/{analysis}/pseudobulk_validation.log"
    benchmark:
        "benchmarks/single_cell/{analysis}/pseudobulk_validation.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    params:
        output_dir=f"{META_PSEUDOBULK_ROOT}/{{analysis}}/stratified_validation"
    shell:
        """
        python workflow/scripts/run_pseudobulk_meta_analysis.py \
          --config {input.config:q} \
          --dataset-plan {input.dataset_plan:q} \
          --contrasts {input.contrasts:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-dir {params.output_dir:q} \
          --mode validation > {log:q} 2>&1
        """


rule pseudobulk_independent_only:
    input:
        datasets=pseudobulk_analysis_dataset_markers
    output:
        marker=f"{MERGED_PSEUDOBULK_ROOT}/{{analysis}}/independent_only/.complete"
    log:
        "logs/single_cell/{analysis}/pseudobulk_independent_only.log"
    benchmark:
        "benchmarks/single_cell/{analysis}/pseudobulk_independent_only.tsv"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    run:
        rows = SINGLE_CELL_PLAN[wildcards.analysis]
        if {row["analysis_strategy"] for row in rows} != {"independent_only"}:
            raise ValueError("dataset_plan.tsv does not authorize independent_only")
        Path(output.marker).parent.mkdir(parents=True, exist_ok=True)
        Path(output.marker).write_text(
            json.dumps(
                {
                    "analysis_id": wildcards.analysis,
                    "strategy": "independent_only",
                    "joint_or_meta_analysis_run": False,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        Path(log[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(log[0]).write_text("Pseudobulk datasets retained independently.\n", encoding="utf-8")


rule single_cell_proportion:
    input:
        metadata=rules.prepare_single_cell_pseudobulk.output.metadata,
        config="config/config.yaml",
        contrasts="config/contrasts.tsv",
        dataset_plan="config/dataset_plan.tsv"
    output:
        marker=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/cell_proportion/.complete",
        results=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/cell_proportion/results.tsv",
        proportions=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/cell_proportion/subject_proportions.tsv"
    log:
        "logs/single_cell/{dataset}/cell_proportion.log"
    benchmark:
        "benchmarks/single_cell/{dataset}/cell_proportion.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["single_cell"]["mem_mb"],
        runtime_min=config["resources"]["single_cell"]["runtime_min"],
        disk_mb=config["resources"]["single_cell"]["disk_mb"]
    shell:
        """
        python workflow/scripts/run_cell_proportion.py \
          --config {input.config:q} --metadata {input.metadata:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --dataset-id {wildcards.dataset:q} \
          --output-results {output.results:q} \
          --output-proportions {output.proportions:q} \
          --output-marker {output.marker:q} > {log:q} 2>&1
        """


rule single_cell_dataset_analysis:
    input:
        preprocessing=rules.preprocess_single_cell_dataset.output.marker,
        pseudobulk=rules.single_cell_pseudobulk_deseq2.output.marker,
        proportions=rules.single_cell_proportion.output.marker
    output:
        marker=f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/.complete"
    log:
        "logs/single_cell/{dataset}/complete.log"
    benchmark:
        "benchmarks/single_cell/{dataset}/complete.tsv"
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
                    "replicate_unit": "subject_id",
                    "cell_replication_used": False,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        Path(log[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(log[0]).write_text(
            f"Completed single-cell analysis for {wildcards.dataset}.\n",
            encoding="utf-8",
        )
