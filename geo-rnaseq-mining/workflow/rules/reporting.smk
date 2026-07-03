REPORT_ENABLED = bool(config["reporting"].get("enabled", False))
REPORT_ROOT = config["reporting"]["output_dir"]
REPORT_TARGETS = (
    [f"{REPORT_ROOT}/.complete"] if REPORT_ENABLED else []
)


def optional_report_args(flag, paths):
    if isinstance(paths, str):
        paths = [paths]
    paths = [str(path) for path in paths if path]
    if not paths:
        return ""
    return f"{flag} " + " ".join(f'"{path}"' for path in paths)


rule collect_provenance:
    input:
        config="config/config.yaml"
    output:
        marker=f"{REPORT_ROOT}/provenance/.complete",
        checksums=f"{REPORT_ROOT}/file_checksums.tsv"
    log:
        "logs/reporting/collect_provenance.log"
    benchmark:
        "benchmarks/reporting/collect_provenance.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py collect_provenance \
          --roots results logs benchmarks config metadata workflow \
          --output {output.checksums:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule collect_software_versions:
    input:
        config="config/config.yaml"
    output:
        marker=f"{REPORT_ROOT}/software/.complete",
        versions=f"{REPORT_ROOT}/software_versions.tsv"
    log:
        "logs/reporting/collect_software_versions.log"
    benchmark:
        "benchmarks/reporting/collect_software_versions.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py collect_software_versions \
          --output {output.versions:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule collect_reference_metadata:
    input:
        config="config/config.yaml"
    output:
        marker=f"{REPORT_ROOT}/references/.complete",
        versions=f"{REPORT_ROOT}/reference_versions.tsv"
    log:
        "logs/reporting/collect_reference_metadata.log"
    benchmark:
        "benchmarks/reporting/collect_reference_metadata.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py collect_reference_metadata \
          --config {input.config:q} \
          --output {output.versions:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule snapshot_reporting_parameters:
    input:
        config="config/config.yaml"
    output:
        marker=f"{REPORT_ROOT}/parameters/.complete",
        snapshot=f"{REPORT_ROOT}/parameter_snapshot.yaml"
    log:
        "logs/reporting/parameter_snapshot.log"
    benchmark:
        "benchmarks/reporting/parameter_snapshot.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py snapshot_parameters \
          --config {input.config:q} \
          --output {output.snapshot:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule collect_test_status:
    input:
        config="config/config.yaml"
    output:
        marker=f"{REPORT_ROOT}/test_status.complete",
        status=f"{REPORT_ROOT}/test_status.tsv"
    log:
        "logs/reporting/test_status.log"
    benchmark:
        "benchmarks/reporting/test_status.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py write_test_status \
          --output {output.status:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule build_audit_trail:
    input:
        config="config/config.yaml",
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN,
        ontology=AUTHORITY_CELLTYPE_ONTOLOGY,
        manifest_issues=rules.validate_manifest.output.errors,
        manifest_warnings=rules.validate_manifest.output.warnings,
        contrast_issues=rules.validate_contrasts.output.validation,
        plan_issues=rules.validate_dataset_plan.output.validation,
        celltype_issues=rules.validate_celltype_ontology.output.validation,
        design_issues=rules.validate_analysis_design.output.validation
    output:
        marker=f"{REPORT_ROOT}/audit/.complete",
        audit=f"{REPORT_ROOT}/audit_trail.tsv",
        exclusions=f"{REPORT_ROOT}/exclusions.tsv",
        warnings=f"{REPORT_ROOT}/warnings.tsv"
    log:
        "logs/reporting/build_audit_trail.log"
    benchmark:
        "benchmarks/reporting/build_audit_trail.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py build_audit_trail \
          --authority-files {input.manifest:q} {input.contrasts:q} \
                            {input.dataset_plan:q} {input.ontology:q} \
          --issue-files {input.manifest_issues:q} {input.manifest_warnings:q} \
                        {input.contrast_issues:q} {input.plan_issues:q} \
                        {input.celltype_issues:q} {input.design_issues:q} \
          --audit {output.audit:q} \
          --exclusions {output.exclusions:q} \
          --warnings {output.warnings:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule render_analysis_report:
    input:
        config="config/config.yaml",
        manifest=AUTHORITY_SAMPLE_MANIFEST,
        contrasts=AUTHORITY_CONTRASTS,
        dataset_plan=AUTHORITY_DATASET_PLAN,
        warnings=rules.build_audit_trail.output.warnings,
        exclusions=rules.build_audit_trail.output.exclusions,
        audit=rules.build_audit_trail.output.audit,
        software=rules.collect_software_versions.output.versions,
        references=rules.collect_reference_metadata.output.versions,
        checksums=rules.collect_provenance.output.checksums,
        test_status=rules.collect_test_status.output.status,
        validation_report=rules.generate_validation_report.output.report,
        candidate_scores=(
            rules.bulk_scrna_integration.output.candidate_scores
            if BULK_SCRNA_INTEGRATION_ENABLED
            else []
        ),
        suggested_annotations=(
            expand(
                f"{SINGLE_CELL_ROOT}/{{dataset}}/single_cell/markers/suggested_annotations.tsv",
                dataset=SINGLE_CELL_DATASETS,
            )
            if SINGLE_CELL_ENABLED
            else []
        )
    output:
        marker=f"{REPORT_ROOT}/analysis_report.complete",
        html=f"{REPORT_ROOT}/analysis_report.html",
        validation=f"{REPORT_ROOT}/validation_report.html"
    log:
        "logs/reporting/render_analysis_report.log"
    benchmark:
        "benchmarks/reporting/render_analysis_report.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        candidate_scores=lambda wildcards, input: optional_report_args(
            "--candidate-scores",
            input.candidate_scores,
        ),
        suggested_annotations=lambda wildcards, input: optional_report_args(
            "--suggested-annotations",
            input.suggested_annotations,
        )
    shell:
        """
        python workflow/scripts/final_reporting.py render_analysis_report \
          --config {input.config:q} \
          --manifest {input.manifest:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --warnings {input.warnings:q} \
          --exclusions {input.exclusions:q} \
          --software {input.software:q} \
          --references {input.references:q} \
          --checksums {input.checksums:q} \
          --audit {input.audit:q} \
          --test-status {input.test_status:q} \
          {params.candidate_scores} \
          {params.suggested_annotations} \
          --validation-report {input.validation_report:q} \
          --validation-output {output.validation:q} \
          --output {output.html:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule render_methods_report:
    input:
        config="config/config.yaml",
        software=rules.collect_software_versions.output.versions,
        references=rules.collect_reference_metadata.output.versions,
        parameters=rules.snapshot_reporting_parameters.output.snapshot,
        test_status=rules.collect_test_status.output.status
    output:
        marker=f"{REPORT_ROOT}/methods.complete",
        methods=f"{REPORT_ROOT}/methods.md"
    log:
        "logs/reporting/render_methods_report.log"
    benchmark:
        "benchmarks/reporting/render_methods_report.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py render_methods_report \
          --config {input.config:q} \
          --software {input.software:q} \
          --references {input.references:q} \
          --output {output.methods:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule build_reproducibility_manifest:
    input:
        analysis=rules.render_analysis_report.output.html,
        methods=rules.render_methods_report.output.methods,
        software=rules.collect_software_versions.output.versions,
        references=rules.collect_reference_metadata.output.versions,
        checksums=rules.collect_provenance.output.checksums,
        parameters=rules.snapshot_reporting_parameters.output.snapshot,
        test_status=rules.collect_test_status.output.status,
        audit=rules.build_audit_trail.output.audit,
        exclusions=rules.build_audit_trail.output.exclusions,
        warnings=rules.build_audit_trail.output.warnings
    output:
        marker=f"{REPORT_ROOT}/reproducibility.complete",
        manifest=f"{REPORT_ROOT}/reproducibility_manifest.tsv"
    log:
        "logs/reporting/reproducibility_manifest.log"
    benchmark:
        "benchmarks/reporting/reproducibility_manifest.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py reproducibility_manifest \
          --artifacts {input.analysis:q} {input.methods:q} {input.software:q} \
                      {input.references:q} {input.checksums:q} \
                      {input.parameters:q} {input.test_status:q} \
                      {input.audit:q} \
                      {input.exclusions:q} {input.warnings:q} \
          --output {output.manifest:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """


rule package_results:
    input:
        reproducibility=rules.build_reproducibility_manifest.output.manifest,
        analysis=rules.render_analysis_report.output.html,
        methods=rules.render_methods_report.output.methods
    output:
        marker=f"{REPORT_ROOT}/.complete",
        package=f"{REPORT_ROOT}/result_package.tar.gz",
        manifest=f"{REPORT_ROOT}/result_package_manifest.tsv"
    log:
        "logs/reporting/package_results.log"
    benchmark:
        "benchmarks/reporting/package_results.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/final_reporting.py package_results \
          --roots config metadata workflow results logs benchmarks \
          --output {output.package:q} \
          --manifest {output.manifest:q} \
          --marker {output.marker:q} > {log:q} 2>&1
        """
