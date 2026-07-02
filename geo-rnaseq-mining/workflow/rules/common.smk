MANUAL_AUTHORITY_FILES = [
    "metadata/reviewed/sample_manifest.tsv",
    "config/contrasts.tsv",
    "config/dataset_plan.tsv",
    "config/celltype_ontology.tsv",
]


rule authority_files:
    input:
        MANUAL_AUTHORITY_FILES
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
    shell:
        "echo 'Reviewed authority files are present; strict validation follows.' > {log}"


rule validate_authority_config:
    input:
        marker=rules.authority_files.output,
        sample_manifest="metadata/reviewed/sample_manifest.tsv",
        contrasts="config/contrasts.tsv",
        dataset_plan="config/dataset_plan.tsv",
        celltype_ontology="config/celltype_ontology.tsv",
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
    shell:
        """
        python workflow/scripts/authority_config.py \
          --sample-manifest {input.sample_manifest:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --celltype-ontology {input.celltype_ontology:q} \
          --schema-dir workflow/schemas \
          --report {output.report:q} \
          --report-only \
          > {log:q} 2>&1
        """
