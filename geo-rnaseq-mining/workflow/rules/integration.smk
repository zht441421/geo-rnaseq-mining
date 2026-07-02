from pathlib import Path


BULK_SCRNA_INTEGRATION_ENABLED = bool(
    config["bulk_scrna_integration"].get("enabled", False)
)
BULK_SCRNA_INTEGRATION_ROOT = config["bulk_scrna_integration"]["output_dir"]
BULK_SCRNA_CONSENSUS_ROOT = config["bulk_scrna_integration"]["consensus_dir"]


def optional_arg(flag, path):
    return f"{flag} {path}" if path and Path(path).exists() else ""


BULK_SCRNA_INTEGRATION_TARGETS = (
    [
        f"{BULK_SCRNA_INTEGRATION_ROOT}/.complete",
        f"{BULK_SCRNA_CONSENSUS_ROOT}/.complete",
    ]
    if BULK_SCRNA_INTEGRATION_ENABLED
    else []
)


rule bulk_scrna_integration:
    input:
        config="config/config.yaml",
        ontology="config/celltype_ontology.tsv"
    output:
        marker=f"{BULK_SCRNA_INTEGRATION_ROOT}/.complete",
        consensus_marker=f"{BULK_SCRNA_CONSENSUS_ROOT}/.complete",
        gene_celltype=f"{BULK_SCRNA_INTEGRATION_ROOT}/gene_celltype_mapping.tsv",
        concordance=f"{BULK_SCRNA_INTEGRATION_ROOT}/bulk_scrna_concordance.tsv",
        candidate_scores=f"{BULK_SCRNA_INTEGRATION_ROOT}/candidate_gene_scores.tsv",
        dataset_support=f"{BULK_SCRNA_INTEGRATION_ROOT}/dataset_support_matrix.tsv",
        celltype_effects=f"{BULK_SCRNA_INTEGRATION_ROOT}/celltype_specific_effects.tsv",
        unmapped=f"{BULK_SCRNA_INTEGRATION_ROOT}/unmapped_genes.tsv",
        consensus_genes=f"{BULK_SCRNA_CONSENSUS_ROOT}/consensus_genes.tsv",
        consensus_pathways=f"{BULK_SCRNA_CONSENSUS_ROOT}/consensus_pathways.tsv"
    log:
        "logs/integration/bulk_scrna_integration.log"
    benchmark:
        "benchmarks/integration/bulk_scrna_integration.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        output_dir=BULK_SCRNA_INTEGRATION_ROOT,
        consensus_dir=BULK_SCRNA_CONSENSUS_ROOT,
        gene_mapping=lambda wildcards: optional_arg(
            "--gene-mapping",
            config["bulk_scrna_integration"].get("gene_mapping_file")
        )
    shell:
        """
        python workflow/scripts/run_bulk_scrna_integration.py \
          --config {input.config:q} \
          --ontology {input.ontology:q} \
          {params.gene_mapping} \
          --output-dir {params.output_dir:q} \
          --consensus-dir {params.consensus_dir:q} > {log:q} 2>&1
        """
