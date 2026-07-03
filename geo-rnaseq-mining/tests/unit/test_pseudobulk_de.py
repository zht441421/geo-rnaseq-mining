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

from prepare_single_cell_pseudobulk import prepare_pseudobulk
from pseudobulk_common import (
    pseudobulk_meta_for_contrast,
    validate_joint_preflight,
)


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    BASE_CONFIG = yaml.safe_load(handle)


def config():
    value = copy.deepcopy(BASE_CONFIG)
    value["single_cell"]["pseudobulk"].update(
        {
            "min_cells_per_pseudobulk": 2,
            "min_subjects_per_group": 2,
            "min_total_counts": 5,
            "min_detected_genes": 2,
            "extra_strata": [],
        }
    )
    value["multi_dataset"]["meta"]["min_studies"] = 2
    return value


def ontology(dataset_ids=("GSE1",)):
    rows = []
    for dataset_id in dataset_ids:
        rows.append(
            {
                "dataset_id": dataset_id,
                "author_label": "T cell",
                "harmonized_level1": "Immune",
                "harmonized_level2": "T cell",
                "harmonized_level3": "T cell",
                "mapping_method": "manual",
                "confidence": "high",
                "review_status": "confirmed",
                "notes": "",
            }
        )
    return rows


def clustered(path, rows, counts=None, labels=None):
    counts = counts if counts is not None else np.ones((len(rows), 3), dtype=int) * 2
    labels = labels or ["T cell"] * len(rows)
    obs = pd.DataFrame(rows, index=[f"C{i}" for i in range(len(rows))])
    obs["author_label"] = labels
    var = pd.DataFrame(index=["G1", "G2", "G3"])
    adata = ad.AnnData(X=sparse.csr_matrix(np.log1p(counts)), obs=obs, var=var)
    adata.layers["counts"] = sparse.csr_matrix(counts)
    adata.write_h5ad(path)


def pb_rows(dataset_id, subjects):
    rows = []
    for subject, sample, group in subjects:
        for _ in range(2):
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "sample_id": sample,
                    "subject_id": subject,
                    "group": group,
                    "condition": group,
                    "tissue": "blood",
                    "batch": "B1",
                }
            )
    return rows


def contrast():
    return {
        "analysis_id": "A1",
        "contrast_id": "case_vs_control",
        "data_scope": "scrna_pseudobulk",
        "numerator": "case",
        "denominator": "control",
        "subset_column": "NA",
        "subset_value": "NA",
        "design_formula": "~ group",
        "paired": "false",
        "min_replicates_per_group": "2",
        "enabled": "true",
    }


class PseudobulkDETests(unittest.TestCase):
    def test_missing_subject_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "clustered.h5ad"
            rows = pb_rows("GSE1", [("NA", "S1", "case")])
            clustered(path, rows)
            with self.assertRaisesRegex(ValueError, "subject_id"):
                prepare_pseudobulk(
                    config(), ontology(), "GSE1", path,
                    root / "counts.tsv", root / "metadata.tsv",
                    root / "metrics.tsv", root / "provenance.json",
                )

    def test_cell_type_with_one_case_subject_is_ineligible_for_joint(self):
        metadata = pd.DataFrame(
            {
                "pseudobulk_id": ["PB1", "PB2", "PB3", "PB4", "PB5", "PB6"],
                "dataset_id": ["GSE1", "GSE1", "GSE1", "GSE2", "GSE2", "GSE2"],
                "subject_id": ["P1", "P2", "P3", "P4", "P5", "P6"],
                "sample_id": ["S1", "S2", "S3", "S4", "S5", "S6"],
                "cell_type": ["T cell"] * 6,
                "group": ["control", "control", "case", "control", "control", "case"],
                "cell_count": ["10"] * 6,
                "total_UMI": ["100"] * 6,
                "detected_genes": ["3"] * 6,
                "eligibility": ["eligible"] * 6,
                "exclusion_reason": ["pass"] * 6,
            }
        )
        plan = [
            {"analysis_id": "A1", "dataset_id": "GSE1", "include": "true", "role": "discovery", "analysis_strategy": "joint_model"},
            {"analysis_id": "A1", "dataset_id": "GSE2", "include": "true", "role": "discovery", "analysis_strategy": "joint_model"},
        ]
        with self.assertRaisesRegex(RuntimeError, "insufficient_subjects"):
            validate_joint_preflight(
                metadata,
                plan,
                [contrast()],
                "A1",
                config(),
            )

    def test_cells_below_threshold_are_recorded_ineligible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "clustered.h5ad"
            rows = pb_rows("GSE1", [("P1", "S1", "case")])[:1]
            clustered(path, rows)
            prepare_pseudobulk(
                config(), ontology(), "GSE1", path,
                root / "counts.tsv", root / "metadata.tsv",
                root / "metrics.tsv", root / "provenance.json",
            )
            metadata = pd.read_csv(root / "metadata.tsv", sep="\t")
            provenance = json.loads(
                (root / "provenance.json").read_text(encoding="utf-8")
            )
        self.assertEqual("ineligible", metadata.loc[0, "eligibility"])
        self.assertIn("min_cells_per_pseudobulk", metadata.loc[0, "exclusion_reason"])
        self.assertEqual(1, provenance["ineligible_pseudobulk_count"])
        self.assertEqual(2, provenance["min_cells_per_pseudobulk"])
        self.assertFalse(provenance["cell_replication_used"])

    def test_same_subject_same_group_samples_are_merged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "clustered.h5ad"
            rows = pb_rows(
                "GSE1",
                [("P1", "S1", "case"), ("P1", "S2", "case")],
            )
            clustered(path, rows)
            prepare_pseudobulk(
                config(), ontology(), "GSE1", path,
                root / "counts.tsv", root / "metadata.tsv",
                root / "metrics.tsv", root / "provenance.json",
            )
            counts = pd.read_csv(root / "counts.tsv", sep="\t")
            metadata = pd.read_csv(root / "metadata.tsv", sep="\t")
        self.assertEqual(1, len(metadata))
        self.assertEqual("P1", metadata.loc[0, "subject_id"])
        self.assertEqual("multiple", metadata.loc[0, "sample_id"])
        self.assertEqual("S1;S2", metadata.loc[0, "sample_ids"])
        self.assertEqual(4, metadata.loc[0, "cell_count"])
        self.assertEqual(["gene_id", "PB00001"], list(counts.columns))

    def test_log_matrix_without_counts_layer_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "log_only.h5ad"
            rows = pb_rows("GSE1", [("P1", "S1", "case")])
            obs = pd.DataFrame(rows, index=[f"C{i}" for i in range(len(rows))])
            obs["author_label"] = "T cell"
            ad.AnnData(
                X=sparse.csr_matrix(np.log1p(np.ones((len(rows), 3)))),
                obs=obs,
                var=pd.DataFrame(index=["G1", "G2", "G3"]),
            ).write_h5ad(path)
            with self.assertRaisesRegex(ValueError, "missing layers"):
                prepare_pseudobulk(
                    config(), ontology(), "GSE1", path,
                    root / "counts.tsv", root / "metadata.tsv",
                    root / "metrics.tsv", root / "provenance.json",
                )

    def test_dataset_group_confounding_blocks_joint(self):
        metadata = pd.DataFrame(
            {
                "pseudobulk_id": ["PB1", "PB2", "PB3", "PB4"],
                "dataset_id": ["GSE1", "GSE1", "GSE2", "GSE2"],
                "subject_id": ["C1", "C2", "K1", "K2"],
                "sample_id": ["S1", "S2", "S3", "S4"],
                "cell_type": ["T cell"] * 4,
                "group": ["case", "case", "control", "control"],
                "cell_count": ["10"] * 4,
                "total_UMI": ["100"] * 4,
                "detected_genes": ["3"] * 4,
                "eligibility": ["eligible"] * 4,
                "exclusion_reason": ["pass"] * 4,
            }
        )
        plan = [
            {"analysis_id": "A1", "dataset_id": "GSE1", "include": "true", "role": "discovery", "analysis_strategy": "joint_model"},
            {"analysis_id": "A1", "dataset_id": "GSE2", "include": "true", "role": "discovery", "analysis_strategy": "joint_model"},
        ]
        with self.assertRaisesRegex(RuntimeError, "dataset_group_complete_confounding"):
            validate_joint_preflight(metadata, plan, [contrast()], "A1", config())

    def test_different_subjects_are_not_merged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "clustered.h5ad"
            rows = [
                {"dataset_id": "GSE1", "sample_id": "S1", "subject_id": "P1", "group": "case"},
                {"dataset_id": "GSE1", "sample_id": "S1", "subject_id": "P2", "group": "case"},
            ]
            clustered(path, rows)
            prepare_pseudobulk(
                config(), ontology(), "GSE1", path,
                root / "counts.tsv", root / "metadata.tsv",
                root / "metrics.tsv", root / "provenance.json",
            )
            metadata = pd.read_csv(root / "metadata.tsv", sep="\t")
        self.assertEqual(2, metadata["subject_id"].nunique())
        self.assertEqual(2, len(metadata))

    def test_unconfirmed_cell_type_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "clustered.h5ad"
            clustered(path, pb_rows("GSE1", [("P1", "S1", "case")]), labels=["Mystery", "Mystery"])
            with self.assertRaisesRegex(ValueError, "lack confirmed ontology"):
                prepare_pseudobulk(
                    config(), ontology(), "GSE1", path,
                    root / "counts.tsv", root / "metadata.tsv",
                    root / "metrics.tsv", root / "provenance.json",
                )

    def test_effect_direction_conflict_is_reported_by_meta(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for dataset_id, effect in (("GSE1", 1.0), ("GSE2", -1.0)):
                out = root / dataset_id / "pseudobulk" / "deseq2" / "case_vs_control" / "T_cell"
                out.mkdir(parents=True)
                pd.DataFrame(
                    {
                        "gene_id": ["G1"],
                        "log2FoldChange": [effect],
                        "lfcSE": [0.2],
                        "pvalue": [0.01],
                    }
                ).to_csv(out / "deseq2_full_results.tsv", sep="\t", index=False)
            result = pseudobulk_meta_for_contrast(
                ["GSE1", "GSE2"],
                "case_vs_control",
                "T_cell",
                root,
                config(),
            )
        self.assertEqual("mixed", result[0]["direction_consistency"])
        self.assertEqual(2, result[0]["n_datasets"])

    def test_pseudobulk_r_script_validates_counts_before_coercion(self):
        source = (
            PROJECT_ROOT
            / "workflow"
            / "scripts"
            / "run_single_cell_pseudobulk_deseq2.R"
        ).read_text(encoding="utf-8")
        self.assertIn("validate_pseudobulk_counts <- function", source)
        self.assertIn(
            "Pseudobulk DESeq2 requires finite non-negative integer raw aggregated counts",
            source,
        )
        self.assertLess(
            source.index("validate_pseudobulk_counts(counts_frame)"),
            source.index("rownames(count_matrix) <- counts_frame$gene_id"),
        )


if __name__ == "__main__":
    unittest.main()
