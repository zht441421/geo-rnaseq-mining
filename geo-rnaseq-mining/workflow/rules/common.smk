from pathlib import Path

AUTHORITY_SAMPLE_MANIFEST = config["geo"]["metadata_reviewed_file"]
AUTHORITY_CONTRASTS = "metadata/reviewed/contrasts.tsv"
AUTHORITY_DATASET_PLAN = config["multi_dataset"]["dataset_plan_file"]
AUTHORITY_CELLTYPE_ONTOLOGY = config["single_cell"]["celltype_ontology_file"]

MANUAL_AUTHORITY_FILES = [
    AUTHORITY_SAMPLE_MANIFEST,
    AUTHORITY_CONTRASTS,
    AUTHORITY_DATASET_PLAN,
    AUTHORITY_CELLTYPE_ONTOLOGY,
]


def existing_authority_files(wildcards):
    return [path for path in MANUAL_AUTHORITY_FILES if Path(path).exists()]


rule authority_files:
    input:
        existing_authority_files
    output:
        touch("resources/.authority_files_present")
    log:
        "logs/validation/authority_files.log"
    benchmark:
        "benchmarks/validation/authority_files.tsv"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    run:
        Path(log[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(log[0]).write_text(
            "Reviewed authority files are present; strict validation follows.\n",
            encoding="utf-8",
        )


rule validate_authority_config:
    input:
        marker=rules.authority_files.output,
        sample_schema="workflow/schemas/sample_manifest.schema.json",
        contrasts_schema="workflow/schemas/contrasts.schema.json",
        dataset_plan_schema="workflow/schemas/dataset_plan.schema.json",
        celltype_schema="workflow/schemas/celltype_ontology.schema.json"
    output:
        report="resources/validation/authority_config.validation.json"
    log:
        "logs/validation/validate_authority_config.log"
    benchmark:
        "benchmarks/validation/validate_authority_config.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        sample_manifest=AUTHORITY_SAMPLE_MANIFEST,
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN,
        celltype_ontology=AUTHORITY_CELLTYPE_ONTOLOGY
    shell:
        """
        python workflow/scripts/authority_config.py \
          --sample-manifest {params.sample_manifest:q} \
          --contrasts {params.contrasts:q} \
          --dataset-plan {params.dataset_plan:q} \
          --celltype-ontology {params.celltype_ontology:q} \
          --schema-dir workflow/schemas \
          --report {output.report:q} \
          --report-only \
          > {log:q} 2>&1
        """
