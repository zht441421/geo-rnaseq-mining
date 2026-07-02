import copy
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from multi_dataset_common import (
    assess_compatibility,
    dominant_dataset,
    leave_one_dataset_out,
    meta_analyze_evidence,
)
from prepare_joint_bulk import prepare_joint_dataset
from run_bulk_meta_analysis import run_meta_analysis
from run_bulk_stratified_validation import run_stratified_validation
from validate_dataset_plan import validate_dataset_plan


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    BASE_CONFIG = yaml.safe_load(handle)


def manifest_row(dataset_id, sample_id, group, matrix_path):
    return {
        "dataset_id": dataset_id,
        "gse_id": dataset_id,
        "gsm_id": f"GSM_{dataset_id}_{sample_id}",
        "srx_id": f"SRX_{dataset_id}_{sample_id}",
        "srr_id": f"SRR_{dataset_id}_{sample_id}",
        "sample_id": f"{dataset_id}_{sample_id}",
        "subject_id": f"{dataset_id}_P{sample_id}",
        "include": "true",
        "group": group,
        "condition": group,
        "tissue": "blood",
        "batch": "B1",
        "sex": "female",
        "age": "50",
        "timepoint": "baseline",
        "treatment": "none",
        "paired_group": f"{dataset_id}_P{sample_id}",
        "data_type": "bulk_rnaseq",
        "library_layout": "PAIRED",
        "matrix_path": str(matrix_path),
        "fastq_r1": "NA",
        "fastq_r2": "NA",
        "notes": "",
        "reviewer_note": "",
        "review_status": "confirmed",
    }


def plan_rows(strategy="joint_model", roles=None):
    roles = roles or {"GSE1": "discovery", "GSE2": "discovery"}
    return [
        {
            "analysis_id": "A1",
            "dataset_id": dataset_id,
            "include": "true",
            "role": roles[dataset_id],
            "merge_group": "M1",
            "analysis_strategy": strategy,
            "reference_dataset": "NA",
            "notes": "",
        }
        for dataset_id in ("GSE1", "GSE2")
    ]


def contrast():
    return {
        "contrast_id": "case_vs_control",
        "analysis_id": "A1",
        "data_scope": "bulk",
        "numerator": "case",
        "denominator": "control",
        "subset_column": "NA",
        "subset_value": "NA",
        "design_formula": "~ dataset_id + group",
        "paired": "false",
        "min_replicates_per_group": "1",
        "enabled": "true",
        "notes": "",
    }


def configured():
    config = copy.deepcopy(BASE_CONFIG)
    config["multi_dataset"]["joint_model"]["allow_author_counts"] = True
    config["validation"]["dataset_compatibility"] = {
        dataset_id: {
            "species": "Homo sapiens",
            "platform": "Illumina",
            "library_strategy": "RNA-Seq",
            "reference_genome": "GRCh38",
            "annotation_version": "GENCODE_48",
            "gene_id_type": "Ensembl_gene",
            "quantification_source": "author_gene_level_counts",
        }
        for dataset_id in ("GSE1", "GSE2")
    }
    return config


def write_matrix(path, sample_ids, fractional=False):
    values = {
        "gene_id": ["ENSG1", "ENSG2", "ENSG3"],
    }
    for index, sample_id in enumerate(sample_ids, start=1):
        values[sample_id] = [
            10.5 if fractional and index == 1 else 10 + index,
            20 + index,
            30 + index,
        ]
    pd.DataFrame(values).to_csv(path, sep="\t", index=False)


def evidence_row(dataset_id, effect, se=0.2, pvalue=0.001, gene_id="G1", sample_size=20):
    return {
        "gene_id": gene_id,
        "gene_symbol": gene_id,
        "dataset_id": dataset_id,
        "log2FoldChange": effect,
        "lfcSE": se,
        "pvalue": pvalue,
        "sample_size": sample_size,
    }


def write_deseq_result(root, dataset_id, effect, pvalue=0.001):
    contrast_dir = (
        root
        / dataset_id
        / "bulk"
        / "deseq2"
        / "case_vs_control"
    )
    contrast_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "gene_id": ["G1", "G2"],
            "gene_symbol": ["GENE1", "GENE2"],
            "log2FoldChange": [effect, 0.1],
            "lfcSE": [0.2, 0.5],
            "pvalue": [pvalue, 0.8],
        }
    ).to_csv(
        contrast_dir / "deseq2_full_results.tsv",
        sep="\t",
        index=False,
    )
    pd.DataFrame({"sample_count": [20]}).to_csv(
        contrast_dir / "contrast_qc.tsv",
        sep="\t",
        index=False,
    )


class MultiDatasetAnalysisTests(unittest.TestCase):
    def make_manifest(self, root, groups=None, fractional_dataset=None):
        groups = groups or {
            "GSE1": ["control", "case"],
            "GSE2": ["control", "case"],
        }
        rows = []
        for dataset_id in ("GSE1", "GSE2"):
            path = root / f"{dataset_id}_counts.tsv"
            dataset_rows = [
                manifest_row(dataset_id, str(index), group, path)
                for index, group in enumerate(groups[dataset_id], start=1)
            ]
            write_matrix(
                path,
                [row["sample_id"] for row in dataset_rows],
                fractional=dataset_id == fractional_dataset,
            )
            rows.extend(dataset_rows)
        return rows

    def test_two_compatible_datasets_are_joint_model_eligible(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self.make_manifest(Path(temporary))
            rows = assess_compatibility(
                manifest,
                plan_rows(),
                [contrast()],
                configured(),
            )
        self.assertEqual(2, len(rows))
        self.assertTrue(
            all(row["compatible_for_joint_model"] == "true" for row in rows)
        )

    def test_complete_dataset_group_confounding_blocks_joint_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self.make_manifest(
                Path(temporary),
                {"GSE1": ["case", "case"], "GSE2": ["control", "control"]},
            )
            rows = assess_compatibility(
                manifest,
                plan_rows(),
                [contrast()],
                configured(),
            )
        self.assertTrue(
            all(
                "dataset_group_complete_confounding"
                in row["incompatibility_reason"]
                for row in rows
            )
        )
        self.assertTrue(
            all(row["compatible_for_joint_model"] == "false" for row in rows)
        )

    def test_different_gene_id_versions_block_joint_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self.make_manifest(Path(temporary))
            config = configured()
            config["validation"]["dataset_compatibility"]["GSE2"][
                "gene_id_type"
            ] = "Ensembl_gene_versioned"
            rows = assess_compatibility(
                manifest,
                plan_rows(),
                [contrast()],
                config,
            )
        self.assertTrue(
            all(
                "incompatible_or_unknown_gene_id_type"
                in row["incompatibility_reason"]
                for row in rows
            )
        )

    def test_tpm_like_fractional_matrix_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self.make_manifest(
                Path(temporary),
                fractional_dataset="GSE2",
            )
            rows = assess_compatibility(
                manifest,
                plan_rows(),
                [contrast()],
                configured(),
            )
        gse2 = next(row for row in rows if row["dataset_id"] == "GSE2")
        self.assertEqual("normalized_or_invalid_matrix", gse2["count_source"])
        self.assertEqual("false", gse2["compatible_for_joint_model"])
        self.assertIn("raw_integer_counts_unavailable", gse2["incompatibility_reason"])

    def test_opposite_effect_directions_are_reported(self):
        evidence = [
            evidence_row("GSE1", 1.5),
            evidence_row("GSE2", -1.5),
        ]
        result = meta_analyze_evidence(
            evidence,
            "random_effects",
            min_studies=2,
        )[0]
        self.assertEqual("mixed", result["direction_consistency"])
        self.assertIn('"GSE1"', result["dataset_specific_effects"])
        self.assertIn('"GSE2"', result["dataset_specific_effects"])

    def test_single_dataset_dominance_is_flagged(self):
        rows = [
            {"dataset_id": "GSE1"} for _ in range(9)
        ] + [{"dataset_id": "GSE2"}]
        result = dominant_dataset(rows, 0.8)
        self.assertEqual("GSE1", result[0])
        self.assertAlmostEqual(0.9, result[1])

    def test_leave_one_dataset_out_instability_is_flagged(self):
        evidence = [
            evidence_row("GSE1", 3.0, se=0.1, pvalue=1e-12),
            evidence_row("GSE2", -0.2, se=0.5, pvalue=0.7),
            evidence_row("GSE3", -0.2, se=0.5, pvalue=0.7),
        ]
        summary, detail = leave_one_dataset_out(
            evidence,
            "random_effects",
            min_studies=2,
            effect_change_threshold=0.2,
        )
        self.assertEqual("true", summary[0]["dataset_driven"])
        self.assertTrue(
            any(row["excluded_dataset"] == "GSE1" for row in detail)
        )

    def test_validation_dataset_leakage_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self.make_manifest(Path(temporary))
            plan = plan_rows(
                "per_dataset_meta",
                {"GSE1": "discovery", "GSE2": "validation"},
            )
            issues = validate_dataset_plan(
                manifest,
                [contrast()],
                plan,
                configured(),
            )
        self.assertIn(
            "VALIDATION_DATA_IN_DISCOVERY_MODEL",
            {row["check_id"] for row in issues},
        )

    def test_joint_input_preparation_combines_only_validated_raw_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self.make_manifest(root)
            config = configured()
            compatibility = assess_compatibility(
                manifest,
                plan_rows(),
                [contrast()],
                config,
            )
            dataset_root = root / "per_dataset"
            for dataset_id in ("GSE1", "GSE2"):
                rows = [
                    row for row in manifest if row["dataset_id"] == dataset_id
                ]
                input_dir = dataset_root / dataset_id / "bulk" / "input"
                input_dir.mkdir(parents=True)
                source = pd.read_csv(rows[0]["matrix_path"], sep="\t")
                source.to_csv(
                    input_dir / "raw_counts.tsv",
                    sep="\t",
                    index=False,
                )
                pd.DataFrame(rows).assign(dataset=dataset_id).to_csv(
                    input_dir / "sample_metadata.tsv",
                    sep="\t",
                    index=False,
                )
            prepare_joint_dataset(
                config,
                manifest,
                plan_rows(),
                [contrast()],
                compatibility,
                "A1",
                dataset_root,
                root / "joint_counts.tsv",
                root / "joint_metadata.tsv",
                root / "joint_validation.tsv",
                root / "joint_provenance.json",
            )
            combined = pd.read_csv(root / "joint_counts.tsv", sep="\t")
            metadata = pd.read_csv(root / "joint_metadata.tsv", sep="\t")
        self.assertEqual(4, len(combined.columns) - 1)
        self.assertEqual(combined.columns[1:].tolist(), metadata["sample_id"].tolist())

    def test_per_dataset_meta_writes_effects_and_loo_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_root = root / "per_dataset"
            write_deseq_result(result_root, "GSE1", 1.5)
            write_deseq_result(result_root, "GSE2", 1.0)
            compatibility = [
                {
                    "analysis_id": "A1",
                    "dataset_id": dataset_id,
                    "contrast_id": "case_vs_control",
                    "compatible_for_meta_analysis": "true",
                }
                for dataset_id in ("GSE1", "GSE2")
            ]
            run_meta_analysis(
                configured(),
                plan_rows("per_dataset_meta"),
                [contrast()],
                compatibility,
                "A1",
                result_root,
                root / "meta",
                root / "consensus",
            )
            results = pd.read_csv(
                root / "meta" / "case_vs_control" / "meta_results.tsv",
                sep="\t",
            )
            loo = pd.read_csv(
                root
                / "consensus"
                / "case_vs_control"
                / "leave_one_dataset_out_summary.tsv",
                sep="\t",
            )
        self.assertIn("dataset_specific_effects", results.columns)
        self.assertIn("direction_consistency", results.columns)
        self.assertIn("dataset_driven", loo.columns)

    def test_stratified_validation_keeps_candidate_selection_discovery_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_root = root / "per_dataset"
            write_deseq_result(result_root, "GSE1", 2.0, 1e-8)
            write_deseq_result(result_root, "GSE2", -2.0, 1e-8)
            stratified_plan = plan_rows(
                "stratified_validation",
                {"GSE1": "discovery", "GSE2": "validation"},
            )
            compatibility = [
                {
                    "analysis_id": "A1",
                    "dataset_id": dataset_id,
                    "contrast_id": "case_vs_control",
                    "compatible_for_meta_analysis": "true",
                }
                for dataset_id in ("GSE1", "GSE2")
            ]
            run_stratified_validation(
                configured(),
                stratified_plan,
                [contrast()],
                compatibility,
                "A1",
                result_root,
                root / "validation",
                root / "consensus",
            )
            results = pd.read_csv(
                root
                / "validation"
                / "case_vs_control"
                / "stratified_validation.tsv",
                sep="\t",
            )
            completion = (
                root / "validation" / ".complete"
            ).read_text(encoding="utf-8")
        gene = results.loc[results["gene_id"] == "G1"].iloc[0]
        self.assertTrue(bool(gene["candidate_selected"]))
        self.assertEqual("direction_mismatch", gene["replication_status"])
        self.assertIn('"candidate_selection_uses_validation": false', completion)


if __name__ == "__main__":
    unittest.main()
