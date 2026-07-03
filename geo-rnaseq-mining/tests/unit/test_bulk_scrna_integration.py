import copy
import sys
import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from run_bulk_scrna_integration import integrate_bulk_scrna


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    BASE_CONFIG = yaml.safe_load(handle)


def config():
    value = copy.deepcopy(BASE_CONFIG)
    value["bulk_scrna_integration"]["dominant_celltype_min_delta"] = 0.05
    return value


def ontology():
    return [
        {
            "dataset_id": "GSE1",
            "author_label": "T cell",
            "harmonized_level2": "T cell",
            "review_status": "confirmed",
        },
        {
            "dataset_id": "GSE1",
            "author_label": "B cell",
            "harmonized_level2": "B cell",
            "review_status": "confirmed",
        },
    ]


def base_tables():
    bulk = [
        {
            "gene_id": "G1",
            "gene_symbol": "GENE1",
            "dataset_id": "GSE1",
            "log2FoldChange": "1.0",
            "padj": "0.001",
        },
        {
            "gene_id": "G1",
            "gene_symbol": "GENE1",
            "dataset_id": "GSE2",
            "log2FoldChange": "0.8",
            "padj": "0.01",
        },
    ]
    pseudobulk = [
        {
            "gene_id": "G1",
            "gene_symbol": "GENE1",
            "dataset_id": "GSE1",
            "cell_type": "T cell",
            "log2FoldChange": "0.7",
            "padj": "0.01",
        }
    ]
    avg = [
        {
            "gene_id": "G1",
            "gene_symbol": "GENE1",
            "cell_type": "T cell",
            "average_expression": "10",
        },
        {
            "gene_id": "G1",
            "gene_symbol": "GENE1",
            "cell_type": "B cell",
            "average_expression": "2",
        },
    ]
    prop = [
        {
            "gene_id": "G1",
            "cell_type": "T cell",
            "expression_cell_fraction": "0.9",
        },
        {
            "gene_id": "G1",
            "cell_type": "B cell",
            "expression_cell_fraction": "0.2",
        },
    ]
    return bulk, pseudobulk, avg, prop


def run_case(
    bulk=None,
    pseudobulk=None,
    avg=None,
    prop=None,
    mapping=None,
    loo=None,
    validation=None,
):
    default_bulk, default_pb, default_avg, default_prop = base_tables()
    return integrate_bulk_scrna(
        config(),
        default_bulk if bulk is None else bulk,
        [],
        default_pb if pseudobulk is None else pseudobulk,
        [],
        [],
        default_avg if avg is None else avg,
        default_prop if prop is None else prop,
        [],
        [] if loo is None else loo,
        [] if validation is None else validation,
        ontology(),
        [] if mapping is None else mapping,
    )


class BulkScrnaIntegrationTests(unittest.TestCase):
    def test_gene_id_one_to_many_is_reported_not_silently_merged(self):
        tables = run_case(
            bulk=[
                {
                    "gene_id": "ALIAS1",
                    "dataset_id": "GSE1",
                    "log2FoldChange": "1",
                    "padj": "0.01",
                }
            ],
            avg=[{"gene_id": "ALIAS1", "cell_type": "T cell", "average_expression": "5"}],
            prop=[{"gene_id": "ALIAS1", "cell_type": "T cell", "expression_cell_fraction": "0.5"}],
            mapping=[
                {
                    "original_gene_id": "ALIAS1",
                    "canonical_gene_id": "GENEA",
                    "gene_symbol": "A",
                },
                {
                    "original_gene_id": "ALIAS1",
                    "canonical_gene_id": "GENEB",
                    "gene_symbol": "B",
                },
            ],
        )
        statuses = {row["mapping_status"] for row in tables["unmapped_genes.tsv"]}
        self.assertIn("ambiguous_one_to_many", statuses)
        canonical = {row["canonical_gene_id"] for row in tables["gene_celltype_mapping.tsv"]}
        self.assertTrue({"GENEA", "GENEB"}.issubset(canonical))

    def test_bulk_and_pseudobulk_opposite_direction_is_flagged(self):
        pb = copy.deepcopy(base_tables()[1])
        pb[0]["log2FoldChange"] = "-0.7"
        tables = run_case(pseudobulk=pb)
        consistency = {
            row["effect_direction_consistency"]
            for row in tables["bulk_scrna_concordance.tsv"]
            if row["cell_type"] == "T cell"
        }
        self.assertIn("opposite", consistency)
        limitations = tables["candidate_gene_scores.tsv"][0]["limitations"]
        self.assertIn("bulk_pseudobulk_opposite_direction", limitations)
        self.assertEqual("limited", tables["candidate_gene_scores.tsv"][0]["confidence"])

    def test_single_gse_support_is_limited_and_dataset_driven(self):
        bulk = [base_tables()[0][0]]
        tables = run_case(bulk=bulk, pseudobulk=[])
        score = tables["candidate_gene_scores.tsv"][0]
        self.assertEqual("true", score["dataset_driven"])
        self.assertIn("single_gse_support", score["limitations"])
        self.assertEqual("limited", score["confidence"])

    def test_candidate_scores_are_not_final_biological_conclusions(self):
        tables = run_case()
        score = tables["candidate_gene_scores.tsv"][0]
        self.assertEqual("false", score["is_final_biological_conclusion"])
        self.assertEqual("human_review_required", score["required_action"])

    def test_ambiguous_dominant_cell_type_is_not_overstated(self):
        avg = [
            {"gene_id": "G1", "cell_type": "T cell", "average_expression": "10"},
            {"gene_id": "G1", "cell_type": "B cell", "average_expression": "9.8"},
        ]
        tables = run_case(avg=avg)
        dominant = {row["dominant_cell_type"] for row in tables["bulk_scrna_concordance.tsv"]}
        self.assertEqual({"ambiguous"}, dominant)
        notes = {row["dominant_cell_type_note"] for row in tables["gene_celltype_mapping.tsv"]}
        self.assertIn("ambiguous_dominant_cell_type", notes)

    def test_validation_failure_limits_confidence(self):
        tables = run_case(
            validation=[
                {
                    "gene_id": "G1",
                    "replication_status": "direction_mismatch",
                }
            ]
        )
        score = tables["candidate_gene_scores.tsv"][0]
        self.assertIn("validation_failed", score["limitations"])
        self.assertEqual("limited", score["confidence"])

    def test_dataset_driven_candidate_uses_loo_evidence(self):
        tables = run_case(
            loo=[
                {
                    "gene_id": "G1",
                    "dataset_driven": "true",
                }
            ]
        )
        score = tables["candidate_gene_scores.tsv"][0]
        self.assertEqual("true", score["dataset_driven"])
        self.assertEqual(0.0, score["loo_stability_score"])

    def test_missing_cell_type_is_explicitly_recorded(self):
        avg = [{"gene_id": "G1", "cell_type": "T cell", "average_expression": "10"}]
        prop = [{"gene_id": "G1", "cell_type": "T cell", "expression_cell_fraction": "0.8"}]
        tables = run_case(avg=avg, prop=prop)
        missing_rows = [
            row for row in tables["gene_celltype_mapping.tsv"]
            if row["cell_type"] == "B cell"
        ]
        self.assertTrue(missing_rows)
        self.assertEqual("missing_cell_type", missing_rows[0]["dominant_cell_type_note"])


if __name__ == "__main__":
    unittest.main()
