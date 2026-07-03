import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from metadata_io import read_tsv, write_tsv
from prepare_data_entry_classification import classify
from prepare_dataset_plan_suggested import build_dataset_plan


class Stage2SuggestedOutputTests(unittest.TestCase):
    def test_dataset_plan_suggested_keeps_formal_fields_blank(self):
        rows = build_dataset_plan(
            [
                {"dataset_id": "GSEMOCK", "gse_id": "GSEMOCK"},
                {"dataset_id": "GSEMOCK", "gse_id": "GSEMOCK"},
            ],
            "analysis_mock",
        )
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("analysis_mock", row["suggested_analysis_id"])
        self.assertEqual("true", row["requires_manual_review"])
        self.assertEqual("", row["analysis_id"])
        self.assertEqual("", row["include"])
        self.assertEqual("", row["analysis_strategy"])
        evidence = json.loads(row["suggestion_evidence"])
        self.assertIn("suggested_analysis_strategy", evidence)

    def test_data_entry_classification_is_suggestion_only(self):
        samples = [{"gse_accession": "GSEMOCK", "gsm_accession": "GSMMOCK1"}]
        runinfo = [
            {
                "gse_accession": "GSEMOCK",
                "gsm_accession": "GSMMOCK1",
                "srr_accession": "SRR000001",
                "library_strategy": "RNA-Seq",
                "library_source": "TRANSCRIPTOMIC",
                "library_layout": "PAIRED",
            }
        ]
        supplementary = [
            {
                "gse_accession": "GSEMOCK",
                "supplementary_file_name": "GSEMOCK_counts_TPM.tsv.gz",
                "supplementary_url": "https://example.org/GSEMOCK_counts_TPM.tsv.gz",
                "file_type": "tsv.gz",
            }
        ]
        rows = classify(samples, runinfo, supplementary)
        entry_points = {row["entry_point_suggested"] for row in rows}
        self.assertIn("bulk_fastq", entry_points)
        self.assertIn("bulk_tpm", entry_points)
        for row in rows:
            self.assertEqual("true", row["requires_manual_review"])
            self.assertNotIn("group", row)
            self.assertNotIn("include", row)
            self.assertNotIn("subject_id", row)

    def test_write_and_read_suggested_classification_headers(self):
        rows = classify(
            [{"gse_accession": "GSEEMPTY", "gsm_accession": "GSMEMPTY"}],
            [],
            [],
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "data_entry_classification.tsv"
            write_tsv(
                output,
                [
                    "dataset_id",
                    "gse_id",
                    "data_type_suggested",
                    "entry_point_suggested",
                    "confidence",
                    "evidence",
                    "requires_manual_review",
                    "recommended_pipeline",
                ],
                rows,
            )
            written = read_tsv(output)
        self.assertEqual("ambiguous", written[0]["entry_point_suggested"])
        self.assertEqual("manual_entry_selection_required", written[0]["recommended_pipeline"])


if __name__ == "__main__":
    unittest.main()
