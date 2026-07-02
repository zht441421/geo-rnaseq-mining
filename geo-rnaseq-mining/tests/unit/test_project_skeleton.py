import csv
import unittest
from pathlib import Path

import jsonschema
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ProjectSkeletonTests(unittest.TestCase):
    def test_required_config_sections_exist(self):
        config_path = PROJECT_ROOT / "config" / "config.yaml"
        with config_path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle)

        required = {
            "project",
            "geo",
            "references",
            "resources",
            "validation",
            "data_entry",
            "bulk",
            "single_cell",
            "multi_dataset",
            "reporting",
            "reproducibility",
        }
        self.assertTrue(required.issubset(set(config)))

    def test_manual_authority_files_exist_and_have_headers(self):
        authority_files = {
            "metadata/reviewed/sample_manifest.tsv": {
                "dataset_id",
                "sample_id",
                "subject_id",
                "group",
                "include",
                "batch",
                "tissue",
                "data_type",
                "review_status",
            },
            "config/contrasts.tsv": {
                "contrast_id",
                "analysis_id",
                "numerator",
                "denominator",
                "design_formula",
                "paired",
            },
            "config/dataset_plan.tsv": {
                "analysis_id",
                "dataset_id",
                "include",
                "role",
                "analysis_strategy",
            },
            "config/celltype_ontology.tsv": {
                "dataset_id",
                "author_label",
                "harmonized_level1",
                "review_status",
            },
        }

        for relative_path, required_headers in authority_files.items():
            with self.subTest(path=relative_path):
                path = PROJECT_ROOT / relative_path
                self.assertTrue(path.is_file())
                with path.open(encoding="utf-8", newline="") as handle:
                    headers = set(next(csv.reader(handle, delimiter="\t")))
                self.assertTrue(required_headers.issubset(headers))

    def test_templates_keep_manual_decisions_unresolved(self):
        authority_paths = (
            PROJECT_ROOT / "metadata" / "reviewed" / "sample_manifest.tsv",
            PROJECT_ROOT / "config" / "contrasts.tsv",
            PROJECT_ROOT / "config" / "dataset_plan.tsv",
            PROJECT_ROOT / "config" / "celltype_ontology.tsv",
        )
        for path in authority_paths:
            with self.subTest(path=path):
                with path.open(encoding="utf-8", newline="") as handle:
                    self.assertEqual([], list(csv.DictReader(handle, delimiter="\t")))

    def test_snakefile_includes_module_skeletons(self):
        snakefile = (PROJECT_ROOT / "workflow" / "Snakefile").read_text(
            encoding="utf-8"
        )
        for module in (
            "common",
            "metadata",
            "validation",
            "bulk",
            "single_cell",
            "multi_dataset",
            "integration",
            "reporting",
        ):
            self.assertIn(f'include: "rules/{module}.smk"', snakefile)

    def test_all_yaml_templates_parse(self):
        yaml_paths = [
            PROJECT_ROOT / "config" / "config.yaml",
            *sorted((PROJECT_ROOT / "workflow" / "envs").glob("*.yaml")),
            *sorted((PROJECT_ROOT / "workflow" / "schemas").glob("*.yaml")),
            *sorted((PROJECT_ROOT / "profiles").glob("*/config.yaml")),
        ]
        self.assertTrue(yaml_paths)
        for path in yaml_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                with path.open(encoding="utf-8") as handle:
                    self.assertIsNotNone(yaml.safe_load(handle))

    def test_config_matches_schema(self):
        with (PROJECT_ROOT / "config" / "config.yaml").open(
            encoding="utf-8"
        ) as handle:
            config = yaml.safe_load(handle)
        with (PROJECT_ROOT / "workflow" / "schemas" / "config.schema.yaml").open(
            encoding="utf-8"
        ) as handle:
            schema = yaml.safe_load(handle)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(config, schema)

    def test_executable_rules_declare_operational_fields(self):
        required_fields = (
            "input:",
            "output:",
            "log:",
            "benchmark:",
            "threads:",
            "resources:",
        )
        rule_sources = {
            "all": (PROJECT_ROOT / "workflow" / "Snakefile").read_text(
                encoding="utf-8"
            ),
            "authority_files": (
                PROJECT_ROOT / "workflow" / "rules" / "common.smk"
            ).read_text(encoding="utf-8"),
            "validate_authority_config": (
                PROJECT_ROOT / "workflow" / "rules" / "common.smk"
            ).read_text(encoding="utf-8"),
        }
        for rule_name, source in rule_sources.items():
            with self.subTest(rule=rule_name):
                for field in required_fields:
                    self.assertIn(field, source)

    def test_metadata_rules_are_registered(self):
        metadata_rules = (
            PROJECT_ROOT / "workflow" / "rules" / "metadata.smk"
        ).read_text(encoding="utf-8")
        for rule_name in (
            "fetch_geo_metadata",
            "fetch_geo_supplementary_index",
            "fetch_sra_runinfo",
            "prepare_raw_metadata",
            "prepare_manifest",
            "generate_metadata_review_report",
        ):
            self.assertIn(f"rule {rule_name}:", metadata_rules)

    def test_validation_rules_are_registered(self):
        validation_rules = (
            PROJECT_ROOT / "workflow" / "rules" / "validation.smk"
        ).read_text(encoding="utf-8")
        for rule_name in (
            "validate_manifest",
            "validate_contrasts",
            "validate_dataset_plan",
            "validate_celltype_ontology",
            "validate_analysis_design",
            "generate_validation_report",
        ):
            self.assertIn(f"rule {rule_name}:", validation_rules)

    def test_data_entry_rules_are_registered(self):
        data_entry_rules = (
            PROJECT_ROOT / "workflow" / "rules" / "data_entry.smk"
        ).read_text(encoding="utf-8")
        for rule_name in (
            "inventory_supplementary_files",
            "classify_data_entry",
            "download_supplementary_files",
            "download_sra",
            "convert_sra_to_fastq",
            "verify_downloads",
            "build_data_inventory",
        ):
            self.assertIn(f"rule {rule_name}:", data_entry_rules)
        self.assertIn("def split_sra_accessions", data_entry_rules)
        self.assertIn('str(value).replace(",", ";").split(";")', data_entry_rules)

    def test_bulk_rules_are_registered(self):
        bulk_rules = (
            PROJECT_ROOT / "workflow" / "rules" / "bulk.smk"
        ).read_text(encoding="utf-8")
        for rule_name in (
            "bulk_fastqc",
            "bulk_multiqc",
            "bulk_salmon_quant",
            "bulk_tximport",
            "bulk_star_align",
            "bulk_featurecounts",
            "prepare_bulk_dataset",
            "bulk_sample_qc",
            "bulk_deseq2",
            "bulk_enrichment",
            "bulk_single_dataset_analysis",
        ):
            self.assertIn(f"rule {rule_name}:", bulk_rules)

    def test_single_cell_rules_are_registered(self):
        rules = (
            PROJECT_ROOT / "workflow" / "rules" / "single_cell.smk"
        ).read_text(encoding="utf-8")
        for rule_name in (
            "preprocess_single_cell_dataset",
            "prepare_single_cell_pseudobulk",
            "single_cell_pseudobulk_deseq2",
            "single_cell_proportion",
            "single_cell_dataset_analysis",
        ):
            self.assertIn(f"rule {rule_name}:", rules)

    def test_reporting_and_optional_bulk_rules_are_registered(self):
        reporting = (
            PROJECT_ROOT / "workflow" / "rules" / "reporting.smk"
        ).read_text(encoding="utf-8")
        bulk = (
            PROJECT_ROOT / "workflow" / "rules" / "bulk.smk"
        ).read_text(encoding="utf-8")
        for rule_name in (
            "collect_provenance",
            "collect_software_versions",
            "collect_reference_metadata",
            "build_audit_trail",
            "render_analysis_report",
            "render_methods_report",
            "package_results",
        ):
            self.assertIn(f"rule {rule_name}:", reporting)
        self.assertIn("rule bulk_optional_modules:", bulk)

    def test_bulk_scrna_integration_rules_are_registered(self):
        rules = (
            PROJECT_ROOT / "workflow" / "rules" / "integration.smk"
        ).read_text(encoding="utf-8")
        self.assertIn("rule bulk_scrna_integration:", rules)
        snakefile = (PROJECT_ROOT / "workflow" / "Snakefile").read_text(
            encoding="utf-8"
        )
        self.assertIn("BULK_SCRNA_INTEGRATION_TARGETS", snakefile)

    def test_rscript_calls_use_portable_launcher(self):
        launcher = PROJECT_ROOT / "workflow" / "scripts" / "run_rscript.py"
        self.assertTrue(launcher.is_file())
        for relative_path in (
            "workflow/rules/metadata.smk",
            "workflow/rules/bulk.smk",
            "workflow/rules/multi_dataset.smk",
            "workflow/rules/single_cell.smk",
        ):
            with self.subTest(path=relative_path):
                source = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("python workflow/scripts/run_rscript.py", source)
                self.assertNotIn("\n        Rscript ", source)
        single_cell_common = (
            PROJECT_ROOT / "workflow" / "scripts" / "single_cell_common.py"
        ).read_text(encoding="utf-8")
        self.assertIn("run_rscript.py", single_cell_common)
        self.assertNotIn('command = ["Rscript"', single_cell_common)


if __name__ == "__main__":
    unittest.main()
