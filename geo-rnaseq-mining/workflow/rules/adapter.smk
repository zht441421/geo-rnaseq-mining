rule validate_adapter_registry:
    input:
        registry="config/adapter_registry.yaml"
    output:
        validation="results/compatibility/adapter_registry_validation.tsv"
    log:
        "logs/adapter/validate_adapter_registry.log"
    benchmark:
        "benchmarks/adapter/validate_adapter_registry.tsv"
    threads: 1
    resources:
        mem_mb=config["resources"]["default"]["mem_mb"],
        runtime_min=config["resources"]["default"]["runtime_min"],
        disk_mb=config["resources"]["default"]["disk_mb"]
    shell:
        """
        python workflow/scripts/dataset_adapters.py \
          --registry {input.registry:q} \
          --output {output.validation:q} > {log:q} 2>&1
        """
