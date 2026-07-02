MVP_CONFIG = config.get("mvp", {})
MVP_ENABLED = bool(MVP_CONFIG.get("enabled", False))
MVP_DATASET = MVP_CONFIG.get("dataset_id", "GSE_MVP")
MVP_CONTRAST = MVP_CONFIG.get("contrast_id", "case_vs_control")

MVP_TARGETS = []
if MVP_ENABLED:
    MVP_TARGETS = [
        "results/compatibility/validated_manifest.tsv",
        "results/compatibility/data_inventory.tsv",
        f"results/per_dataset/{MVP_DATASET}/bulk/counts_validated.tsv",
        f"results/per_dataset/{MVP_DATASET}/bulk/deseq2_environment_error_{MVP_CONTRAST}.tsv",
        f"results/per_dataset/{MVP_DATASET}/single_cell/processed.h5ad",
        f"results/per_dataset/{MVP_DATASET}/single_cell/cell_qc.tsv",
        f"results/per_dataset/{MVP_DATASET}/pseudobulk/pseudobulk_sample_metadata.tsv",
        f"results/per_dataset/{MVP_DATASET}/pseudobulk/pseudobulk_counts_Tcell.tsv",
        f"results/meta_analysis/bulk/meta_results_{MVP_CONTRAST}.tsv",
        "results/integration/gene_celltype_mapping.tsv",
        "results/integration/bulk_scrna_concordance.tsv",
        "results/integration/candidate_gene_scores.tsv",
        "results/integration/unmapped_genes.tsv",
        "results/provenance/result_file_provenance.tsv",
        "results/reports/analysis_report.html",
        "results/reports/methods.md",
        "results/mvp/.complete",
    ]


rule mvp_pipeline:
    input:
        config=lambda wildcards: MVP_CONFIG["config_file"],
        manifest=lambda wildcards: MVP_CONFIG["manifest"],
        contrasts=lambda wildcards: MVP_CONFIG["contrasts"],
        dataset_plan=lambda wildcards: MVP_CONFIG["dataset_plan"],
        ontology=lambda wildcards: MVP_CONFIG["celltype_ontology"],
        bulk_counts=lambda wildcards: MVP_CONFIG["bulk_counts"],
        single_cell_counts=lambda wildcards: MVP_CONFIG["single_cell_counts"]
    output:
        validated="results/compatibility/validated_manifest.tsv",
        manifest_errors="results/compatibility/manifest_errors.tsv",
        manifest_warnings="results/compatibility/manifest_warnings.tsv",
        contrast_validation="results/compatibility/contrast_validation.tsv",
        dataset_plan_validation="results/compatibility/dataset_plan_validation.tsv",
        design_validation="results/compatibility/design_matrix_validation.tsv",
        validation_report="results/compatibility/validation_report.html",
        inventory="results/compatibility/data_inventory.tsv",
        bulk_counts=f"results/per_dataset/{MVP_DATASET}/bulk/counts_validated.tsv",
        bulk_qc=f"results/per_dataset/{MVP_DATASET}/bulk/sample_qc.tsv",
        normalized=f"results/per_dataset/{MVP_DATASET}/bulk/normalized_counts.tsv",
        pca=f"results/per_dataset/{MVP_DATASET}/bulk/pca_coordinates.tsv",
        deseq2_error=f"results/per_dataset/{MVP_DATASET}/bulk/deseq2_environment_error_{MVP_CONTRAST}.tsv",
        deseq2_session=f"results/per_dataset/{MVP_DATASET}/bulk/deseq2_session_info.txt",
        bulk_log=f"results/per_dataset/{MVP_DATASET}/bulk/bulk_analysis.log",
        processed=f"results/per_dataset/{MVP_DATASET}/single_cell/processed.h5ad",
        cell_qc=f"results/per_dataset/{MVP_DATASET}/single_cell/cell_qc.tsv",
        sample_cell_counts=f"results/per_dataset/{MVP_DATASET}/single_cell/sample_cell_counts.tsv",
        pseudobulk_counts=f"results/per_dataset/{MVP_DATASET}/pseudobulk/pseudobulk_counts_Tcell.tsv",
        pseudobulk_metadata=f"results/per_dataset/{MVP_DATASET}/pseudobulk/pseudobulk_sample_metadata.tsv",
        pseudobulk_eligibility=f"results/per_dataset/{MVP_DATASET}/pseudobulk/pseudobulk_eligibility.tsv",
        skipped_celltypes=f"results/per_dataset/{MVP_DATASET}/pseudobulk/skipped_celltypes.tsv",
        pseudobulk_log=f"results/per_dataset/{MVP_DATASET}/pseudobulk/pseudobulk_analysis.log",
        meta=f"results/meta_analysis/bulk/meta_results_{MVP_CONTRAST}.tsv",
        mapping="results/integration/gene_celltype_mapping.tsv",
        concordance="results/integration/bulk_scrna_concordance.tsv",
        scores="results/integration/candidate_gene_scores.tsv",
        unmapped="results/integration/unmapped_genes.tsv",
        result_prov="results/provenance/result_file_provenance.tsv",
        input_prov="results/provenance/input_file_provenance.tsv",
        manifest_trace="results/provenance/manifest_trace.tsv",
        checksums="results/provenance/checksum_manifest.tsv",
        report="results/reports/analysis_report.html",
        methods="results/reports/methods.md",
        warnings="results/reports/warnings.tsv",
        repro="results/reports/reproducibility_manifest.tsv",
        done="results/mvp/.complete"
    log:
        "logs/mvp/run_mvp_pipeline.log"
    benchmark:
        "benchmarks/mvp/run_mvp_pipeline.tsv"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/run_mvp_pipeline.py \
          --config {input.config:q} \
          --manifest {input.manifest:q} \
          --contrasts {input.contrasts:q} \
          --dataset-plan {input.dataset_plan:q} \
          --ontology {input.ontology:q} \
          --bulk-counts {input.bulk_counts:q} \
          --single-cell-counts {input.single_cell_counts:q} \
          --done {output.done:q} > {log:q} 2>&1
        """
