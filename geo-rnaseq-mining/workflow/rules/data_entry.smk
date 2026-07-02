import csv


DATA_ENTRY_DIR = "results/compatibility"


def split_sra_accessions(value):
    if value in {"", "NA", None}:
        return []
    return [
        token.strip()
        for token in str(value).replace(",", ";").split(";")
        if token.strip() and token.strip() != "NA"
    ]


def load_reviewed_sra_metadata(path):
    metadata = {}
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if (
                row.get("include") == "true"
                and row.get("review_status") == "confirmed"
            ):
                for srr in split_sra_accessions(row.get("srr_id", "NA")):
                    metadata[srr] = row
    return metadata


SRA_METADATA = load_reviewed_sra_metadata(
    "metadata/reviewed/sample_manifest.tsv"
)
SRA_RUNS = sorted(SRA_METADATA)
SRA_PREFETCH_STATUS = expand(
    "data/sra/{srr}/.prefetch_complete.json", srr=SRA_RUNS
)
SRA_FASTQ_STATUS = expand(
    "data/fastq/{srr}/.fasterq_complete.json", srr=SRA_RUNS
)


rule inventory_supplementary_files:
    input:
        authority=rules.validate_authority_config.output.report,
        manifest="metadata/reviewed/sample_manifest.tsv",
        supplementary=rules.fetch_geo_supplementary_index.output.index
    output:
        inventory=f"{DATA_ENTRY_DIR}/supplementary_inventory.tsv"
    log:
        "logs/data_entry/inventory_supplementary_files.log"
    benchmark:
        "benchmarks/data_entry/inventory_supplementary_files.tsv"
    conda:
        "../envs/data-entry.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/inventory_supplementary_files.py \
          --manifest {input.manifest:q} \
          --supplementary {input.supplementary:q} \
          --output {output.inventory:q} \
          > {log:q} 2>&1
        """


rule classify_data_entry:
    input:
        authority=rules.validate_authority_config.output.report,
        manifest="metadata/reviewed/sample_manifest.tsv",
        supplementary=rules.inventory_supplementary_files.output.inventory
    output:
        classified=f"{DATA_ENTRY_DIR}/classified_data_entries.tsv"
    log:
        "logs/data_entry/classify_data_entry.log"
    benchmark:
        "benchmarks/data_entry/classify_data_entry.tsv"
    conda:
        "../envs/data-entry.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/classify_data_entry.py \
          --manifest {input.manifest:q} \
          --supplementary-inventory {input.supplementary:q} \
          --project-root . \
          --output {output.classified:q} \
          > {log:q} 2>&1
        """


rule download_supplementary_files:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        config="config/config.yaml",
        inventory=rules.inventory_supplementary_files.output.inventory
    output:
        status=f"{DATA_ENTRY_DIR}/supplementary_download_status.tsv"
    log:
        "logs/data_entry/download_supplementary_files.log"
    benchmark:
        "benchmarks/data_entry/download_supplementary_files.tsv"
    conda:
        "../envs/data-entry.yaml"
    threads: config["resources"]["download"]["threads"]
    resources:
        mem_mb=config["resources"]["download"]["mem_mb"],
        runtime_min=config["resources"]["download"]["runtime_min"],
        disk_mb=config["resources"]["download"]["disk_mb"]
    shell:
        """
        python workflow/scripts/download_supplementary_files.py \
          --config {input.config:q} \
          --inventory {input.inventory:q} \
          --project-root . \
          --output {output.status:q} \
          > {log:q} 2>&1
        """


rule download_sra:
    input:
        gate=rules.enforce_validation_gate.output.marker,
        manifest="metadata/reviewed/sample_manifest.tsv"
    output:
        status="data/sra/{srr}/.prefetch_complete.json"
    log:
        "logs/sra/{srr}.prefetch.log"
    benchmark:
        "benchmarks/sra/{srr}.prefetch.tsv"
    conda:
        "../envs/sra-tools.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["download"]["mem_mb"],
        runtime_min=config["resources"]["download"]["runtime_min"],
        disk_mb=config["resources"]["download"]["disk_mb"]
    params:
        enabled="--enabled" if config["data_entry"]["sra_download_enabled"] else "",
        output_dir="data/sra",
        max_size=config["data_entry"]["prefetch_max_size"],
        retries=config["data_entry"]["sra_retries"],
        retry_delay=config["data_entry"]["retry_delay_seconds"]
    shell:
        """
        python workflow/scripts/sra_pipeline.py prefetch \
          --srr {wildcards.srr} \
          --output-dir {params.output_dir:q} \
          --status {output.status:q} \
          --max-size {params.max_size} \
          --retries {params.retries} \
          --retry-delay {params.retry_delay} \
          {params.enabled} \
          > {log:q} 2>&1
        """


rule convert_sra_to_fastq:
    input:
        status="data/sra/{srr}/.prefetch_complete.json"
    output:
        status="data/fastq/{srr}/.fasterq_complete.json"
    log:
        "logs/sra/{srr}.fasterq.log"
    benchmark:
        "benchmarks/sra/{srr}.fasterq.tsv"
    conda:
        "../envs/sra-tools.yaml"
    threads: config["resources"]["download"]["threads"]
    resources:
        mem_mb=config["resources"]["download"]["mem_mb"],
        runtime_min=config["resources"]["download"]["runtime_min"],
        disk_mb=config["resources"]["download"]["disk_mb"]
    params:
        layout=lambda wildcards: SRA_METADATA[wildcards.srr].get(
            "library_layout", "NA"
        ),
        output_dir=lambda wildcards: f"data/fastq/{wildcards.srr}",
        temp_dir=config["data_entry"]["fasterq_temp_dir"]
    shell:
        """
        python workflow/scripts/sra_pipeline.py fasterq \
          --srr {wildcards.srr} \
          --layout {params.layout} \
          --prefetch-status {input.status:q} \
          --output-dir {params.output_dir:q} \
          --temp-dir {params.temp_dir:q} \
          --status {output.status:q} \
          --threads {threads} \
          > {log:q} 2>&1
        """


rule verify_downloads:
    input:
        manifest="metadata/reviewed/sample_manifest.tsv",
        supplementary=rules.download_supplementary_files.output.status,
        sra_status=SRA_FASTQ_STATUS
    output:
        verification=f"{DATA_ENTRY_DIR}/download_verification.tsv"
    log:
        "logs/data_entry/verify_downloads.log"
    benchmark:
        "benchmarks/data_entry/verify_downloads.tsv"
    conda:
        "../envs/data-entry.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/verify_downloads.py \
          --manifest {input.manifest:q} \
          --supplementary-status {input.supplementary:q} \
          --sra-status {input.sra_status:q} \
          --output {output.verification:q} \
          > {log:q} 2>&1
        """


rule build_data_inventory:
    input:
        classified=rules.classify_data_entry.output.classified,
        verified=rules.verify_downloads.output.verification
    output:
        inventory=f"{DATA_ENTRY_DIR}/data_inventory.tsv"
    log:
        "logs/data_entry/build_data_inventory.log"
    benchmark:
        "benchmarks/data_entry/build_data_inventory.tsv"
    conda:
        "../envs/data-entry.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/build_data_inventory.py \
          --classified {input.classified:q} \
          --verified {input.verified:q} \
          --output {output.inventory:q} \
          > {log:q} 2>&1
        """
