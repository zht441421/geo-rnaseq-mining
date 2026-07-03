COMPATIBILITY_DIR = "results/compatibility"
VALIDATION_STATUS = "resources/validation/preanalysis_status.json"
CELLTYPE_METRICS_FILE = config["validation"].get("celltype_metrics_file")
CELLTYPE_METRICS_INPUT = [CELLTYPE_METRICS_FILE] if CELLTYPE_METRICS_FILE else []
CELLTYPE_METRICS_ARG = (
    f'--celltype-metrics "{CELLTYPE_METRICS_FILE}"'
    if CELLTYPE_METRICS_FILE
    else ""
)


rule validate_manifest:
    input:
        authority=rules.validate_authority_config.output.report
    output:
        validated=f"{COMPATIBILITY_DIR}/validated_manifest.tsv",
        errors=f"{COMPATIBILITY_DIR}/manifest_errors.tsv",
        warnings=f"{COMPATIBILITY_DIR}/manifest_warnings.tsv",
        identities=f"{COMPATIBILITY_DIR}/sample_identity_conflicts.tsv"
    log:
        "logs/validation/validate_manifest.log"
    benchmark:
        "benchmarks/validation/validate_manifest.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        manifest=AUTHORITY_SAMPLE_MANIFEST
    shell:
        """
        python workflow/scripts/validate_manifest.py \
          --manifest {params.manifest:q} \
          --project-root . \
          --validated-manifest {output.validated:q} \
          --errors {output.errors:q} \
          --warnings {output.warnings:q} \
          --identity-conflicts {output.identities:q} \
          > {log:q} 2>&1
        """


rule validate_contrasts:
    input:
        authority=rules.validate_authority_config.output.report
    output:
        validation=f"{COMPATIBILITY_DIR}/contrast_validation.tsv"
    log:
        "logs/validation/validate_contrasts.log"
    benchmark:
        "benchmarks/validation/validate_contrasts.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN
    shell:
        """
        python workflow/scripts/validate_contrasts.py \
          --manifest {params.manifest:q} \
          --contrasts {params.contrasts:q} \
          --dataset-plan {params.dataset_plan:q} \
          --output {output.validation:q} \
          > {log:q} 2>&1
        """


rule validate_dataset_plan:
    input:
        authority=rules.validate_authority_config.output.report,
        config="config/config.yaml"
    output:
        validation=f"{COMPATIBILITY_DIR}/dataset_plan_validation.tsv"
    log:
        "logs/validation/validate_dataset_plan.log"
    benchmark:
        "benchmarks/validation/validate_dataset_plan.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN
    shell:
        """
        python workflow/scripts/validate_dataset_plan.py \
          --config {input.config:q} \
          --manifest {params.manifest:q} \
          --contrasts {params.contrasts:q} \
          --dataset-plan {params.dataset_plan:q} \
          --output {output.validation:q} \
          > {log:q} 2>&1
        """


rule validate_celltype_ontology:
    input:
        authority=rules.validate_authority_config.output.report,
        config="config/config.yaml",
        metrics=CELLTYPE_METRICS_INPUT
    output:
        validation=f"{COMPATIBILITY_DIR}/celltype_ontology_validation.tsv"
    log:
        "logs/validation/validate_celltype_ontology.log"
    benchmark:
        "benchmarks/validation/validate_celltype_ontology.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        metrics_arg=CELLTYPE_METRICS_ARG,
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN,
        ontology=AUTHORITY_CELLTYPE_ONTOLOGY
    shell:
        """
        python workflow/scripts/validate_celltype_ontology.py \
          --config {input.config:q} \
          --manifest {params.manifest:q} \
          --contrasts {params.contrasts:q} \
          --dataset-plan {params.dataset_plan:q} \
          --ontology {params.ontology:q} \
          {params.metrics_arg} \
          --output {output.validation:q} \
          > {log:q} 2>&1
        """


rule validate_analysis_design:
    input:
        authority=rules.validate_authority_config.output.report,
        config="config/config.yaml"
    output:
        validation=f"{COMPATIBILITY_DIR}/design_matrix_validation.tsv",
        crosstab=f"{COMPATIBILITY_DIR}/dataset_group_crosstab.tsv"
    log:
        "logs/validation/validate_analysis_design.log"
    benchmark:
        "benchmarks/validation/validate_analysis_design.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN
    shell:
        """
        python workflow/scripts/validate_analysis_design.py \
          --config {input.config:q} \
          --manifest {params.manifest:q} \
          --contrasts {params.contrasts:q} \
          --dataset-plan {params.dataset_plan:q} \
          --design-validation {output.validation:q} \
          --crosstab {output.crosstab:q} \
          > {log:q} 2>&1
        """


rule generate_validation_report:
    input:
        authority=rules.validate_authority_config.output.report,
        validated=rules.validate_manifest.output.validated,
        manifest_errors=rules.validate_manifest.output.errors,
        manifest_warnings=rules.validate_manifest.output.warnings,
        identities=rules.validate_manifest.output.identities,
        contrasts=rules.validate_contrasts.output.validation,
        dataset_plan_validation=rules.validate_dataset_plan.output.validation,
        celltype=rules.validate_celltype_ontology.output.validation,
        design=rules.validate_analysis_design.output.validation,
        crosstab=rules.validate_analysis_design.output.crosstab
    output:
        report=f"{COMPATIBILITY_DIR}/validation_report.html",
        status=VALIDATION_STATUS
    log:
        "logs/validation/generate_validation_report.log"
    benchmark:
        "benchmarks/validation/generate_validation_report.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        dataset_plan=AUTHORITY_DATASET_PLAN
    shell:
        """
        python workflow/scripts/generate_preanalysis_validation_report.py \
          --authority-report {input.authority:q} \
          --validated-manifest {input.validated:q} \
          --dataset-plan {params.dataset_plan:q} \
          --crosstab {input.crosstab:q} \
          --issue-files {input.manifest_errors:q} {input.manifest_warnings:q} \
                        {input.identities:q} {input.contrasts:q} \
                        {input.dataset_plan_validation:q} {input.celltype:q} \
                        {input.design:q} \
          --report {output.report:q} \
          --status {output.status:q} \
          > {log:q} 2>&1
        """


rule enforce_validation_gate:
    input:
        report=rules.generate_validation_report.output.report,
        status=rules.generate_validation_report.output.status
    output:
        marker=touch("resources/validation/.preanalysis_validation_passed")
    log:
        "logs/validation/enforce_validation_gate.log"
    benchmark:
        "benchmarks/validation/enforce_validation_gate.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/enforce_validation_gate.py \
          --status {input.status:q} \
          --marker {output.marker:q} \
          > {log:q} 2>&1
        """
