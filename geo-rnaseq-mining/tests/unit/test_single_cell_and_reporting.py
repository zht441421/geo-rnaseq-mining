import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_project_report import generate_report
from prepare_single_cell_dataset import prepare_single_cell_dataset
from run_cell_proportion import analyze_cell_proportions


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    BASE_CONFIG = yaml.safe_load(handle)


def manifest_row(sample_id, subject_id, group, path):
    return {
        "dataset_id": "GSE_SC",
        "gse_id": "GSE_SC",
        "gsm_id": f"GSM_{sample_id}",
        "srx_id": "NA",
        "srr_id": "NA",
        "sample_id": sample_id,
        "subject_id": subject_id,
        "include": "true",
        "group": group,
        "condition": group,
        "tissue": "blood",
        "batch": "B1",
        "sex": "female",
        "age": "50",
        "timepoint": "baseline",
        "treatment": "none",
        "paired_group": subject_id,
        "data_type": "scrna",
        "library_layout": "NA",
        "matrix_path": str(path),
        "fastq_r1": "NA",
        "fastq_r2": "NA",
        "notes": "",
        "reviewer_note": "",
        "review_status": "confirmed",
    }


def ontology():
    return [
        {
            "dataset_id": "GSE_SC",
            "author_label": "T cell",
            "harmonized_level1": "Immune cell",
            "harmonized_level2": "T cell",
            "harmonized_level3": "T cell",
            "mapping_method": "manual_author_review",
            "confidence": "high",
            "review_status": "confirmed",
            "notes": "",
        }
    ]


def write_h5ad(path, fractional=False, label="T cell"):
    matrix = np.array(
        [
            [1.5 if fractional else 1, 2, 0],
            [3, 1, 1],
        ],
        dtype=float,
    )
    adata = ad.AnnData(
        X=sparse.csr_matrix(matrix),
        obs=pd.DataFrame(
            {"author_label": [label, label]},
            index=["CELL1", "CELL2"],
        ),
        var=pd.DataFrame(index=["GENE1", "GENE2", "MT-GENE3"]),
    )
    adata.layers["counts"] = adata.X.copy()
    adata.write_h5ad(path)


def configured():
    config = copy.deepcopy(BASE_CONFIG)
    config["single_cell"]["qc"] = {
        "min_genes": 0,
        "max_genes": 100,
        "min_counts": 0,
        "max_mito_percent": 100,
    }
    config["single_cell"]["pseudobulk"]["min_cells"] = 1
    config["single_cell"]["normalization"]["highly_variable_genes"] = 3
    config["single_cell"]["normalization"]["pca_components"] = 2
    return config


class SingleCellAndReportingTests(unittest.TestCase):
    def test_raw_cells_are_aggregated_at_subject_level(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = []
            for index, (subject, group) in enumerate(
                (
                    ("P1", "control"),
                    ("P2", "control"),
                    ("P3", "case"),
                    ("P4", "case"),
                ),
                start=1,
            ):
                path = root / f"S{index}.h5ad"
                write_h5ad(path)
                manifest.append(
                    manifest_row(f"S{index}", subject, group, path)
                )
            prepare_single_cell_dataset(
                configured(),
                manifest,
                ontology(),
                "GSE_SC",
                root / "normalized.h5ad",
                root / "cell_qc.tsv",
                root / "celltype_metrics.tsv",
                root / "pseudobulk_counts.tsv",
                root / "pseudobulk_metadata.tsv",
                root / "provenance.json",
            )
            counts = pd.read_csv(root / "pseudobulk_counts.tsv", sep="\t")
            metadata = pd.read_csv(
                root / "pseudobulk_metadata.tsv",
                sep="\t",
            )
            provenance = json.loads(
                (root / "provenance.json").read_text(encoding="utf-8")
            )
        self.assertEqual(4, len(counts.columns) - 1)
        self.assertEqual(4, metadata["subject_id"].nunique())
        self.assertEqual("subject_id", provenance["pseudobulk_level"])
        self.assertEqual(8, provenance["retained_cells"])

    def test_fractional_single_cell_counts_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "fractional.h5ad"
            write_h5ad(path, fractional=True)
            with self.assertRaisesRegex(ValueError, "integer raw counts"):
                prepare_single_cell_dataset(
                    configured(),
                    [manifest_row("S1", "P1", "case", path)],
                    ontology(),
                    "GSE_SC",
                    root / "normalized.h5ad",
                    root / "qc.tsv",
                    root / "metrics.tsv",
                    root / "counts.tsv",
                    root / "metadata.tsv",
                    root / "provenance.json",
                )

    def test_unmapped_author_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "unknown_label.h5ad"
            write_h5ad(path, label="Mystery")
            with self.assertRaisesRegex(ValueError, "lack confirmed ontology"):
                prepare_single_cell_dataset(
                    configured(),
                    [manifest_row("S1", "P1", "case", path)],
                    ontology(),
                    "GSE_SC",
                    root / "normalized.h5ad",
                    root / "qc.tsv",
                    root / "metrics.tsv",
                    root / "counts.tsv",
                    root / "metadata.tsv",
                    root / "provenance.json",
                )

    def test_cell_proportion_uses_subject_level_values(self):
        metadata = [
            {
                "dataset_id": "GSE_SC",
                "subject_id": subject,
                "group": group,
                "author_label": label,
                "cell_count": count,
            }
            for subject, group, label, count in (
                ("P1", "control", "T cell", 2),
                ("P1", "control", "B cell", 8),
                ("P2", "control", "T cell", 3),
                ("P2", "control", "B cell", 7),
                ("P3", "case", "T cell", 8),
                ("P3", "case", "B cell", 2),
                ("P4", "case", "T cell", 7),
                ("P4", "case", "B cell", 3),
            )
        ]
        contrast = {
            "analysis_id": "A1",
            "contrast_id": "case_vs_control",
            "data_scope": "cell_proportion",
            "numerator": "case",
            "denominator": "control",
            "enabled": "true",
        }
        plan = [
            {
                "analysis_id": "A1",
                "dataset_id": "GSE_SC",
                "include": "true",
            }
        ]
        results, proportions = analyze_cell_proportions(
            metadata,
            [contrast],
            plan,
            "GSE_SC",
        )
        t_cell = next(
            row for row in results if row["author_label"] == "T cell"
        )
        self.assertEqual("subject_level_mann_whitney_u", t_cell["test"])
        self.assertGreater(t_cell["proportion_difference"], 0)
        self.assertEqual(4, proportions["subject_id"].nunique())

    def test_report_hashes_results_and_authority_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "results"
            (results / "compatibility").mkdir(parents=True)
            (results / "compatibility" / "validation.tsv").write_text(
                "status\npass\n",
                encoding="utf-8",
            )
            authority = root / "manifest.tsv"
            authority.write_text("sample_id\nS1\n", encoding="utf-8")
            status = root / "status.json"
            status.write_text('{"status":"pass"}\n', encoding="utf-8")
            issue_file = root / "issues.tsv"
            issue_file.write_text(
                "severity\tscope\tcheck_id\tanalysis_id\tdataset_id\tstatus\tmessage\n"
                "warning\ttest\tWARN\tA1\tGSE1\tfail\treview\n",
                encoding="utf-8",
            )
            config = configured()
            generate_report(
                config,
                status,
                [issue_file],
                results,
                [authority],
                results / "reports" / "project_report.html",
                results / "reports" / "manifest.tsv",
                results / "reports" / "provenance.json",
            )
            html = (
                results / "reports" / "project_report.html"
            ).read_text(encoding="utf-8")
            provenance = json.loads(
                (results / "reports" / "provenance.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertIn("Open validation findings", html)
        self.assertEqual(1, provenance["result_file_count"])
        self.assertNotEqual(
            "NA",
            provenance["authority_snapshot"][str(authority)]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()
