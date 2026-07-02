#!/usr/bin/env python3

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

from metadata_io import NA, load_raw_json, read_tsv, write_tsv


RAW_FIELDS = [
    "dataset_id",
    "gse_id",
    "gsm_id",
    "srx_id",
    "srr_id",
    "geo_title",
    "geo_source_name",
    "geo_characteristics_raw",
    "platform",
    "library_strategy",
    "library_source",
    "library_layout",
    "supplementary_files",
]
SUGGESTED_FIELDS = [
    "suggested_sample_id",
    "suggested_subject_id",
    "suggested_group",
    "suggested_condition",
    "suggested_tissue",
    "suggested_batch",
    "suggested_data_type",
    "suggested_include",
    "suggestion_evidence",
    "suggestion_confidence",
    "requires_manual_review",
]
FORMAL_FIELDS = [
    "sample_id",
    "subject_id",
    "include",
    "group",
    "condition",
    "tissue",
    "batch",
    "sex",
    "age",
    "timepoint",
    "treatment",
    "paired_group",
    "data_type",
    "matrix_path",
    "fastq_r1",
    "fastq_r2",
    "notes",
    "reviewer_note",
    "review_status",
]
MANIFEST_FIELDS = RAW_FIELDS + SUGGESTED_FIELDS + FORMAL_FIELDS
CONFLICT_FIELDS = [
    "dataset_id",
    "gse_id",
    "gsm_id",
    "srx_id",
    "srr_id",
    "conflict_type",
    "severity",
    "observed_values",
    "evidence",
    "suggested_action",
]
UNMAPPED_FIELDS = [
    "dataset_id",
    "gse_id",
    "gsm_id",
    "srx_id",
    "srr_id",
    "reason",
    "suggested_action",
]


def flatten_values(value):
    if isinstance(value, list):
        for item in value:
            yield from flatten_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_values(item)
    elif value not in (None, "", NA):
        yield str(value)


def characteristic_strings(raw_value):
    if raw_value in (None, "", NA):
        return []
    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError):
        return [str(raw_value)]
    if isinstance(parsed, list) and all(
        isinstance(item, dict) and "field_name" in item for item in parsed
    ):
        values = []
        for item in parsed:
            values.extend(flatten_values(item.get("values")))
        return values
    return list(flatten_values(parsed))


def parse_characteristics(raw_value):
    parsed = []
    for text in characteristic_strings(raw_value):
        if ":" in text:
            key, value = text.split(":", 1)
            parsed.append((key.strip(), value.strip(), text))
        else:
            parsed.append(("", text.strip(), text))
    return parsed


def matching_terms(text, terms):
    lowered = text.lower()
    matches = []
    for term in terms:
        pattern = rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])"
        if re.search(pattern, lowered):
            matches.append(term)
    return sorted(set(matches))


def characteristic_suggestion(characteristics, keys):
    key_terms = [key.lower() for key in keys]
    matches = []
    for key, value, raw_text in characteristics:
        lowered = key.lower()
        if any(term in lowered for term in key_terms) and value:
            matches.append((value, raw_text))
    unique_values = list(dict.fromkeys(value for value, _ in matches))
    if len(unique_values) == 1:
        return unique_values[0], [raw for _, raw in matches], "high"
    if len(unique_values) > 1:
        return "conflict", [raw for _, raw in matches], "low"
    return NA, ["No matching characteristic key was found."], "low"


def infer_data_type(text, library_strategy, rules):
    scrna = matching_terms(text, rules["scrna_terms"])
    snrna = matching_terms(text, rules["snrna_terms"])
    if scrna and snrna:
        return "conflict", [*scrna, *snrna], "low"
    if snrna:
        return "snRNA-seq_candidate", snrna, "medium"
    if scrna:
        return "scRNA-seq_candidate", scrna, "medium"
    if library_strategy != NA and "rna-seq" in library_strategy.lower():
        return (
            "bulk_RNA-seq_candidate",
            [f"library_strategy={library_strategy}; no single-cell/nucleus term found"],
            "low",
        )
    return NA, ["Insufficient library strategy and modality evidence."], "low"


def evidence_entry(value, evidence, confidence):
    return {
        "value": value,
        "evidence": evidence,
        "confidence": confidence,
    }


def build_suggestions(sample, run, rules):
    characteristics = parse_characteristics(sample.get("characteristics_ch1_raw"))
    text_parts = [
        sample.get("title", ""),
        sample.get("source_name", ""),
        *[raw for _, _, raw in characteristics],
    ]
    text = " | ".join(part for part in text_parts if part not in ("", NA))
    case_terms = matching_terms(text, rules["case_candidate_terms"])
    control_terms = matching_terms(text, rules["control_candidate_terms"])
    if case_terms and control_terms:
        suggested_group = "conflict"
        group_evidence = {
            "case_candidate_terms": case_terms,
            "control_candidate_terms": control_terms,
        }
        group_confidence = "low"
    elif case_terms:
        suggested_group = "case_candidate"
        group_evidence = {"case_candidate_terms": case_terms}
        group_confidence = "medium"
    elif control_terms:
        suggested_group = "control_candidate"
        group_evidence = {"control_candidate_terms": control_terms}
        group_confidence = "medium"
    else:
        suggested_group = NA
        group_evidence = {"message": "No configured group candidate term found."}
        group_confidence = "low"

    condition, condition_evidence, condition_confidence = characteristic_suggestion(
        characteristics, rules["condition_keys"]
    )
    tissue, tissue_evidence, tissue_confidence = characteristic_suggestion(
        characteristics, rules["tissue_keys"]
    )
    if tissue == NA and sample.get("source_name") not in (None, "", NA):
        tissue = sample["source_name"]
        tissue_evidence = [f"geo_source_name={sample['source_name']}"]
        tissue_confidence = "low"
    batch, batch_evidence, batch_confidence = characteristic_suggestion(
        characteristics, rules["batch_keys"]
    )
    data_type, data_type_evidence, data_type_confidence = infer_data_type(
        text, run.get("library_strategy", NA), rules
    )
    gsm = sample.get("gsm_accession", NA)
    srr = run.get("srr_accession", NA)
    suggested_sample_id = f"{gsm}__{srr}" if srr != NA else gsm

    evidence = {
        "suggested_sample_id": evidence_entry(
            suggested_sample_id,
            ["Deterministic identifier from raw GSM and SRR; no runs were merged."],
            "high",
        ),
        "suggested_subject_id": evidence_entry(
            NA,
            ["Subject and biological replicate relationships are never inferred."],
            "low",
        ),
        "suggested_group": evidence_entry(
            suggested_group, group_evidence, group_confidence
        ),
        "suggested_condition": evidence_entry(
            condition, condition_evidence, condition_confidence
        ),
        "suggested_tissue": evidence_entry(
            tissue, tissue_evidence, tissue_confidence
        ),
        "suggested_batch": evidence_entry(batch, batch_evidence, batch_confidence),
        "suggested_data_type": evidence_entry(
            data_type, data_type_evidence, data_type_confidence
        ),
        "suggested_include": evidence_entry(
            "undetermined",
            ["Sample inclusion requires explicit human review."],
            "low",
        ),
    }
    confidences = [entry["confidence"] for entry in evidence.values()]
    overall_confidence = (
        "low"
        if "low" in confidences
        else "medium"
        if "medium" in confidences
        else "high"
    )
    return {
        "suggested_sample_id": suggested_sample_id,
        "suggested_subject_id": NA,
        "suggested_group": suggested_group,
        "suggested_condition": condition,
        "suggested_tissue": tissue,
        "suggested_batch": batch,
        "suggested_data_type": data_type,
        "suggested_include": "undetermined",
        "suggestion_evidence": json.dumps(
            evidence, ensure_ascii=False, sort_keys=True
        ),
        "suggestion_confidence": overall_confidence,
        "requires_manual_review": "true",
    }, {
        "case_terms": case_terms,
        "control_terms": control_terms,
        "technical_terms": matching_terms(
            text, rules["technical_replicate_terms"]
        ),
        "condition": condition,
        "batch": batch,
        "data_type": data_type,
    }


def supplementary_by_gsm(rows):
    gse_files = defaultdict(list)
    gsm_files = defaultdict(list)
    for row in rows:
        value = {
            "file_name": row.get("supplementary_file_name", NA),
            "url": row.get("supplementary_url", NA),
            "size_bytes": row.get("size_bytes", NA),
            "file_type": row.get("file_type", NA),
        }
        if row.get("gsm_accession", NA) == NA:
            gse_files[row.get("gse_accession", NA)].append(value)
        else:
            gsm_files[row.get("gsm_accession", NA)].append(value)
    return gse_files, gsm_files


def add_conflict(conflicts, sample, run, conflict_type, severity, values, evidence, action):
    conflicts.append(
        {
            "dataset_id": sample.get("gse_accession", NA),
            "gse_id": sample.get("gse_accession", NA),
            "gsm_id": sample.get("gsm_accession", NA),
            "srx_id": run.get("srx_accession", NA),
            "srr_id": run.get("srr_accession", NA),
            "conflict_type": conflict_type,
            "severity": severity,
            "observed_values": json.dumps(values, ensure_ascii=False),
            "evidence": json.dumps(evidence, ensure_ascii=False),
            "suggested_action": action,
        }
    )


def prepare_manifest(samples, runinfo, supplementary, rules):
    runs_by_gsm = defaultdict(list)
    unmapped = []
    sample_ids = {sample.get("gsm_accession", NA) for sample in samples}
    for run in runinfo:
        gsm = run.get("gsm_accession", NA)
        if gsm == NA or gsm not in sample_ids:
            unmapped.append(
                {
                    "dataset_id": run.get("gse_accession", NA),
                    "gse_id": run.get("gse_accession", NA),
                    "gsm_id": gsm,
                    "srx_id": run.get("srx_accession", NA),
                    "srr_id": run.get("srr_accession", NA),
                    "reason": "SRA_RUN_WITHOUT_GEO_SAMPLE",
                    "suggested_action": "Review the raw GSM-SRX-SRR relationship manually.",
                }
            )
        else:
            runs_by_gsm[gsm].append(run)

    gse_files, gsm_files = supplementary_by_gsm(supplementary)
    manifest = []
    conflicts = []
    for sample in samples:
        gse = sample.get("gse_accession", NA)
        gsm = sample.get("gsm_accession", NA)
        runs = runs_by_gsm.get(gsm) or [
            {
                "gse_accession": gse,
                "gsm_accession": gsm,
                "srx_accession": NA,
                "srr_accession": NA,
                "library_strategy": NA,
                "library_source": NA,
                "library_layout": NA,
            }
        ]
        real_runs = [run for run in runs if run.get("srr_accession", NA) != NA]
        if not real_runs:
            unmapped.append(
                {
                    "dataset_id": gse,
                    "gse_id": gse,
                    "gsm_id": gsm,
                    "srx_id": runs[0].get("srx_accession", NA),
                    "srr_id": NA,
                    "reason": "GEO_SAMPLE_WITHOUT_MAPPED_SRR",
                    "suggested_action": "Confirm whether this sample has SRA runs or only supplementary data.",
                }
            )
        if len(real_runs) > 1:
            add_conflict(
                conflicts,
                sample,
                real_runs[0],
                "MULTIPLE_SRR_FOR_GSM",
                "warning",
                [run["srr_accession"] for run in real_runs],
                ["All run mappings were retained as separate manifest rows."],
                "Decide manually whether runs are technical replicates and whether merging is valid.",
            )

        supplementary_values = gse_files[gse] + gsm_files[gsm]
        for run in runs:
            suggestions, flags = build_suggestions(sample, run, rules)
            if flags["case_terms"] and flags["control_terms"]:
                add_conflict(
                    conflicts,
                    sample,
                    run,
                    "CONFLICTING_GROUP_TERMS",
                    "critical",
                    {
                        "case_candidate_terms": flags["case_terms"],
                        "control_candidate_terms": flags["control_terms"],
                    },
                    [sample.get("title", NA), sample.get("characteristics_ch1_raw", NA)],
                    "Inspect the original GEO description and assign group manually.",
                )
            elif not flags["case_terms"] and not flags["control_terms"]:
                add_conflict(
                    conflicts,
                    sample,
                    run,
                    "MISSING_GROUP_EVIDENCE",
                    "warning",
                    [NA],
                    [sample.get("title", NA), sample.get("characteristics_ch1_raw", NA)],
                    "Assign group manually from the study design; no candidate term was found.",
                )
            if flags["technical_terms"]:
                add_conflict(
                    conflicts,
                    sample,
                    run,
                    "TECHNICAL_REPLICATE_DESCRIPTION",
                    "warning",
                    flags["technical_terms"],
                    [sample.get("title", NA), sample.get("characteristics_ch1_raw", NA)],
                    "Define technical replicate relationships manually; no runs were merged.",
                )
            if run.get("library_layout", NA) == NA:
                add_conflict(
                    conflicts,
                    sample,
                    run,
                    "MISSING_LIBRARY_LAYOUT",
                    "warning",
                    [NA],
                    [f"SRR={run.get('srr_accession', NA)}"],
                    "Confirm library layout from SRA or the publication before FASTQ processing.",
                )
            if flags["condition"] == "conflict":
                add_conflict(
                    conflicts,
                    sample,
                    run,
                    "CONFLICTING_CONDITION_VALUES",
                    "warning",
                    ["conflict"],
                    [sample.get("characteristics_ch1_raw", NA)],
                    "Resolve the condition using the original study documentation.",
                )
            if flags["data_type"] == "conflict":
                add_conflict(
                    conflicts,
                    sample,
                    run,
                    "CONFLICTING_DATA_TYPE_TERMS",
                    "critical",
                    ["scRNA-seq_candidate", "snRNA-seq_candidate"],
                    [sample.get("title", NA), sample.get("characteristics_ch1_raw", NA)],
                    "Assign data_type manually and decide whether modalities may be combined.",
                )

            row = {
                "dataset_id": gse,
                "gse_id": gse,
                "gsm_id": gsm,
                "srx_id": run.get("srx_accession", NA),
                "srr_id": run.get("srr_accession", NA),
                "geo_title": sample.get("title", NA),
                "geo_source_name": sample.get("source_name", NA),
                "geo_characteristics_raw": sample.get(
                    "characteristics_ch1_raw", NA
                ),
                "platform": sample.get("platform", NA),
                "library_strategy": run.get("library_strategy", NA),
                "library_source": run.get("library_source", NA),
                "library_layout": run.get("library_layout", NA),
                "supplementary_files": json.dumps(
                    supplementary_values, ensure_ascii=False
                )
                if supplementary_values
                else NA,
                **suggestions,
            }
            row.update({field: "" for field in FORMAL_FIELDS})
            row["review_status"] = "pending"
            manifest.append(row)
    return manifest, conflicts, unmapped


def write_manifest(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=MANIFEST_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare suggestions for human metadata review."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--runinfo", required=True)
    parser.add_argument("--supplementary", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--conflicts", required=True)
    parser.add_argument("--unmapped-runs", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        rules = yaml.safe_load(handle)["metadata_review"]
    manifest, conflicts, unmapped = prepare_manifest(
        read_tsv(args.samples),
        read_tsv(args.runinfo),
        read_tsv(args.supplementary),
        rules,
    )
    write_manifest(args.manifest, manifest)
    write_tsv(args.conflicts, CONFLICT_FIELDS, conflicts)
    write_tsv(args.unmapped_runs, UNMAPPED_FIELDS, unmapped)
    print(
        f"Prepared {len(manifest)} suggested rows, "
        f"{len(conflicts)} conflicts, and {len(unmapped)} unmapped records."
    )


if __name__ == "__main__":
    main()
