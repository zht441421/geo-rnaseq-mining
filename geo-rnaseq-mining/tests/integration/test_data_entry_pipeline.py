import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT_ROOT / "workflow" / "scripts"


class DataEntryPipelineIntegrationTest(unittest.TestCase):
    def test_offline_manifest_to_final_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            matrix = root / "counts.tsv"
            matrix.write_text("gene_id\tS1\nG1\t1\nG2\t2\n", encoding="utf-8")
            manifest = root / "manifest.tsv"
            headers = [
                "dataset_id", "gse_id", "gsm_id", "srx_id", "srr_id",
                "sample_id", "subject_id", "include", "group", "condition",
                "tissue", "batch", "sex", "age", "timepoint", "treatment",
                "paired_group", "data_type", "library_layout", "matrix_path",
                "fastq_r1", "fastq_r2", "notes", "reviewer_note", "review_status",
            ]
            row = {field: "NA" for field in headers}
            row.update(
                {
                    "dataset_id": "D1",
                    "gse_id": "GSE1",
                    "gsm_id": "GSM1",
                    "sample_id": "S1",
                    "subject_id": "P1",
                    "include": "true",
                    "group": "case",
                    "data_type": "bulk",
                    "library_layout": "PAIRED",
                    "matrix_path": str(matrix),
                    "review_status": "confirmed",
                }
            )
            with manifest.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=headers, delimiter="\t", lineterminator="\n"
                )
                writer.writeheader()
                writer.writerow(row)
            supplementary = root / "supplementary.tsv"
            supplementary.write_text(
                "gse_accession\tgsm_accession\tsource_scope\traw_metadata_key\t"
                "supplementary_file_name\tsupplementary_url\tsize_bytes\tfile_type\tfetched_at_utc\n",
                encoding="utf-8",
            )
            supp_inventory = root / "supp_inventory.tsv"
            classified = root / "classified.tsv"
            supplement_status = root / "supp_status.tsv"
            verified = root / "verified.tsv"
            final = root / "data_inventory.tsv"
            commands = [
                [
                    sys.executable,
                    str(SCRIPTS / "inventory_supplementary_files.py"),
                    "--manifest", str(manifest),
                    "--supplementary", str(supplementary),
                    "--output", str(supp_inventory),
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "classify_data_entry.py"),
                    "--manifest", str(manifest),
                    "--supplementary-inventory", str(supp_inventory),
                    "--project-root", str(root),
                    "--output", str(classified),
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "download_supplementary_files.py"),
                    "--config", str(PROJECT_ROOT / "config" / "config.yaml"),
                    "--inventory", str(supp_inventory),
                    "--project-root", str(root),
                    "--output", str(supplement_status),
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "verify_downloads.py"),
                    "--manifest", str(manifest),
                    "--supplementary-status", str(supplement_status),
                    "--output", str(verified),
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "build_data_inventory.py"),
                    "--classified", str(classified),
                    "--verified", str(verified),
                    "--output", str(final),
                ],
            ]
            for command in commands:
                subprocess.run(command, check=True, cwd=PROJECT_ROOT)
            with final.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(1, len(rows))
        self.assertEqual("bulk_gene_count_matrix", rows[0]["entry_point"])
        self.assertEqual("raw_integer_counts", rows[0]["count_type"])
        self.assertEqual("bulk", rows[0]["data_type_confirmed"])


if __name__ == "__main__":
    unittest.main()
