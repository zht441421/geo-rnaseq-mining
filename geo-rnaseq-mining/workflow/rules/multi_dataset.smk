import csv
import json
from collections import defaultdict
from pathlib import Path


MULTI_ENABLED = bool(config["multi_dataset"].get("enabled", False))
MULTI_PLAN_FILE = config["multi_dataset"]["dataset_plan_file"]
MULTI_COMPATIBILITY = "results/compatibility/dataset_compatibility.tsv"
MERGED_BULK_ROOT = "results/merged_analysis/bulk"
META_BULK_ROOT = "results/meta_analysis/bulk"
CONSENSUS_BULK_ROOT = "results/consensus/bulk"


def load_multi_plan(path):
    grouped = defaultdict(list)
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("include") == "true":
                grouped[row["analysis_id"]].append(row)
    return dict(grouped)


MULTI_PLAN = load_multi_plan(MULTI_PLAN_FILE)
MULTI_ANALYSES = sorted(MULTI_PLAN) if MULTI_ENABLED else []
MULTI_DATASETS = sorted(
    {
        row["dataset_id"]
        for analysis_id in MULTI_ANALYSES
        for row in MULTI_PLAN[analysis_id]
    }
)
MULTI_STRATEGY = {
    analysis_id: next(
        iter({row["analysis_strategy"] for row in rows}),
        "invalid",
    )
    for analysis_id, rows in MULTI_PLAN.items()
}


def analysis_dataset_markers(wildcards):
    return [
        f"results/per_dataset/{row['dataset_id']}/bulk/.complete"
        for row in MULTI_PLAN[wildcards.analysis]
    ]


def analysis_deseq_markers(wildcards):
    return [
        f"results/per_dataset/{row['dataset_id']}/bulk/deseq2/.complete"
        for row in MULTI_PLAN[wildcards.analysis]
    ]


def strategy_target(analysis_id):
    strategy = MULTI_STRATEGY[analysis_id]
    if strategy == "joint_model":
        return f"{MERGED_BULK_ROOT}/{analysis_id}/joint_model/.complete"
    if strategy == "per_dataset_meta":
        return f"{META_BULK_ROOT}/{analysis_id}/per_dataset_meta/.complete"
    if strategy == "stratified_validation":
        return f"{META_BULK_ROOT}/{analysis_id}/stratified_validation/.complete"
    if strategy == "independent_only":
        return f"{MERGED_BULK_ROOT}/{analysis_id}/independent_only/.complete"
    raise ValueError(
        f"analysis_id {analysis_id} must have one valid strategy in dataset_plan.tsv"
    )


MULTI_DATASET_TARGETS = (
    [MULTI_COMPATIBILITY]
    + [strategy_target(analysis_id) for analysis_id in MULTI_ANALYSES]
    if MULTI_ANALYSES
    else []
)


rule assess_dataset_compatibility:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        datasets=expand(
            "results/per_dataset/{dataset}/bulk/.complete",
            dataset=MULTI_DATASETS,
        ),
        config="config/config.yaml",
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        dataset_plan=MULTI_PLAN_FILE,
        contrasts=AUTHORITY_CONTRASTS,
        geo_samples=rules.fetch_geo_metadata.output.samples,
        sra_runinfo=rules.fetch_sra_runinfo.output.runinfo
    output:
        compatibility=MULTI_COMPATIBILITY
    log:
        "logs/multi_dataset/compatibility.log"
    benchmark:
        "benchmarks/multi_dataset/compatibility.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/assess_dataset_compatibility.py \
          --config {input.config:q} --manifest {input.manifest:q} \
          --dataset-plan {input.dataset_plan:q} \
          --contrasts {input.contrasts:q} \
          --geo-samples {input.geo_samples:q} \
          --sra-runinfo {input.sra_runinfo:q} \
          --output {output.compatibility:q} > {log:q} 2>&1
        """


rule prepare_joint_bulk:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        datasets=analysis_dataset_markers,
        compatibility=rules.assess_dataset_compatibility.output.compatibility,
        config="config/config.yaml",
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        dataset_plan=MULTI_PLAN_FILE,
        contrasts=AUTHORITY_CONTRASTS
    output:
        counts=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/input/raw_counts.tsv",
        metadata=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/input/sample_metadata.tsv",
        validation=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/input/preflight_validation.tsv",
        provenance=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/input/provenance.json"
    log:
        "logs/multi_dataset/{analysis}/prepare_joint.log"
    benchmark:
        "benchmarks/multi_dataset/{analysis}/prepare_joint.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_joint_bulk.py \
          --config {input.config:q} --manifest {input.manifest:q} \
          --dataset-plan {input.dataset_plan:q} \
          --contrasts {input.contrasts:q} \
          --compatibility {input.compatibility:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-counts {output.counts:q} \
          --output-metadata {output.metadata:q} \
          --output-validation {output.validation:q} \
          --output-provenance {output.provenance:q} > {log:q} 2>&1
        """


rule bulk_joint_model:
    input:
        counts=rules.prepare_joint_bulk.output.counts,
        metadata=rules.prepare_joint_bulk.output.metadata,
        validation=rules.prepare_joint_bulk.output.validation,
        config="config/config.yaml",
        dataset_plan=MULTI_PLAN_FILE,
        contrasts=AUTHORITY_CONTRASTS
    output:
        marker=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/.complete",
        manifest=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/results_manifest.tsv",
        effects=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/effect_direction_summary.tsv",
        session=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model/session_info.txt"
    log:
        "logs/multi_dataset/{analysis}/joint_model.log"
    benchmark:
        "benchmarks/multi_dataset/{analysis}/joint_model.tsv"
    conda:
        "../envs/r-bulk-analysis.yaml"
    threads: config["resources"]["bulk"]["threads"]
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        output_dir=f"{MERGED_BULK_ROOT}/{{analysis}}/joint_model"
    shell:
        """
        python workflow/scripts/run_rscript.py workflow/scripts/run_bulk_joint_model.R \
          --counts {input.counts:q} --metadata {input.metadata:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --config {input.config:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-dir {params.output_dir:q} > {log:q} 2>&1
        """


rule bulk_per_dataset_meta:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        datasets=analysis_deseq_markers,
        compatibility=rules.assess_dataset_compatibility.output.compatibility,
        config="config/config.yaml",
        dataset_plan=MULTI_PLAN_FILE,
        contrasts=AUTHORITY_CONTRASTS
    output:
        marker=f"{META_BULK_ROOT}/{{analysis}}/per_dataset_meta/.complete",
        manifest=f"{META_BULK_ROOT}/{{analysis}}/per_dataset_meta/results_manifest.tsv",
        status=f"{META_BULK_ROOT}/{{analysis}}/per_dataset_meta/meta_analysis_status.tsv",
        consensus=f"{CONSENSUS_BULK_ROOT}/{{analysis}}/per_dataset_meta/.complete"
    log:
        "logs/multi_dataset/{analysis}/meta.log"
    benchmark:
        "benchmarks/multi_dataset/{analysis}/meta.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        output_dir=f"{META_BULK_ROOT}/{{analysis}}/per_dataset_meta",
        consensus_dir=f"{CONSENSUS_BULK_ROOT}/{{analysis}}/per_dataset_meta"
    shell:
        """
        python workflow/scripts/run_bulk_meta_analysis.py \
          --config {input.config:q} \
          --dataset-plan {input.dataset_plan:q} \
          --contrasts {input.contrasts:q} \
          --compatibility {input.compatibility:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-dir {params.output_dir:q} \
          --consensus-dir {params.consensus_dir:q} > {log:q} 2>&1
        """


rule bulk_stratified_validation:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        datasets=analysis_deseq_markers,
        compatibility=rules.assess_dataset_compatibility.output.compatibility,
        config="config/config.yaml",
        dataset_plan=MULTI_PLAN_FILE,
        contrasts=AUTHORITY_CONTRASTS
    output:
        marker=f"{META_BULK_ROOT}/{{analysis}}/stratified_validation/.complete",
        manifest=f"{META_BULK_ROOT}/{{analysis}}/stratified_validation/results_manifest.tsv",
        consensus=f"{CONSENSUS_BULK_ROOT}/{{analysis}}/stratified_validation/.complete"
    log:
        "logs/multi_dataset/{analysis}/stratified_validation.log"
    benchmark:
        "benchmarks/multi_dataset/{analysis}/stratified_validation.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["bulk"]["mem_mb"],
        runtime_min=config["resources"]["bulk"]["runtime_min"],
        disk_mb=config["resources"]["bulk"]["disk_mb"]
    params:
        output_dir=f"{META_BULK_ROOT}/{{analysis}}/stratified_validation",
        consensus_dir=f"{CONSENSUS_BULK_ROOT}/{{analysis}}/stratified_validation"
    shell:
        """
        python workflow/scripts/run_bulk_stratified_validation.py \
          --config {input.config:q} \
          --dataset-plan {input.dataset_plan:q} \
          --contrasts {input.contrasts:q} \
          --compatibility {input.compatibility:q} \
          --analysis-id {wildcards.analysis:q} \
          --output-dir {params.output_dir:q} \
          --consensus-dir {params.consensus_dir:q} > {log:q} 2>&1
        """


rule bulk_independent_only:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        datasets=analysis_dataset_markers,
        compatibility=rules.assess_dataset_compatibility.output.compatibility,
        dataset_plan=MULTI_PLAN_FILE
    output:
        marker=f"{MERGED_BULK_ROOT}/{{analysis}}/independent_only/.complete"
    log:
        "logs/multi_dataset/{analysis}/independent_only.log"
    benchmark:
        "benchmarks/multi_dataset/{analysis}/independent_only.tsv"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    run:
        rows = MULTI_PLAN[wildcards.analysis]
        if {row["analysis_strategy"] for row in rows} != {"independent_only"}:
            raise ValueError("dataset_plan.tsv does not authorize independent_only")
        Path(output.marker).parent.mkdir(parents=True, exist_ok=True)
        Path(output.marker).write_text(
            json.dumps(
                {
                    "analysis_id": wildcards.analysis,
                    "strategy": "independent_only",
                    "dataset_ids": [row["dataset_id"] for row in rows],
                    "joint_or_meta_analysis_run": False,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        Path(log[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(log[0]).write_text(
            "Datasets retained as independent analyses by reviewed plan.\n",
            encoding="utf-8",
        )
