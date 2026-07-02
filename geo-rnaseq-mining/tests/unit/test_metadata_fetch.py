import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from fetch_geo_supplementary_index import collect_entries
from fetch_sra_runinfo import FIELDS as SRA_FIELDS
from fetch_sra_runinfo import collect_runinfo
from metadata_io import fetch_bytes, read_tsv
from prepare_raw_metadata import sha256_file


FIXTURES = PROJECT_ROOT / "tests" / "fixtures"


class MockResponse:
    def __init__(self, content=b"", headers=None):
        self.content = content
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.content


class MetadataFetchTests(unittest.TestCase):
    def test_sra_one_to_many_mapping_is_preserved(self):
        samples = read_tsv(FIXTURES / "mock_geo_samples_raw.tsv")
        runinfo = (FIXTURES / "mock_sra_runinfo.csv").read_bytes()

        def fake_fetcher(*args, **kwargs):
            return runinfo, False, 1

        with tempfile.TemporaryDirectory() as temporary:
            rows, events = collect_runinfo(
                samples,
                temporary,
                retries=3,
                retry_delay=0,
                timeout=1,
                request_interval=0,
                email="",
                api_key="",
                user_agent="test",
                fetcher=fake_fetcher,
            )

        mapped = [row for row in rows if row["gsm_accession"] == "GSMMOCK1"]
        self.assertEqual(["SRR000001", "SRR000002"], [
            row["srr_accession"] for row in mapped
        ])
        unresolved = [row for row in rows if row["gsm_accession"] == "GSMMOCK2"]
        self.assertEqual("NA", unresolved[0]["srx_accession"])
        self.assertTrue(any(event["event_type"] == "NO_SRX_RELATION" for event in events))

    def test_sra_output_has_no_formal_design_fields(self):
        self.assertNotIn("group", SRA_FIELDS)
        self.assertNotIn("subject_id", SRA_FIELDS)
        self.assertNotIn("include", SRA_FIELDS)

    def test_mock_geo_raw_characteristics_remain_verbatim(self):
        samples = read_tsv(FIXTURES / "mock_geo_samples_raw.tsv")
        self.assertIn(
            "disease state: source wording",
            samples[0]["characteristics_ch1_raw"],
        )
        for forbidden in ("group", "subject_id", "include"):
            self.assertNotIn(forbidden, samples[0])

    def test_supplementary_index_uses_raw_metadata_without_download(self):
        series = read_tsv(FIXTURES / "mock_geo_series_raw.tsv")

        def fake_head(request, timeout):
            self.assertEqual("HEAD", request.method)
            return MockResponse(headers={"Content-Length": "12345"})

        with tempfile.TemporaryDirectory() as temporary:
            entries, events = collect_entries(
                series,
                "GSE",
                use_head=True,
                cache_dir=temporary,
                timeout=1,
                user_agent="test",
                retries=2,
                retry_delay=0,
                opener=fake_head,
            )

        self.assertEqual(1, len(entries))
        self.assertEqual("GSEMOCK_counts.tsv.gz", entries[0]["supplementary_file_name"])
        self.assertEqual("12345", entries[0]["size_bytes"])
        self.assertEqual([], events)

    def test_network_fetch_retries_and_reuses_cache(self):
        attempts = {"count": 0}

        def flaky_opener(request, timeout):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise OSError("simulated transient failure")
            return MockResponse(content=b"cached content")

        with tempfile.TemporaryDirectory() as temporary:
            cache_path = Path(temporary) / "response.bin"
            first, first_cache_hit, first_attempt = fetch_bytes(
                "https://example.org/test",
                cache_path,
                retries=3,
                retry_delay=0,
                timeout=1,
                opener=flaky_opener,
            )
            second, second_cache_hit, second_attempt = fetch_bytes(
                "https://example.org/test",
                cache_path,
                retries=3,
                retry_delay=0,
                timeout=1,
                opener=lambda *args, **kwargs: self.fail("cache was not used"),
            )

        self.assertEqual(b"cached content", first)
        self.assertFalse(first_cache_hit)
        self.assertEqual(3, first_attempt)
        self.assertEqual(first, second)
        self.assertTrue(second_cache_hit)
        self.assertEqual(0, second_attempt)

    def test_sha256_matches_file_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "metadata.tsv"
            path.write_bytes(b"a\tb\n1\t2\n")
            observed = sha256_file(path)
        expected = hashlib.sha256(b"a\tb\n1\t2\n").hexdigest()
        self.assertEqual(expected, observed)


if __name__ == "__main__":
    unittest.main()
