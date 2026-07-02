REPORT_ENABLED = bool(config["reporting"].get("enabled", False))
REPORT_ROOT = config["reporting"]["output_dir"]
REPORT_TARGETS = (
    [f"{REPORT_ROOT}/.complete"] if REPORT_ENABLED else []
)


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


rule build_audit_trail:
    input:
        config="config/config.yaml",
        manifest="metadata/reviewed/sample_manifest.tsv",
        contrasts="config/contrasts.tsv",
        dataset_plan="config/dataset_plan.tsv",
        ontology="config/celltype_ontology.tsv",
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
        manifest="metadata/reviewed/sample_manifest.tsv",
        contrasts="config/contrasts.tsv",
        dataset_plan="config/dataset_plan.tsv",
        warnings=rules.build_audit_trail.output.warnings,
        exclusions=rules.build_audit_trail.output.exclusions,
        audit=rules.build_audit_trail.output.audit,
        software=rules.collect_software_versions.output.versions,
        references=rules.collect_reference_metadata.output.versions,
        checksums=rules.collect_provenance.output.checksums,
        validation_report=rules.generate_validation_report.output.report
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
        parameters=rules.snapshot_reporting_parameters.output.snapshot
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
                      {input.parameters:q} {input.audit:q} \
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
