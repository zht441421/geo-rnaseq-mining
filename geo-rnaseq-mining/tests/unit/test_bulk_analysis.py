import csv
import tempfile
import sys
import unittest
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from bulk_common import (
    blocking_issues,
    calculate_sample_qc,
    validate_bulk_count_matrix,
)
from prepare_bulk_dataset import prepare_dataset
from preanalysis_common import read_tsv
from validate_analysis_design import validate_design_matrices


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    CONFIG = yaml.safe_load(handle)


def manifest_row(sample_id, subject_id, group, matrix_path, batch="B1"):
    return {
        "dataset_id": "GSE_TEST",
        "gse_id": "GSE_TEST",
        "gsm_id": f"GSM_{sample_id}",
        "srx_id": f"SRX_{sample_id}",
        "srr_id": f"SRR_{sample_id}",
        "sample_id": sample_id,
        "subject_id": subject_id,
        "include": "true",
        "group": group,
        "condition": group,
        "tissue": "blood",
        "batch": batch,
        "sex": "female" if sample_id in {"S1", "S3", "S5"} else "male",
        "age": "50",
        "timepoint": "baseline",
        "treatment": "none",
        "paired_group": subject_id,
        "data_type": "bulk_rnaseq",
        "library_layout": "PAIRED",
        "matrix_path": str(matrix_path),
        "fastq_r1": "NA",
        "fastq_r2": "NA",
        "notes": "",
        "reviewer_note": "",
        "review_status": "confirmed",
    }


def contrast(formula="~ group", paired="false"):
    return {
        "contrast_id": "case_vs_control",
        "analysis_id": "A1",
        "data_scope": "bulk",
        "numerator": "case",
        "denominator": "control",
        "subset_column": "NA",
        "subset_value": "NA",
        "design_formula": formula,
        "paired": paired,
        "min_replicates_per_group": "2",
        "enabled": "true",
        "notes": "",
    }


def plan():
    return [
        {
            "analysis_id": "A1",
            "dataset_id": "GSE_TEST",
            "include": "true",
            "role": "discovery",
            "merge_group": "NA",
            "analysis_strategy": "independent_only",
            "reference_dataset": "NA",
            "notes": "",
        }
    ]


def check_ids(issues):
    return {issue["check_id"] for issue in issues}


class BulkAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.fixture = PROJECT_ROOT / "tests" / "fixtures" / "small_bulk_counts.tsv"
        sample_ids = [f"S{index}" for index in range(1, 7)]
        self.manifest = [
            manifest_row(
                sample_id,
                f"P{(index + 1) // 2}",
                "control" if index % 2 else "case",
                self.fixture,
            )
            for index, sample_id in enumerate(sample_ids, start=1)
        ]

    def test_small_simulated_count_dataset_is_prepared(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_dataset(
                CONFIG,
                self.manifest,
                "GSE_TEST",
                self.fixture,
                root / "raw_counts.tsv",
                root / "sample_metadata.tsv",
                root / "input_validation.tsv",
                root / "input_provenance.json",
            )
            prepared = pd.read_csv(root / "raw_counts.tsv", sep="\t")
            metadata = read_tsv(root / "sample_metadata.tsv")
            validation = read_tsv(root / "input_validation.tsv")
        self.assertEqual(
            ["gene_id", "S1", "S2", "S3", "S4", "S5", "S6"],
            list(prepared.columns),
        )
        self.assertEqual(6, len(metadata))
        self.assertIn("ALL_ZERO_BULK_GENES", check_ids(validation))
        self.assertFalse(blocking_issues(validation))

    def test_non_integer_matrix_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "counts.tsv"
            path.write_text(
                "gene_id\tS1\tS2\nG1\t1.5\t2\n",
                encoding="utf-8",
            )
            _, issues = validate_bulk_count_matrix(
                path,
                ["S1", "S2"],
                "GSE_TEST",
            )
        self.assertIn("NON_INTEGER_BULK_COUNTS", check_ids(issues))
        self.assertTrue(blocking_issues(issues))

    def test_sample_order_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "counts.tsv"
            path.write_text(
                "gene_id\tS2\tS1\nG1\t1\t2\n",
                encoding="utf-8",
            )
            _, issues = validate_bulk_count_matrix(
                path,
                ["S1", "S2"],
                "GSE_TEST",
            )
        self.assertIn("BULK_SAMPLE_ORDER_MISMATCH", check_ids(issues))
        self.assertTrue(blocking_issues(issues))

    def test_non_full_rank_bulk_design_is_rejected(self):
        manifest = [row.copy() for row in self.manifest]
        for row in manifest:
            row["batch"] = f"B_{row['group']}"
        issues = validate_design_matrices(
            manifest,
            [contrast(formula="~ group + batch")],
            plan(),
            CONFIG,
        )
        self.assertIn("DESIGN_MATRIX_NOT_FULL_RANK", check_ids(issues))

    def test_paired_bulk_design_is_full_rank(self):
        issues = validate_design_matrices(
            self.manifest,
            [contrast(formula="~ subject_id + group", paired="true")],
            plan(),
            CONFIG,
        )
        self.assertIn("DESIGN_MATRIX_FULL_RANK", check_ids(issues))
        self.assertNotIn("DESIGN_MATRIX_NOT_FULL_RANK", check_ids(issues))
        self.assertNotIn("PAIRED_FACTOR_NOT_IN_FORMULA", check_ids(issues))

    def test_outlier_report_never_removes_samples(self):
        counts = pd.read_csv(self.fixture, sep="\t")
        counts["S6"] = counts["S6"] * 1000
        metrics, outliers = calculate_sample_qc(
            counts,
            self.manifest,
            detected_gene_min_count=1,
            outlier_z_threshold=1.0,
        )
        self.assertEqual(6, len(metrics))
        self.assertEqual(6, len(outliers))
        self.assertTrue(any(row["outlier_flag"] == "true" for row in outliers))
        self.assertTrue(
            all(row["retained_for_analysis"] == "true" for row in outliers)
        )


if __name__ == "__main__":
    unittest.main()
