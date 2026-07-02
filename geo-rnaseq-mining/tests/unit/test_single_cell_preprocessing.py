import copy
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

from preprocess_single_cell_dataset import add_suggested_annotations
from single_cell_common import (
    calculate_preprocessing_qc,
    cluster_single_cell_object,
    create_post_qc_object,
    load_single_cell_preprocessing_dataset,
    read_single_cell_entry,
)


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    BASE_CONFIG = yaml.safe_load(handle)


def permissive_config():
    config = copy.deepcopy(BASE_CONFIG)
    config["single_cell"]["qc"]["strategy"] = "hard"
    config["single_cell"]["qc"]["hard"].update(
        {
            "min_genes": 0,
            "max_genes": 100000,
            "min_counts": 0,
            "max_counts": None,
            "max_pct_mt": 100,
            "max_pct_ribo": 100,
            "max_pct_hb": 100,
            "min_complexity": 0,
        }
    )
    config["single_cell"]["qc"]["mad"]["enabled"] = False
    config["single_cell"]["doublet"]["enabled"] = False
    config["single_cell"]["normalization"]["highly_variable_genes"] = 3
    config["single_cell"]["normalization"]["pca_components"] = 2
    return config


def manifest_row(sample_id, subject_id, path):
    return {
        "dataset_id": "GSE_SC",
        "gse_id": "GSE_SC",
        "gsm_id": f"GSM_{sample_id}",
        "sample_id": sample_id,
        "subject_id": subject_id,
        "include": "true",
        "group": "case",
        "condition": "case",
        "tissue": "blood",
        "batch": "B1",
        "data_type": "scrna",
        "matrix_path": str(path),
        "review_status": "confirmed",
    }


def write_h5ad(path, matrix=None, barcodes=None, with_counts=True):
    matrix = np.asarray(
        matrix
        if matrix is not None
        else [[1, 2, 0], [3, 1, 1]],
        dtype=float,
    )
    barcodes = barcodes or [f"CELL{i + 1}" for i in range(matrix.shape[0])]
    adata = ad.AnnData(
        X=sparse.csr_matrix(matrix),
        obs=pd.DataFrame(index=barcodes),
        var=pd.DataFrame(
            {"gene_symbol": ["RPS1", "HBA1", "MT-GENE3"][: matrix.shape[1]]},
            index=["GENE1", "GENE2", "GENE3"][: matrix.shape[1]],
        ),
    )
    if with_counts:
        adata.layers["counts"] = adata.X.copy()
    adata.write_h5ad(path)


def contract_adata(sample_totals):
    rows = []
    sample_ids = []
    for sample_id, totals in sample_totals.items():
        for total in totals:
            rows.append([total, 0, 0])
            sample_ids.append(sample_id)
    matrix = sparse.csr_matrix(np.asarray(rows, dtype=int))
    obs = pd.DataFrame(index=[f"C{i}" for i in range(len(rows))])
    obs["dataset_id"] = "GSE_SC"
    obs["gse_id"] = "GSE_SC"
    obs["sample_id"] = sample_ids
    obs["subject_id"] = [f"P_{sample}" for sample in sample_ids]
    obs["group"] = "case"
    obs["batch"] = "B1"
    obs["technology"] = "scrna"
    obs["tissue"] = "blood"
    obs["condition"] = "case"
    obs["original_barcode"] = obs.index
    obs["author_label"] = "manual_label"
    var = pd.DataFrame(index=["G1", "G2", "G3"])
    var["gene_id_original"] = var.index
    var["gene_id_canonical"] = var.index
    var["gene_symbol"] = ["GENE1", "GENE2", "MT-GENE3"]
    var["reference_build"] = "test"
    var["mapping_status"] = "identity"
    adata = ad.AnnData(X=matrix.copy(), obs=obs, var=var)
    adata.layers["counts"] = matrix.copy()
    return adata


class SingleCellPreprocessingTests(unittest.TestCase):
    def test_duplicate_barcode_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.h5ad"
            write_h5ad(path, barcodes=["CELL1", "CELL1"])
            with self.assertRaisesRegex(ValueError, "duplicate cell barcodes"):
                read_single_cell_entry(path, "counts", permissive_config())

    def test_missing_subject_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.h5ad"
            write_h5ad(path)
            with self.assertRaisesRegex(ValueError, "requires subject_id"):
                load_single_cell_preprocessing_dataset(
                    [manifest_row("S1", "NA", path)],
                    permissive_config(),
                    "GSE_SC",
                )

    def test_missing_counts_layer_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing_counts.h5ad"
            write_h5ad(path, with_counts=False)
            with self.assertRaisesRegex(ValueError, "missing required raw counts"):
                read_single_cell_entry(path, "counts", permissive_config())

    def test_fractional_raw_counts_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fractional.h5ad"
            write_h5ad(path, matrix=[[1.5, 0, 1], [2, 1, 0]])
            with self.assertRaisesRegex(ValueError, "integer raw counts"):
                read_single_cell_entry(path, "counts", permissive_config())

    def test_qc_thresholds_are_calculated_per_sample(self):
        config = permissive_config()
        config["single_cell"]["qc"]["strategy"] = "mad"
        config["single_cell"]["qc"]["mad"].update(
            {
                "enabled": True,
                "min_cells": 3,
                "metrics": ["total_counts"],
            }
        )
        adata = contract_adata({"S1": [10, 11, 100], "S2": [1000, 1100, 1200]})
        result = calculate_preprocessing_qc(adata, config)
        thresholds = result["thresholds"]
        total = thresholds.loc[thresholds["metric"] == "total_counts"]
        self.assertEqual({"S1", "S2"}, set(total["sample_id"]))
        self.assertEqual(2, total["effective_upper"].nunique())

    def test_doublet_detection_runs_by_sample(self):
        config = permissive_config()
        config["single_cell"]["doublet"].update(
            {"enabled": True, "method": "scrublet", "min_cells": 2}
        )
        adata = contract_adata({"S1": [10, 11], "S2": [20, 21]})
        calls = []

        def detector(sample, sample_id, method):
            calls.append((sample_id, sample.n_obs, method))
            return np.zeros(sample.n_obs), np.zeros(sample.n_obs, dtype=bool)

        calculate_preprocessing_qc(adata, config, detector=detector)
        self.assertEqual(
            [("S1", 2, "scrublet"), ("S2", 2, "scrublet")],
            calls,
        )

    def test_clustering_never_overwrites_raw_counts(self):
        config = permissive_config()
        adata = contract_adata({"S1": [10, 11]})
        retained = pd.Series(True, index=adata.obs_names)
        post = create_post_qc_object(adata, retained)
        expected = post.layers["counts"].copy()
        clustered = cluster_single_cell_object(post, config)
        self.assertTrue((clustered.layers["counts"] != expected).nnz == 0)
        self.assertFalse((clustered.X != expected).nnz == 0)

    def test_suggested_annotation_does_not_replace_author_label(self):
        config = permissive_config()
        adata = contract_adata({"S1": [10, 11]})
        adata.obs["leiden"] = pd.Categorical(["0", "0"])
        original = adata.obs["author_label"].copy()
        markers = pd.DataFrame(
            columns=["cluster", "gene_symbol", "gene_id_original"]
        )
        add_suggested_annotations(adata, markers, config)
        self.assertTrue(adata.obs["author_label"].equals(original))
        self.assertTrue((adata.obs["suggested_annotation"] == "unassigned").all())


if __name__ == "__main__":
    unittest.main()
