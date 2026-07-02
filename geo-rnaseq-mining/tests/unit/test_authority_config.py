import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
SCHEMA_DIR = PROJECT_ROOT / "workflow" / "schemas"
EXAMPLES = PROJECT_ROOT / "resources" / "examples" / "authority_config"
sys.path.insert(0, str(SCRIPT_DIR))

from authority_config import (
    AuthorityValidationError,
    TABLE_SPECS,
    validate_authority_files,
)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class AuthorityConfigTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.paths = {}
        for table in TABLE_SPECS:
            source = EXAMPLES / f"{table}.example.tsv"
            destination = self.root / f"{table}.tsv"
            shutil.copyfile(source, destination)
            self.paths[table] = destination

    def tearDown(self):
        self.temporary.cleanup()

    def rewrite_rows(self, table, transform):
        path = self.paths[table]
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            headers = reader.fieldnames
            rows = list(reader)
        rows = transform(rows)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=headers, delimiter="\t", lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)

    def assert_error_code(self, expected_code):
        with self.assertRaises(AuthorityValidationError) as context:
            validate_authority_files(self.paths, SCHEMA_DIR)
        codes = {item.code for item in context.exception.issues}
        self.assertIn(expected_code, codes)
        self.assertIn("Suggested action:", str(context.exception))
        return context.exception

    def test_all_json_schemas_are_valid_draft_2020_12(self):
        for schema_name in (
            "sample_manifest.schema.json",
            "contrasts.schema.json",
            "dataset_plan.schema.json",
            "celltype_ontology.schema.json",
        ):
            with self.subTest(schema=schema_name):
                schema = json.loads((SCHEMA_DIR / schema_name).read_text("utf-8"))
                Draft202012Validator.check_schema(schema)

    def test_valid_examples_pass_without_modifying_sources(self):
        before = {name: file_hash(path) for name, path in self.paths.items()}
        result = validate_authority_files(self.paths, SCHEMA_DIR)
        after = {name: file_hash(path) for name, path in self.paths.items()}
        self.assertEqual(before, after)
        self.assertEqual("valid", result["report"]["status"])
        self.assertEqual(1, result["report"]["excluded_samples_preserved"])
        self.assertEqual("CD4 T cell", result["tables"]["celltype_ontology"][0]["author_label"])

    def test_include_true_requires_confirmed_status(self):
        def transform(rows):
            rows[0]["review_status"] = "pending"
            return rows

        self.rewrite_rows("sample_manifest", transform)
        self.assert_error_code("SCHEMA_VIOLATION")

    def test_excluded_row_must_have_include_false(self):
        def transform(rows):
            rows[1]["include"] = "true"
            return rows

        self.rewrite_rows("sample_manifest", transform)
        self.assert_error_code("SCHEMA_VIOLATION")

    def test_duplicate_sample_id_is_rejected_even_when_excluded(self):
        def transform(rows):
            rows[1]["sample_id"] = rows[0]["sample_id"]
            return rows

        self.rewrite_rows("sample_manifest", transform)
        self.assert_error_code("DUPLICATE_SAMPLE_ID")

    def test_pseudobulk_requires_subject_id(self):
        def transform(rows):
            rows[0]["data_type"] = "scrna_pseudobulk"
            rows[0]["subject_id"] = "NA"
            return rows

        self.rewrite_rows("sample_manifest", transform)
        self.assert_error_code("SCHEMA_VIOLATION")

    def test_boolean_values_are_strict_lowercase(self):
        def transform(rows):
            rows[0]["include"] = "TRUE"
            return rows

        self.rewrite_rows("dataset_plan", transform)
        self.assert_error_code("INVALID_BOOLEAN")

    def test_numerator_and_denominator_must_differ(self):
        def transform(rows):
            rows[0]["denominator"] = rows[0]["numerator"]
            return rows

        self.rewrite_rows("contrasts", transform)
        self.assert_error_code("IDENTICAL_CONTRAST_GROUPS")

    def test_unknown_analysis_strategy_is_rejected(self):
        def transform(rows):
            rows[0]["analysis_strategy"] = "auto_switch"
            return rows

        self.rewrite_rows("dataset_plan", transform)
        self.assert_error_code("SCHEMA_VIOLATION")

    def test_extra_column_is_rejected(self):
        path = self.paths["contrasts"]
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[0] += "\tauto_direction"
        lines[1] += "\ttrue"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assert_error_code("HEADER_MISMATCH")


if __name__ == "__main__":
    unittest.main()
