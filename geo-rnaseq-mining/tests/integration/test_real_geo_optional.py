import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(
    os.environ.get("RUN_GEO_NETWORK_TESTS") == "1",
    "Set RUN_GEO_NETWORK_TESTS=1 to enable the real GEO integration test.",
)
class RealGeoIntegrationTest(unittest.TestCase):
    def test_small_geo_accession(self):
        if not shutil.which("Rscript"):
            self.skipTest("Rscript is not available")

        accession = os.environ.get("GEO_TEST_ACCESSION", "GSE100")
        script = PROJECT_ROOT / "workflow" / "scripts" / "fetch_geo_metadata.R"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outputs = {
                "series": root / "geo_series_raw.tsv",
                "samples": root / "geo_samples_raw.tsv",
                "platforms": root / "geo_platforms_raw.tsv",
                "events": root / "events.tsv",
            }
            subprocess.run(
                [
                    "Rscript",
                    str(script),
                    "--accessions",
                    accession,
                    "--series-output",
                    str(outputs["series"]),
                    "--samples-output",
                    str(outputs["samples"]),
                    "--platforms-output",
                    str(outputs["platforms"]),
                    "--event-log",
                    str(outputs["events"]),
                    "--cache-dir",
                    str(root / "cache"),
                    "--retries",
                    "2",
                    "--retry-delay",
                    "1",
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )
            for output in outputs.values():
                self.assertTrue(output.is_file())
                self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
