import tempfile
import unittest
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "workflow" / "scripts"))

from dataset_adapters import adapt_path, load_registry


class AdapterContainerCiTests(unittest.TestCase):
    def test_registry_priority_and_disabled_adapter(self):
        registry = load_registry(PROJECT_ROOT / "config" / "adapter_registry.yaml")
        self.assertEqual([row["name"] for row in registry], ["generic_bulk_matrix", "generic_10x"])
        disabled = [dict(row) for row in registry]
        disabled[0]["enabled"] = False
        with tempfile.TemporaryDirectory() as tmp:
            matrix = Path(tmp) / "counts.tsv"
            matrix.write_text("gene_id\tS1\nG1\t10\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                adapt_path(disabled, "D1", "S1", matrix)

    def test_bulk_adapter_flags_tpm_like_matrix(self):
        registry = load_registry(PROJECT_ROOT / "config" / "adapter_registry.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            matrix = Path(tmp) / "expr.tsv"
            matrix.write_text("gene_id\tS1\nG1\t1.5\nG2\t2.5\n", encoding="utf-8")
            row = adapt_path(registry, "D1", "S1", matrix)
            self.assertEqual(row["adapter"], "generic_bulk_matrix")
            self.assertEqual(row["likely_normalized"], "true")
            self.assertIn("likely_normalized", row["technical_consistency"])

    def test_10x_adapter_detects_missing_files(self):
        registry = load_registry(PROJECT_ROOT / "config" / "adapter_registry.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "matrix.mtx").write_text("%%MatrixMarket matrix coordinate integer general\n", encoding="utf-8")
            row = adapt_path(registry, "D1", "S1", path)
            self.assertEqual(row["adapter"], "generic_10x")
            self.assertIn("missing_10x_files", row["technical_consistency"])
            self.assertEqual(row["requires_manual_review"], "true")

    def test_container_and_ci_static_files_exist(self):
        files = [
            PROJECT_ROOT / "containers" / "Dockerfile",
            PROJECT_ROOT / "containers" / "apptainer.def",
            PROJECT_ROOT / "containers" / "build_docker.ps1",
            PROJECT_ROOT / "containers" / "build_apptainer.sh",
            PROJECT_ROOT / "profiles" / "container" / "config.yaml",
            PROJECT_ROOT / ".github" / "workflows" / "ci.yml",
        ]
        for path in files:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
