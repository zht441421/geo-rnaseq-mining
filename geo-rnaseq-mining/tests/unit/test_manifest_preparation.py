import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_metadata_review_report import render_report
from prepare_manifest import (
    FORMAL_FIELDS,
    parse_characteristics,
    prepare_manifest,
    write_manifest,
)


with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    RULES = yaml.safe_load(handle)["metadata_review"]


def sample(
    title="Unresolved sample",
    characteristics="NA",
    gsm="GSMTEST1",
    source_name="source tissue",
):
    return {
        "gse_accession": "GSETEST",
        "gsm_accession": gsm,
        "title": title,
        "source_name": source_name,
        "organism": "Homo sapiens",
        "platform": "GPLTEST",
        "characteristics_ch1_raw": characteristics,
    }


def run(srr="SRRTEST1", layout="PAIRED", gsm="GSMTEST1"):
    return {
        "gse_accession": "GSETEST",
        "gsm_accession": gsm,
        "srx_accession": "SRXTEST1",
        "srr_accession": srr,
        "library_strategy": "RNA-Seq",
        "library_source": "TRANSCRIPTOMIC",
        "library_layout": layout,
    }


class ManifestPreparationTests(unittest.TestCase):
    def prepare(self, samples, runs):
        return prepare_manifest(samples, runs, [], RULES)

    def test_characteristic_with_multiple_colons_splits_only_first(self):
        raw = json.dumps(
            {"characteristics_ch1": ["condition: stage II: recurrent: treated"]}
        )
        parsed = parse_characteristics(raw)
        self.assertEqual("condition", parsed[0][0])
        self.assertEqual("stage II: recurrent: treated", parsed[0][1])

    def test_one_gsm_multiple_srr_remains_multiple_rows(self):
        manifest, conflicts, _ = self.prepare(
            [sample()],
            [run("SRRTEST1"), run("SRRTEST2")],
        )
        self.assertEqual(2, len(manifest))
        self.assertEqual(
            {"GSMTEST1__SRRTEST1", "GSMTEST1__SRRTEST2"},
            {row["suggested_sample_id"] for row in manifest},
        )
        self.assertTrue(
            any(item["conflict_type"] == "MULTIPLE_SRR_FOR_GSM" for item in conflicts)
        )

    def test_conflicting_group_terms_are_flagged_not_confirmed(self):
        manifest, conflicts, _ = self.prepare(
            [sample(title="case and healthy control comparison")],
            [run()],
        )
        self.assertEqual("conflict", manifest[0]["suggested_group"])
        self.assertEqual("", manifest[0]["group"])
        self.assertTrue(
            any(
                item["conflict_type"] == "CONFLICTING_GROUP_TERMS"
                for item in conflicts
            )
        )

    def test_no_group_description_requires_manual_review(self):
        manifest, conflicts, _ = self.prepare(
            [sample(title="RNA library", source_name="blood")],
            [run()],
        )
        self.assertEqual("NA", manifest[0]["suggested_group"])
        self.assertEqual("true", manifest[0]["requires_manual_review"])
        evidence = json.loads(manifest[0]["suggestion_evidence"])
        self.assertIn("No configured group", evidence["suggested_group"]["evidence"]["message"])
        self.assertTrue(
            any(
                item["conflict_type"] == "MISSING_GROUP_EVIDENCE"
                for item in conflicts
            )
        )

    def test_missing_library_layout_is_reported(self):
        _, conflicts, _ = self.prepare([sample()], [run(layout="NA")])
        self.assertTrue(
            any(
                item["conflict_type"] == "MISSING_LIBRARY_LAYOUT"
                for item in conflicts
            )
        )

    def test_technical_replicate_description_does_not_merge_runs(self):
        raw = json.dumps(
            {"characteristics_ch1": ["replicate: technical replicate 2"]}
        )
        manifest, conflicts, _ = self.prepare(
            [sample(characteristics=raw)],
            [run("SRRTEST1"), run("SRRTEST2")],
        )
        self.assertEqual(2, len(manifest))
        self.assertTrue(
            any(
                item["conflict_type"] == "TECHNICAL_REPLICATE_DESCRIPTION"
                for item in conflicts
            )
        )

    def test_suggested_and_formal_fields_are_isolated(self):
        manifest, conflicts, unmapped = self.prepare(
            [sample(title="patient tumor RNA")],
            [run()],
        )
        row = manifest[0]
        self.assertEqual("case_candidate", row["suggested_group"])
        for field in FORMAL_FIELDS:
            expected = "pending" if field == "review_status" else ""
            self.assertEqual(expected, row[field])
        self.assertIn(row["suggestion_confidence"], {"high", "medium", "low"})
        evidence = json.loads(row["suggestion_evidence"])
        for field in (
            "suggested_sample_id",
            "suggested_subject_id",
            "suggested_group",
            "suggested_condition",
            "suggested_tissue",
            "suggested_batch",
            "suggested_data_type",
            "suggested_include",
        ):
            self.assertIn(field, evidence)
            self.assertTrue(evidence[field]["evidence"])
        self.assertEqual([], unmapped)
        report = render_report(manifest, conflicts, unmapped)
        self.assertIn("Suggestions only", report)
        self.assertIn("Formal fields remain blank", report)
        self.assertIn("patient tumor RNA", report)

    def test_written_manifest_preserves_blank_formal_fields(self):
        manifest, _, _ = self.prepare(
            [sample(title="healthy control")],
            [run()],
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample_manifest_suggested.tsv"
            write_manifest(path, manifest)
            with path.open(encoding="utf-8", newline="") as handle:
                written = next(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual("control_candidate", written["suggested_group"])
        self.assertEqual("", written["group"])
        self.assertEqual("", written["subject_id"])
        self.assertEqual("", written["include"])
        self.assertEqual("pending", written["review_status"])


if __name__ == "__main__":
    unittest.main()
