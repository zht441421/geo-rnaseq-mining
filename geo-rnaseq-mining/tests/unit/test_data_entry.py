import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from data_entry_common import (
    classify_local_file,
    classify_remote_candidate,
    inspect_10x_directory,
    inspect_tabular_matrix,
)
from sra_pipeline import (
    fasterq_command,
    fastq_record_count,
    prefetch_command,
    status_is_valid,
)


class DataEntryTests(unittest.TestCase):
    def write_matrix(self, root, name, content):
        path = Path(root) / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_integer_gene_count_matrix(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_matrix(
                temporary,
                "counts.tsv",
                "gene_id\tS1\tS2\nG1\t1\t2\nG2\t0\t3\n",
            )
            result = inspect_tabular_matrix(path, {"S1", "S2"})
        self.assertEqual("raw_integer_counts", result["count_type"])
        self.assertEqual("true", result["is_integer"])
        self.assertEqual("false", result["has_negative"])
        self.assertEqual("true", result["sample_columns_match"])

    def test_tpm_is_exploratory_and_never_deseq2(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_matrix(
                temporary,
                "expression_TPM.tsv",
                "gene_id\tS1\nG1\t1.25\nG2\t2.75\n",
            )
            result = classify_local_file("D1", "S1", "bulk", path, ["S1"])
        self.assertEqual("tpm", result["count_type"])
        self.assertEqual("true", result["likely_normalized"])
        self.assertEqual("exploratory_only_no_deseq2", result["recommended_pipeline"])

    def test_log_transformed_matrix_is_detected_from_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_matrix(
                temporary,
                "matrix.tsv",
                "gene_id\tS1\nG1\t0.25\nG2\t12.75\n",
            )
            result = inspect_tabular_matrix(path, {"S1"})
        self.assertEqual("log_transformed_likely", result["count_type"])
        self.assertEqual("true", result["likely_log_transformed"])

    def test_negative_and_duplicate_gene_ids_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_matrix(
                temporary,
                "matrix.tsv",
                "gene_id\tS1\nG1\t1\nG1\t-2\n",
            )
            result = inspect_tabular_matrix(path, {"S1"})
        self.assertEqual("true", result["has_negative"])
        self.assertEqual(1, result["duplicate_gene_ids"])

    def test_empty_matrix_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_matrix(temporary, "matrix.tsv", "gene_id\tS1\n")
            result = inspect_tabular_matrix(path, {"S1"})
        self.assertTrue(result["empty"])

    def test_sample_column_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_matrix(
                temporary, "matrix.tsv", "gene_id\tWRONG\nG1\t1\n"
            )
            result = inspect_tabular_matrix(path, {"S1"})
        self.assertEqual("false", result["sample_columns_match"])
        self.assertEqual(["S1"], result["missing_sample_columns"])

    def test_10x_directory_requires_content_trio(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "matrix.mtx").write_text(
                "%%MatrixMarket matrix coordinate integer general\n"
                "2 2 2\n1 1 1\n2 2 3\n",
                encoding="utf-8",
            )
            (root / "features.tsv").write_text("G1\tA\nG2\tB\n", encoding="utf-8")
            (root / "barcodes.tsv").write_text("C1\nC2\n", encoding="utf-8")
            result = inspect_10x_directory(root)
        self.assertTrue(result["recognized"])
        self.assertEqual("10x_mtx_directory", result["file_format"])
        self.assertEqual("raw_integer_counts", result["count_type"])

    def test_confirmed_bulk_conflicts_with_10x_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "matrix.mtx").write_text(
                "%%MatrixMarket matrix coordinate integer general\n1 1 1\n1 1 1\n",
                encoding="utf-8",
            )
            (root / "features.tsv").write_text("G1\tA\n", encoding="utf-8")
            (root / "barcodes.tsv").write_text("C1\n", encoding="utf-8")
            result = classify_local_file("D1", "S1", "bulk", root)
        self.assertEqual("single_cell_10x_mtx", result["entry_point"])
        self.assertEqual("error:data_type_file_conflict", result["technical_consistency"])
        self.assertEqual("true", result["requires_manual_review"])

    def test_cellranger_nested_output_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            matrix_dir = root / "outs" / "filtered_feature_bc_matrix"
            matrix_dir.mkdir(parents=True)
            (matrix_dir / "matrix.mtx").write_text(
                "%%MatrixMarket matrix coordinate integer general\n1 1 1\n1 1 2\n",
                encoding="utf-8",
            )
            (matrix_dir / "features.tsv").write_text("G1\tA\n", encoding="utf-8")
            (matrix_dir / "barcodes.tsv").write_text("C1\n", encoding="utf-8")
            result = classify_local_file("D1", "S1", "scrna", root)
        self.assertEqual(
            "single_cell_cellranger_directory", result["entry_point"]
        )
        self.assertEqual("consistent", result["technical_consistency"])

    def test_remote_extension_is_not_treated_as_verified_count(self):
        result = classify_remote_candidate(
            {"file_name": "counts.tsv.gz", "url": "https://example/counts.tsv.gz"}
        )
        self.assertEqual("unverified", result["count_type"])
        self.assertEqual("true", result["requires_manual_review"])

    def test_paired_fasterq_command_uses_split_files(self):
        command = fasterq_command(
            Path("SRR1.sra"), Path("out"), Path("tmp"), 4, paired=True
        )
        self.assertIn("--split-files", command)
        self.assertIn("--threads", command)
        self.assertEqual(
            ["prefetch", "SRR1", "--output-directory", "sra", "--max-size", "10G"],
            prefetch_command("SRR1", Path("sra"), "10G"),
        )

    def test_fastq_integrity_and_verified_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fastq = root / "SRR1.fastq.gz"
            with gzip.open(fastq, "wt", encoding="utf-8") as handle:
                handle.write("@r1\nACGT\n+\n!!!!\n")
            self.assertEqual(1, fastq_record_count(fastq))
            from data_entry_common import sha256_file

            status = root / "status.json"
            status.write_text(
                json.dumps(
                    {
                        "status": "verified",
                        "files": [
                            {"path": str(fastq), "checksum": sha256_file(fastq)}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.assertTrue(status_is_valid(status))


if __name__ == "__main__":
    unittest.main()
