import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "workflow" / "scripts" / "sra_pipeline.py"


@unittest.skipUnless(
    os.environ.get("RUN_SRA_NETWORK_TESTS") == "1",
    "Set RUN_SRA_NETWORK_TESTS=1 and SRA_TEST_ACCESSION to enable.",
)
class OptionalSraIntegrationTest(unittest.TestCase):
    def test_prefetch_fasterq_and_integrity(self):
        accession = os.environ.get("SRA_TEST_ACCESSION")
        if not accession:
            self.skipTest("SRA_TEST_ACCESSION is not set")
        for executable in ("prefetch", "vdb-validate", "fasterq-dump", "pigz"):
            if not shutil.which(executable):
                self.skipTest(f"{executable} is not available")
        layout = os.environ.get("SRA_TEST_LAYOUT", "SINGLE")
        max_size = os.environ.get("SRA_TEST_MAX_SIZE", "100M")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefetch_status = root / "prefetch.json"
            fastq_status = root / "fasterq.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "prefetch",
                    "--srr",
                    accession,
                    "--output-dir",
                    str(root / "sra"),
                    "--status",
                    str(prefetch_status),
                    "--max-size",
                    max_size,
                    "--retries",
                    "2",
                    "--retry-delay",
                    "2",
                    "--enabled",
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "fasterq",
                    "--srr",
                    accession,
                    "--layout",
                    layout,
                    "--prefetch-status",
                    str(prefetch_status),
                    "--output-dir",
                    str(root / "fastq"),
                    "--temp-dir",
                    str(root / "tmp"),
                    "--status",
                    str(fastq_status),
                    "--threads",
                    "2",
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )
            status = json.loads(fastq_status.read_text(encoding="utf-8"))
            self.assertEqual("verified", status["status"])
            self.assertTrue(status["files"])


if __name__ == "__main__":
    unittest.main()
