RAW_METADATA_DIR = config["geo"]["metadata_raw_dir"]
SUGGESTED_METADATA_DIR = config["geo"]["metadata_suggested_dir"]
METADATA_CACHE_DIR = config["geo"]["cache_dir"]
METADATA_EVENT_DIR = f"{RAW_METADATA_DIR}/.events"
GEO_ACCESSIONS = config["geo"].get("accessions", [])
GEO_ACCESSIONS_ARG = ",".join(GEO_ACCESSIONS)
GEO_METADATA_ENV = "../envs/r-bulk.yaml" if GEO_ACCESSIONS else "../envs/base.yaml"


rule fetch_geo_metadata:
    input:
        config="config/config.yaml"
    output:
        series=f"{RAW_METADATA_DIR}/geo_series_raw.tsv",
        samples=f"{RAW_METADATA_DIR}/geo_samples_raw.tsv",
        platforms=f"{RAW_METADATA_DIR}/geo_platforms_raw.tsv",
        events=f"{METADATA_EVENT_DIR}/fetch_geo_metadata.tsv"
    log:
        "logs/metadata/fetch_geo_metadata.log"
    benchmark:
        "benchmarks/metadata/fetch_geo_metadata.tsv"
    conda:
        GEO_METADATA_ENV
    threads: 1
    resources:
        mem_mb=config["resources"]["download"]["mem_mb"],
        runtime_min=config["resources"]["download"]["runtime_min"],
        disk_mb=config["resources"]["download"]["disk_mb"]
    params:
        accessions=GEO_ACCESSIONS_ARG,
        cache_dir=f"{METADATA_CACHE_DIR}/geo",
        retries=config["geo"]["retries"],
        retry_delay=config["geo"]["retry_delay_seconds"]
    shell:
        """
        python workflow/scripts/fetch_geo_metadata.py \
          --accessions "{params.accessions}" \
          --series-output {output.series:q} \
          --samples-output {output.samples:q} \
          --platforms-output {output.platforms:q} \
          --event-log {output.events:q} \
          --cache-dir {params.cache_dir:q} \
          --retries {params.retries} \
          --retry-delay {params.retry_delay} \
          > {log:q} 2>&1
        """


rule fetch_geo_supplementary_index:
    input:
        config="config/config.yaml",
        series=rules.fetch_geo_metadata.output.series,
        samples=rules.fetch_geo_metadata.output.samples
    output:
        index=f"{RAW_METADATA_DIR}/geo_supplementary_files_raw.tsv",
        legacy=f"{RAW_METADATA_DIR}/supplementary_files_raw.tsv",
        events=f"{METADATA_EVENT_DIR}/fetch_geo_supplementary_index.tsv"
    log:
        "logs/metadata/fetch_geo_supplementary_index.log"
    benchmark:
        "benchmarks/metadata/fetch_geo_supplementary_index.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["download"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        cache_dir=f"{METADATA_CACHE_DIR}/supplementary",
        retries=config["geo"]["retries"],
        retry_delay=config["geo"]["retry_delay_seconds"],
        timeout=config["geo"]["timeout_seconds"],
        use_head="--use-head" if config["geo"]["supplementary_head_requests"] else "",
        user_agent=config["geo"]["user_agent"]
    shell:
        """
        python workflow/scripts/fetch_geo_supplementary_index.py \
          --series {input.series:q} \
          --samples {input.samples:q} \
          --output {output.index:q} \
          --legacy-output {output.legacy:q} \
          --event-log {output.events:q} \
          --cache-dir {params.cache_dir:q} \
          --retries {params.retries} \
          --retry-delay {params.retry_delay} \
          --timeout {params.timeout} \
          --user-agent "{params.user_agent}" \
          {params.use_head} \
          > {log:q} 2>&1
        """


rule fetch_sra_runinfo:
    input:
        config="config/config.yaml",
        samples=rules.fetch_geo_metadata.output.samples
    output:
        runinfo=f"{RAW_METADATA_DIR}/sra_runinfo_raw.tsv",
        events=f"{METADATA_EVENT_DIR}/fetch_sra_runinfo.tsv"
    log:
        "logs/metadata/fetch_sra_runinfo.log"
    benchmark:
        "benchmarks/metadata/fetch_sra_runinfo.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["download"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    params:
        cache_dir=f"{METADATA_CACHE_DIR}/sra",
        retries=config["geo"]["retries"],
        retry_delay=config["geo"]["retry_delay_seconds"],
        timeout=config["geo"]["timeout_seconds"],
        request_interval=config["geo"]["ncbi_request_interval_seconds"],
        email=config["geo"].get("ncbi_email") or "",
        api_key_env=config["geo"]["ncbi_api_key_env"],
        user_agent=config["geo"]["user_agent"]
    shell:
        """
        python workflow/scripts/fetch_sra_runinfo.py \
          --samples {input.samples:q} \
          --output {output.runinfo:q} \
          --event-log {output.events:q} \
          --cache-dir {params.cache_dir:q} \
          --retries {params.retries} \
          --retry-delay {params.retry_delay} \
          --timeout {params.timeout} \
          --request-interval {params.request_interval} \
          --email "{params.email}" \
          --api-key-env "{params.api_key_env}" \
          --user-agent "{params.user_agent}" \
          > {log:q} 2>&1
        """


rule prepare_raw_metadata:
    input:
        series=rules.fetch_geo_metadata.output.series,
        samples=rules.fetch_geo_metadata.output.samples,
        platforms=rules.fetch_geo_metadata.output.platforms,
        runinfo=rules.fetch_sra_runinfo.output.runinfo,
        supplementary=rules.fetch_geo_supplementary_index.output.index,
        geo_events=rules.fetch_geo_metadata.output.events,
        sra_events=rules.fetch_sra_runinfo.output.events,
        supplementary_events=rules.fetch_geo_supplementary_index.output.events
    output:
        fetch_log=f"{RAW_METADATA_DIR}/metadata_fetch_log.tsv",
        checksums=f"{RAW_METADATA_DIR}/metadata_checksums.sha256"
    log:
        "logs/metadata/prepare_raw_metadata.log"
    benchmark:
        "benchmarks/metadata/prepare_raw_metadata.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_raw_metadata.py \
          --data-files {input.series:q} {input.samples:q} {input.platforms:q} \
                       {input.runinfo:q} {input.supplementary:q} \
          --event-files {input.geo_events:q} {input.sra_events:q} \
                        {input.supplementary_events:q} \
          --fetch-log {output.fetch_log:q} \
          --checksums {output.checksums:q} \
          > {log:q} 2>&1
        """


rule prepare_manifest:
    input:
        config="config/config.yaml",
        samples=rules.fetch_geo_metadata.output.samples,
        runinfo=rules.fetch_sra_runinfo.output.runinfo,
        supplementary=rules.fetch_geo_supplementary_index.output.index
    output:
        manifest=f"{SUGGESTED_METADATA_DIR}/sample_manifest_suggested.tsv",
        conflicts=f"{SUGGESTED_METADATA_DIR}/metadata_conflicts.tsv",
        unmapped=f"{SUGGESTED_METADATA_DIR}/unmapped_runs.tsv"
    log:
        "logs/metadata/prepare_manifest.log"
    benchmark:
        "benchmarks/metadata/prepare_manifest.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_manifest.py \
          --config {input.config:q} \
          --samples {input.samples:q} \
          --runinfo {input.runinfo:q} \
          --supplementary {input.supplementary:q} \
          --manifest {output.manifest:q} \
          --conflicts {output.conflicts:q} \
          --unmapped-runs {output.unmapped:q} \
          > {log:q} 2>&1
        """


rule prepare_dataset_plan_suggested:
    input:
        config="config/config.yaml",
        manifest=rules.prepare_manifest.output.manifest
    output:
        dataset_plan=f"{SUGGESTED_METADATA_DIR}/dataset_plan_suggested.tsv"
    log:
        "logs/metadata/prepare_dataset_plan_suggested.log"
    benchmark:
        "benchmarks/metadata/prepare_dataset_plan_suggested.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_dataset_plan_suggested.py \
          --config {input.config:q} \
          --manifest {input.manifest:q} \
          --output {output.dataset_plan:q} \
          > {log:q} 2>&1
        """


rule prepare_data_entry_classification:
    input:
        samples=rules.fetch_geo_metadata.output.samples,
        runinfo=rules.fetch_sra_runinfo.output.runinfo,
        supplementary=rules.fetch_geo_supplementary_index.output.index
    output:
        classification=f"{SUGGESTED_METADATA_DIR}/data_entry_classification.tsv"
    log:
        "logs/metadata/prepare_data_entry_classification.log"
    benchmark:
        "benchmarks/metadata/prepare_data_entry_classification.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/prepare_data_entry_classification.py \
          --samples {input.samples:q} \
          --runinfo {input.runinfo:q} \
          --supplementary {input.supplementary:q} \
          --output {output.classification:q} \
          > {log:q} 2>&1
        """


rule generate_metadata_review_report:
    input:
        manifest=rules.prepare_manifest.output.manifest,
        conflicts=rules.prepare_manifest.output.conflicts,
        unmapped=rules.prepare_manifest.output.unmapped,
        dataset_plan=rules.prepare_dataset_plan_suggested.output.dataset_plan,
        classification=rules.prepare_data_entry_classification.output.classification
    output:
        report=f"{SUGGESTED_METADATA_DIR}/metadata_review_report.html"
    log:
        "logs/metadata/generate_metadata_review_report.log"
    benchmark:
        "benchmarks/metadata/generate_metadata_review_report.tsv"
    conda:
        "../envs/base.yaml"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/generate_metadata_review_report.py \
          --manifest {input.manifest:q} \
          --conflicts {input.conflicts:q} \
          --unmapped-runs {input.unmapped:q} \
          --dataset-plan {input.dataset_plan:q} \
          --data-entry-classification {input.classification:q} \
          --output {output.report:q} \
          > {log:q} 2>&1
        """
