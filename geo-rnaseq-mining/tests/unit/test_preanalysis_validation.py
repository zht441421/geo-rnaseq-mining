import csv
import tempfile
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from preanalysis_common import read_tsv
from validate_analysis_design import validate_design_matrices
from validate_celltype_ontology import validate_celltype_ontology
from validate_contrasts import validate_contrasts
from validate_dataset_plan import validate_dataset_plan
from validate_manifest import validate_manifest_rows, write_validated_manifest
from enforce_validation_gate import assert_validation_allowed
from generate_preanalysis_validation_report import blocked_analysis_ids


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    CONFIG = yaml.safe_load(handle)


def manifest_row(
    sample_id,
    subject_id,
    group,
    dataset_id="D1",
    gsm_id=None,
    srr_id=None,
    data_type="bulk",
    include="true",
    review_status="confirmed",
):
    return {
        "dataset_id": dataset_id,
        "gse_id": dataset_id,
        "gsm_id": gsm_id or f"GSM_{sample_id}",
        "srx_id": f"SRX_{sample_id}",
        "srr_id": srr_id or f"SRR_{sample_id}",
        "sample_id": sample_id,
        "subject_id": subject_id,
        "include": include,
        "group": group,
        "condition": "condition",
        "tissue": "blood",
        "batch": "B1",
        "sex": "NA",
        "age": "NA",
        "timepoint": "baseline",
        "treatment": "none",
        "paired_group": "NA",
        "data_type": data_type,
        "library_layout": "PAIRED",
        "matrix_path": "NA",
        "fastq_r1": "NA",
        "fastq_r2": "NA",
        "notes": "",
        "reviewer_note": "",
        "review_status": review_status,
    }


def contrast(
    analysis_id="A1",
    numerator="case",
    denominator="control",
    paired="false",
    formula="~ group",
):
    return {
        "contrast_id": "C1",
        "analysis_id": analysis_id,
        "data_scope": "bulk",
        "numerator": numerator,
        "denominator": denominator,
        "subset_column": "NA",
        "subset_value": "NA",
        "design_formula": formula,
        "paired": paired,
        "min_replicates_per_group": "1",
        "enabled": "true",
        "notes": "",
    }


def plan_row(
    dataset_id,
    analysis_id="A1",
    role="discovery",
    strategy="independent_only",
    merge_group="NA",
):
    return {
        "analysis_id": analysis_id,
        "dataset_id": dataset_id,
        "include": "true",
        "role": role,
        "merge_group": merge_group,
        "analysis_strategy": strategy,
        "reference_dataset": "NA",
        "notes": "",
    }


def check_ids(issues):
    return {item["check_id"] for item in issues}


class PreanalysisValidationTests(unittest.TestCase):
    def test_empty_group_is_error(self):
        manifest = [
            manifest_row("S1", "P1", ""),
            manifest_row("S2", "P2", "control"),
        ]
        issues = validate_contrasts(manifest, [contrast()], [plan_row("D1")])
        self.assertIn("GROUP_MISSING", check_ids(issues))

    def test_pending_sample_cannot_be_included(self):
        manifest = [
            manifest_row(
                "S1", "P1", "case", include="true", review_status="pending"
            )
        ]
        issues, _ = validate_manifest_rows(manifest, PROJECT_ROOT)
        self.assertIn("PENDING_SAMPLE_INCLUDED", check_ids(issues))

    def test_subject_group_conflict_is_error(self):
        manifest = [
            manifest_row("S1", "P1", "case"),
            manifest_row("S2", "P1", "control"),
        ]
        issues = validate_contrasts(manifest, [contrast()], [plan_row("D1")])
        self.assertIn("SUBJECT_GROUP_CONFLICT", check_ids(issues))

    def test_contrast_group_must_exist(self):
        manifest = [
            manifest_row("S1", "P1", "case"),
            manifest_row("S2", "P2", "case"),
        ]
        issues = validate_contrasts(manifest, [contrast()], [plan_row("D1")])
        self.assertIn("CONTRAST_GROUP_NOT_FOUND", check_ids(issues))

    def test_incomplete_pair_is_error(self):
        case = manifest_row("S1", "P1", "case")
        control = manifest_row("S2", "P2", "control")
        case["paired_group"] = "PAIR1"
        control["paired_group"] = "PAIR2"
        issues = validate_contrasts(
            [case, control],
            [contrast(paired="true", formula="~ paired_group + group")],
            [plan_row("D1")],
        )
        self.assertIn("INCOMPLETE_PAIR", check_ids(issues))

    def test_dataset_group_complete_confounding_is_critical(self):
        manifest = [
            manifest_row("S1", "P1", "case", dataset_id="D1"),
            manifest_row("S2", "P2", "case", dataset_id="D1"),
            manifest_row("S3", "P3", "control", dataset_id="D2"),
            manifest_row("S4", "P4", "control", dataset_id="D2"),
        ]
        plan = [
            plan_row("D1", strategy="joint_model", merge_group="M1"),
            plan_row("D2", strategy="joint_model", merge_group="M1"),
        ]
        issues = validate_dataset_plan(manifest, [contrast()], plan, CONFIG)
        confounding = [
            item
            for item in issues
            if item["check_id"] == "DATASET_GROUP_COMPLETE_CONFOUNDING"
        ]
        self.assertEqual("critical", confounding[0]["severity"])

    def test_design_matrix_not_full_rank(self):
        manifest = [
            manifest_row("S1", "P1", "case"),
            manifest_row("S2", "P2", "case"),
            manifest_row("S3", "P3", "control"),
            manifest_row("S4", "P4", "control"),
        ]
        for row in manifest:
            row["batch"] = "B_CASE" if row["group"] == "case" else "B_CONTROL"
        issues = validate_design_matrices(
            manifest,
            [contrast(formula="~ group + batch")],
            [plan_row("D1")],
            CONFIG,
        )
        self.assertIn("DESIGN_MATRIX_NOT_FULL_RANK", check_ids(issues))

    def test_validation_dataset_cannot_enter_discovery_model(self):
        manifest = [
            manifest_row("S1", "P1", "case", dataset_id="D1"),
            manifest_row("S2", "P2", "control", dataset_id="D1"),
            manifest_row("S3", "P3", "case", dataset_id="D2"),
            manifest_row("S4", "P4", "control", dataset_id="D2"),
        ]
        plan = [
            plan_row("D1", role="discovery", strategy="joint_model", merge_group="M1"),
            plan_row("D2", role="validation", strategy="joint_model", merge_group="M1"),
        ]
        issues = validate_dataset_plan(manifest, [contrast()], plan, CONFIG)
        self.assertIn("VALIDATION_DATA_IN_DISCOVERY_MODEL", check_ids(issues))

    def test_single_cell_sample_requires_subject_id(self):
        manifest = [
            manifest_row(
                "S1", "NA", "case", data_type="scrna_pseudobulk"
            )
        ]
        sc_contrast = contrast()
        sc_contrast["data_scope"] = "scrna_pseudobulk"
        issues = validate_celltype_ontology(
            manifest,
            [sc_contrast],
            [plan_row("D1")],
            [],
            CONFIG,
            metrics=[],
        )
        self.assertIn("SINGLE_CELL_SUBJECT_ID_MISSING", check_ids(issues))

    def test_count_matrix_column_mismatch_is_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            matrix = Path(temporary) / "counts.tsv"
            matrix.write_text("gene_id\tWRONG\nG1\t1\nG2\t2\n", encoding="utf-8")
            row = manifest_row("S1", "P1", "case")
            row["matrix_path"] = str(matrix)
            issues, _ = validate_manifest_rows([row], PROJECT_ROOT)
        self.assertIn("COUNT_SAMPLE_COLUMNS_MISSING", check_ids(issues))

    def test_duplicate_srr_across_samples_is_critical(self):
        manifest = [
            manifest_row("S1", "P1", "case", srr_id="SRR_DUP"),
            manifest_row("S2", "P2", "control", srr_id="SRR_DUP"),
        ]
        issues, identities = validate_manifest_rows(manifest, PROJECT_ROOT)
        self.assertIn("DUPLICATE_SRR_ID", check_ids(issues))
        self.assertTrue(
            any(item["severity"] == "critical" for item in identities)
        )

    def test_semicolon_srr_overlap_across_samples_is_critical(self):
        manifest = [
            manifest_row("S1", "P1", "case", srr_id="SRR_A;SRR_SHARED"),
            manifest_row("S2", "P2", "control", srr_id="SRR_SHARED;SRR_B"),
        ]
        issues, identities = validate_manifest_rows(manifest, PROJECT_ROOT)
        self.assertIn("DUPLICATE_SRR_ID", check_ids(issues))
        self.assertTrue(
            any(item["check_id"] == "DUPLICATE_SRR_ID" for item in identities)
        )

    def test_paired_fastq_same_file_is_critical(self):
        with tempfile.TemporaryDirectory() as temporary:
            fastq = Path(temporary) / "sample_R1.fastq"
            fastq.write_text("@r\nAC\n+\nII\n", encoding="utf-8")
            row = manifest_row("S1", "P1", "case")
            row["fastq_r1"] = str(fastq)
            row["fastq_r2"] = str(fastq)
            row["matrix_path"] = "NA"
            issues, identities = validate_manifest_rows([row], PROJECT_ROOT)
        self.assertIn("PAIRED_FASTQ_MATES_IDENTICAL", check_ids(issues))
        self.assertIn("FASTQ_PATH_REUSED_WITHIN_SAMPLE", check_ids(identities))

    def test_fastq_path_reused_across_samples_is_critical(self):
        with tempfile.TemporaryDirectory() as temporary:
            r1 = Path(temporary) / "shared_R1.fastq"
            r2a = Path(temporary) / "S1_R2.fastq"
            r2b = Path(temporary) / "S2_R2.fastq"
            for path in (r1, r2a, r2b):
                path.write_text("@r\nAC\n+\nII\n", encoding="utf-8")
            first = manifest_row("S1", "P1", "case")
            second = manifest_row("S2", "P2", "control")
            first["fastq_r1"] = str(r1)
            first["fastq_r2"] = str(r2a)
            second["fastq_r1"] = str(r1)
            second["fastq_r2"] = str(r2b)
            first["matrix_path"] = "NA"
            second["matrix_path"] = "NA"
            issues, identities = validate_manifest_rows([first, second], PROJECT_ROOT)
        self.assertIn("FASTQ_PATH_REUSED_ACROSS_SAMPLES", check_ids(issues))
        self.assertIn("FASTQ_PATH_REUSED_ACROSS_SAMPLES", check_ids(identities))

    def test_validated_output_never_overwrites_user_values(self):
        manifest = [manifest_row("S1", "P1", "case")]
        original = deepcopy(manifest)
        issues, _ = validate_manifest_rows(manifest, PROJECT_ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "validated.tsv"
            write_validated_manifest(output, manifest, issues)
            written = read_tsv(output)[0]
        self.assertEqual(original, manifest)
        for field, value in original[0].items():
            self.assertEqual(value, written[field])

    def test_fractional_count_matrix_is_critical(self):
        with tempfile.TemporaryDirectory() as temporary:
            matrix = Path(temporary) / "counts.tsv"
            matrix.write_text("gene_id\tS1\nG1\t1.5\n", encoding="utf-8")
            row = manifest_row("S1", "P1", "case")
            row["matrix_path"] = str(matrix)
            issues, _ = validate_manifest_rows([row], PROJECT_ROOT)
        fractional = [
            item for item in issues if item["check_id"] == "NON_INTEGER_COUNT_MATRIX"
        ]
        self.assertEqual("critical", fractional[0]["severity"])

    def test_critical_status_blocks_global_gate(self):
        with self.assertRaises(RuntimeError):
            assert_validation_allowed(
                {"critical_block": True, "blocked_analysis_ids": []}
            )

    def test_error_blocks_only_related_analysis_id(self):
        issues = [
            {
                "severity": "error",
                "analysis_id": "A1",
                "dataset_id": "D1",
            }
        ]
        blocked = blocked_analysis_ids(issues, [plan_row("D1")])
        self.assertEqual(["A1"], blocked)
        with self.assertRaises(RuntimeError):
            assert_validation_allowed(
                {"critical_block": False, "blocked_analysis_ids": blocked},
                "A1",
            )
        assert_validation_allowed(
            {"critical_block": False, "blocked_analysis_ids": blocked},
            "A2",
        )


if __name__ == "__main__":
    unittest.main()
