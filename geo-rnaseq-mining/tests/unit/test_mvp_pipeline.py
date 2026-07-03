import csv
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "workflow" / "scripts"))

from run_mvp_pipeline import (  # noqa: E402
    read_count_matrix,
    validate_manifest,
    write_provenance,
)


def manifest_row(sample_id, group="control", subject_id="P1", dataset_id="GSE_MVP", data_type="bulk_matrix"):
    return {
        "dataset_id": dataset_id,
        "sample_id": sample_id,
        "subject_id": subject_id,
        "include": "true",
        "group": group,
        "data_type": data_type,
        "matrix_path": "counts.tsv",
        "review_status": "confirmed",
    }


def contrast(formula="~ group"):
    return {
        "contrast_id": "case_vs_control",
        "analysis_id": "mvp_analysis",
        "numerator": "case",
        "denominator": "control",
        "design_formula": formula,
        "enabled": "true",
    }


def plan_row(dataset_id="GSE_MVP", role="discovery", strategy="independent_only"):
    return {
        "analysis_id": "mvp_analysis",
        "dataset_id": dataset_id,
        "include": "true",
        "role": role,
        "analysis_strategy": strategy,
    }


def counts(*sample_ids):
    return pd.DataFrame({"gene_id": ["GENE1", "GENE2"], **{sample: [100, 50] for sample in sample_ids}})


def check_ids(issues):
    return {issue["check_id"] for issue in issues}


class MvpPipelineValidationTests(unittest.TestCase):
    def test_pending_included_sample_blocks_mvp(self):
        manifest = [manifest_row("S1"), manifest_row("S2", group="case", subject_id="P2")]
        manifest[1]["review_status"] = "pending"
        _, errors, _ = validate_manifest(manifest, [contrast()], [plan_row()], counts("S1", "S2"))
        self.assertIn("INCLUDED_SAMPLE_NOT_CONFIRMED", check_ids(errors))

    def test_missing_group_blocks_bulk_de(self):
        manifest = [manifest_row("S1"), manifest_row("S2", group="", subject_id="P2")]
        _, errors, _ = validate_manifest(manifest, [contrast()], [plan_row()], counts("S1", "S2"))
        self.assertIn("INCLUDED_BULK_SAMPLE_MISSING_GROUP", check_ids(errors))

    def test_missing_subject_blocks_single_cell_pseudobulk(self):
        manifest = [
            manifest_row("S1"),
            manifest_row("S2", group="case", subject_id="P2"),
            manifest_row("SC1", subject_id="", data_type="single_cell_h5ad"),
        ]
        _, errors, _ = validate_manifest(manifest, [contrast()], [plan_row()], counts("S1", "S2"))
        self.assertIn("INCLUDED_SINGLE_CELL_SAMPLE_MISSING_SUBJECT_ID", check_ids(errors))

    def test_contrast_unknown_group_blocks_mvp(self):
        manifest = [manifest_row("S1"), manifest_row("S2", group="case", subject_id="P2")]
        bad = contrast()
        bad["numerator"] = "missing_case"
        _, errors, _ = validate_manifest(manifest, [bad], [plan_row()], counts("S1", "S2"))
        self.assertIn("GROUP_NOT_FOUND", check_ids(errors))

    def test_confounded_joint_model_blocks_mvp(self):
        manifest = [
            manifest_row("S1", "control", "P1", "D1"),
            manifest_row("S2", "control", "P2", "D1"),
            manifest_row("S3", "case", "P3", "D2"),
            manifest_row("S4", "case", "P4", "D2"),
        ]
        plan = [plan_row("D1", strategy="joint_model"), plan_row("D2", strategy="joint_model")]
        _, errors, _ = validate_manifest(manifest, [contrast()], plan, counts("S1", "S2", "S3", "S4"))
        self.assertIn("JOINT_MODEL_DATASET_GROUP_COMPLETELY_CONFOUNDED", check_ids(errors))

    def test_validation_dataset_not_allowed_in_discovery_model(self):
        manifest = [manifest_row("S1"), manifest_row("S2", group="case", subject_id="P2")]
        plan = [plan_row(role="validation", strategy="joint_model")]
        _, errors, _ = validate_manifest(manifest, [contrast()], plan, counts("S1", "S2"))
        self.assertIn("VALIDATION_DATASET_IN_DISCOVERY_MODEL", check_ids(errors))

    def test_tpm_like_matrix_is_rejected_before_deseq2(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tpm.tsv"
            path.write_text("gene_id\tS1\tS2\nGENE1\t1.2\t2.3\nGENE2\t3.4\t4.5\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-integer|normalized/log-like"):
                read_count_matrix(path)

    def test_matrix_column_order_mismatch_blocks_mvp(self):
        manifest = [manifest_row("S1"), manifest_row("S2", group="case", subject_id="P2")]
        _, errors, _ = validate_manifest(manifest, [contrast()], [plan_row()], counts("S2", "S1"))
        self.assertIn("COUNT_MATRIX_SAMPLE_ORDER_MISMATCH", check_ids(errors))

    def test_result_provenance_has_required_trace_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = root / "results" / "compatibility" / "validated_manifest.tsv"
            result.parent.mkdir(parents=True)
            result.write_text("sample_id\nS1\n", encoding="utf-8")
            config = root / "config.yaml"
            manifest_path = root / "manifest.tsv"
            config.write_text("project: {}\n", encoding="utf-8")
            manifest_path.write_text("sample_id\nS1\n", encoding="utf-8")
            manifest = [manifest_row("S1")]
            write_provenance(
                root,
                [config, manifest_path],
                manifest,
                config,
                "mvp_analysis",
                "case_vs_control",
                "GSE_MVP",
            )
            with (root / "results" / "provenance" / "result_file_provenance.tsv").open(
                encoding="utf-8",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertGreaterEqual(len(rows), 1)
        required = {
            "producing_rule",
            "input_files",
            "input_checksums",
            "script",
            "config",
            "analysis_id",
            "contrast_id",
            "dataset_id",
            "manifest_rows",
            "timestamp",
            "git_commit",
        }
        self.assertTrue(required.issubset(rows[0]))
        self.assertEqual("mvp_analysis", rows[0]["analysis_id"])


if __name__ == "__main__":
    unittest.main()
