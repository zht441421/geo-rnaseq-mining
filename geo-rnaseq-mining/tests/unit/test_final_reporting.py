import argparse
import csv
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "workflow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from final_reporting import (
    build_audit_trail,
    collect_reference_metadata,
    package_results,
    render_analysis_report,
    render_methods_report,
    write_test_status,
)


def read_tsv(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class FinalReportingTest(unittest.TestCase):
    def test_audit_trail_preserves_reviewed_values_and_exclusions(self):
        with mock.patch("final_reporting.git_version", return_value="test-version"):
            root = self._tmp()
            authority = root / "authority.tsv"
            authority.write_text(
                "sample_id\tgroup_raw\tgroup_suggested\tgroup\tinclude\texclusion_reason\treview_status\treviewer_note\tmodified_at\n"
                "S1\tcase?\tcase\tcase\tfalse\tmanual exclusion\tconfirmed\tchecked by reviewer\t2026-07-02T00:00:00Z\n",
                encoding="utf-8",
            )
            issues = root / "issues.tsv"
            issues.write_text(
                "severity\tscope\tcheck_id\tanalysis_id\tdataset_id\tmessage\n"
                "warning\tmanifest\tmissing_optional\tA1\tGSE1\toptional field absent\n",
                encoding="utf-8",
            )

            build_audit_trail(
                argparse.Namespace(
                    authority_files=[str(authority)],
                    issue_files=[str(issues)],
                    audit=str(root / "audit.tsv"),
                    exclusions=str(root / "exclusions.tsv"),
                    warnings=str(root / "warnings.tsv"),
                    marker=str(root / ".complete"),
                )
            )

            audit = read_tsv(root / "audit.tsv")
            group_rows = [row for row in audit if row["field"] == "group"]
            self.assertEqual(group_rows[0]["original_value"], "case?")
            self.assertEqual(group_rows[0]["suggested_value"], "case")
            self.assertEqual(group_rows[0]["final_user_value"], "case")
            self.assertEqual(group_rows[0]["review_status"], "confirmed")
            self.assertEqual(group_rows[0]["pipeline_version"], "test-version")
            exclusions = read_tsv(root / "exclusions.tsv")
            self.assertEqual(exclusions[0]["reason"], "manual exclusion")
            warnings = read_tsv(root / "warnings.tsv")
            self.assertEqual(warnings[0]["message"], "optional field absent")

    def test_package_excludes_large_raw_sequence_files(self):
        root = self._tmp()
        result_root = root / "results"
        result_root.mkdir()
        (result_root / "table.tsv").write_text("gene\tpadj\nA\t0.01\n", encoding="utf-8")
        (result_root / "reads.fastq.gz").write_bytes(b"not real fastq")
        package = root / "reports" / "result_package.tar.gz"
        manifest = root / "reports" / "result_package_manifest.tsv"
        marker = root / "reports" / ".complete"

        package_results(
            argparse.Namespace(
                roots=[str(result_root)],
                output=str(package),
                manifest=str(manifest),
                marker=str(marker),
            )
        )

        rows = {Path(row["path"]).name: row for row in read_tsv(manifest)}
        self.assertEqual(rows["table.tsv"]["included"], "true")
        self.assertEqual(rows["reads.fastq.gz"]["included"], "false")
        self.assertEqual(rows["reads.fastq.gz"]["reason"], "excluded_large_raw_sequence_file")
        with tarfile.open(package, "r:gz") as archive:
            names = archive.getnames()
        self.assertTrue(any(name.endswith("table.tsv") for name in names))
        self.assertFalse(any(name.endswith("reads.fastq.gz") for name in names))

    def test_default_test_status_records_do_not_claim_passed(self):
        root = self._tmp()
        write_test_status(
            argparse.Namespace(
                output=str(root / "test_status.tsv"),
                marker=str(root / "test_status.complete"),
            )
        )

        rows = read_tsv(root / "test_status.tsv")
        self.assertGreaterEqual(len(rows), 4)
        self.assertTrue(all(row["result"] != "passed" for row in rows))
        self.assertTrue(any(row["scope"] == "real_geo_sra_network" for row in rows))
        self.assertTrue(
            any(row["status"] == "opt_in_not_run_by_default" for row in rows)
        )

    def test_reports_state_unconfirmed_fields_are_not_facts(self):
        root = self._tmp()
        config = {
            "project": {"name": "demo", "description": "Demo association study"},
            "reporting": {"title": "Demo Report"},
            "references": {"gtf": str(root / "missing.gtf")},
        }
        config_path = root / "config.yaml"
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        manifest = root / "manifest.tsv"
        manifest.write_text(
            "dataset_id\tsample_id\treview_status\tinclude\nGSE1\tS1\tpending\ttrue\n",
            encoding="utf-8",
        )
        contrasts = root / "contrasts.tsv"
        contrasts.write_text(
            "analysis_id\tcontrast_id\tdata_scope\tnumerator\tdenominator\tdesign_formula\tenabled\n"
            "A1\tC1\tbulk\tcase\tcontrol\t~ group\ttrue\n",
            encoding="utf-8",
        )
        plan = root / "dataset_plan.tsv"
        plan.write_text(
            "analysis_id\tdataset_id\tinclude\trole\tanalysis_strategy\treference_dataset\n"
            "A1\tGSE1\ttrue\tdiscovery\tper_dataset\tNA\n",
            encoding="utf-8",
        )
        empty = root / "empty.tsv"
        empty.write_text("severity\tscope\tcheck_id\tanalysis_id\tdataset_id\tmessage\n", encoding="utf-8")
        software = root / "software_versions.tsv"
        software.write_text(
            "software\tversion\tsource\tcommand\npython\tPython 3.12\truntime\tpython --version\n",
            encoding="utf-8",
        )
        checksums = root / "file_checksums.tsv"
        checksums.write_text(
            "path\tmodule\tsize_bytes\tsha256\tmodified_utc\nraw/counts.tsv\tper_dataset\t12\tabc123\t2026-07-02T00:00:00Z\n",
            encoding="utf-8",
        )
        audit = root / "audit.tsv"
        audit.write_text(
            "field\trecord_id\toriginal_value\tsuggested_value\tfinal_user_value\treview_status\treviewer_note\tmodification_timestamp\tsource_file\tpipeline_version\n"
            "group\tS1\tcase?\tcase\tcase\tconfirmed\tchecked\t2026-07-02T00:00:00Z\tmanifest.tsv\ttest\n",
            encoding="utf-8",
        )

        collect_reference_metadata(
            argparse.Namespace(
                config=str(config_path),
                output=str(root / "reference_versions.tsv"),
                marker=str(root / "references.complete"),
            )
        )
        render_analysis_report(
            argparse.Namespace(
                config=str(config_path),
                manifest=str(manifest),
                contrasts=str(contrasts),
                dataset_plan=str(plan),
                warnings=str(empty),
                exclusions=str(root / "exclusions.tsv"),
                software=str(software),
                references=str(root / "reference_versions.tsv"),
                checksums=str(checksums),
                audit=str(audit),
                validation_report=None,
                validation_output=None,
                output=str(root / "analysis_report.html"),
                marker=str(root / "analysis.complete"),
            )
        )
        html = (root / "analysis_report.html").read_text(encoding="utf-8")
        self.assertIn("Suggestions are not facts", html)
        self.assertIn("no tests are reported as passed", html)
        self.assertIn("potential cellular source only", html)
        self.assertIn("Each contrast", html)
        self.assertIn("Design formula", html)
        self.assertIn("Python 3.12", html)
        self.assertIn("raw/counts.tsv", html)
        self.assertIn("case?", html)
        self.assertIn("Reference genome and GTF", html)
        self.assertNotIn(" driver ", html.lower())
        self.assertNotIn(" mechanism", html.lower())

    def test_report_surfaces_candidate_and_annotation_review_limits(self):
        root = self._tmp()
        config = {
            "project": {"name": "demo", "description": "Demo association study"},
            "reporting": {"title": "Demo Report"},
            "references": {},
        }
        config_path = root / "config.yaml"
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        manifest = root / "manifest.tsv"
        manifest.write_text(
            "dataset_id\tsample_id\treview_status\tinclude\nGSE1\tS1\tconfirmed\ttrue\n",
            encoding="utf-8",
        )
        contrasts = root / "contrasts.tsv"
        contrasts.write_text(
            "analysis_id\tcontrast_id\tdata_scope\tnumerator\tdenominator\tdesign_formula\tpaired\tenabled\n"
            "A1\tC1\tbulk\tcase\tcontrol\t~ group\tfalse\ttrue\n",
            encoding="utf-8",
        )
        plan = root / "dataset_plan.tsv"
        plan.write_text(
            "analysis_id\tdataset_id\tinclude\trole\tanalysis_strategy\treference_dataset\n"
            "A1\tGSE1\ttrue\tdiscovery\tper_dataset\tNA\n",
            encoding="utf-8",
        )
        warnings = root / "warnings.tsv"
        warnings.write_text(
            "severity\tscope\tcheck_id\tanalysis_id\tdataset_id\tmessage\n",
            encoding="utf-8",
        )
        candidate_scores = root / "candidate_gene_scores.tsv"
        candidate_scores.write_text(
            "canonical_gene_id\tbest_bulk_log2fc\tbest_pseudobulk_log2fc\tbulk_pseudobulk_direction\tdominant_cell_type\tlimitations\tdataset_driven\tconfidence\tis_final_biological_conclusion\trequired_action\n"
            "GENE1\t1.2\t-0.8\topposite\tT cell\tbulk_pseudobulk_opposite_direction;single_gse_support\ttrue\tlimited\tfalse\thuman_review_required\n",
            encoding="utf-8",
        )
        suggestions = root / "suggested_annotations.tsv"
        suggestions.write_text(
            "cluster\tsuggested_label\treview_status\tis_final\trequired_action\n"
            "0\tT cell\tnot_reviewed\tfalse\thuman_review_required\n",
            encoding="utf-8",
        )

        render_analysis_report(
            argparse.Namespace(
                config=str(config_path),
                manifest=str(manifest),
                contrasts=str(contrasts),
                dataset_plan=str(plan),
                warnings=str(warnings),
                exclusions=str(root / "exclusions.tsv"),
                software=None,
                references=None,
                checksums=None,
                audit=None,
                candidate_scores=[str(candidate_scores)],
                suggested_annotations=[str(suggestions)],
                test_status=None,
                validation_report=None,
                validation_output=None,
                output=str(root / "analysis_report.html"),
                marker=str(root / "analysis.complete"),
            )
        )

        html = (root / "analysis_report.html").read_text(encoding="utf-8")
        self.assertIn("Candidate genes are hypothesis-generating", html)
        self.assertIn("Automated review status", html)
        self.assertIn("GENE1", html)
        self.assertIn("bulk_pseudobulk_opposite_direction", html)
        self.assertIn("single_gse_support", html)
        self.assertIn("limited", html)
        self.assertIn("human_review_required", html)
        self.assertIn("not final biological conclusions", html)

    def test_methods_report_includes_software_and_references(self):
        root = self._tmp()
        config_path = root / "config.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "project": {"name": "demo"},
                    "reporting": {"title": "Demo Report"},
                }
            ),
            encoding="utf-8",
        )
        software = root / "software.tsv"
        software.write_text(
            "software\tversion\tsource\tcommand\nsnakemake\t8.30.0\truntime\tsnakemake --version\n",
            encoding="utf-8",
        )
        references = root / "references.tsv"
        references.write_text(
            "reference_field\tvalue\texists\tsha256\tstatus\ngtf\tGENCODE.gtf\tfalse\tNA\tmetadata_or_unresolved\n",
            encoding="utf-8",
        )
        render_methods_report(
            argparse.Namespace(
                config=str(config_path),
                software=str(software),
                references=str(references),
                output=str(root / "methods.md"),
                marker=str(root / "methods.complete"),
            )
        )
        methods = (root / "methods.md").read_text(encoding="utf-8")
        self.assertIn("## Software Versions", methods)
        self.assertIn("snakemake", methods)
        self.assertIn("## Reference Versions", methods)
        self.assertIn("GENCODE.gtf", methods)

    def _tmp(self):
        return Path(self.enterContext(tempfile.TemporaryDirectory()))


if __name__ == "__main__":
    unittest.main()
