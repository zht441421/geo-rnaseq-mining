from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-4c-dry-run-validation-rejection-matrix.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_4c_validation_matrix_documents_accepted_conditions() -> None:
    text = _doc_text()

    required_terms = (
        "accepted dry-run request conditions",
        "`mode` | `dry_run`",
        "`allow_network` | `false`",
        "`allow_pipeline_execution` | `false`",
        "`allow_snakemake` | `false`",
        "`allow_real_coze_call` | `false`",
        "`operator_approved` | `false`",
        "`output_format` | `json`, `markdown`, or `html`",
        "accession-like placeholder such as `gse123456`",
        "must not trigger download",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_4c_validation_matrix_documents_rejected_conditions() -> None:
    text = _doc_text()

    required_terms = (
        "rejected request conditions",
        "`mode = run`",
        "`mode = execute`",
        "`allow_network = true`",
        "`allow_pipeline_execution = true`",
        "`allow_snakemake = true`",
        "`allow_real_coze_call = true`",
        "`operator_approved = true` with real execution intent",
        "`dataset_accession` contains a url",
        "`dataset_accession` contains a shell fragment",
        "`output_format = zip`",
        "request contains `command`",
        "request contains `shell`",
        "request contains `subprocess`",
        "request contains `secret`, `token`, `password`, or `api_key`",
        "request asks to write real artifacts",
        "request asks to write database records",
        "request asks for a background worker or scheduler",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_4c_validation_matrix_documents_rejection_reasons() -> None:
    text = _doc_text()

    rejection_reasons = (
        "real_execution_not_allowed",
        "network_access_not_allowed",
        "pipeline_execution_not_allowed",
        "snakemake_not_allowed",
        "real_coze_call_not_allowed",
        "operator_approval_not_active_in_this_phase",
        "unsupported_output_format",
        "unsafe_dataset_accession",
        "command_field_not_allowed",
        "secret_field_not_allowed",
        "artifact_write_not_allowed",
        "database_write_not_allowed",
        "background_execution_not_allowed",
    )

    missing_reasons = [reason for reason in rejection_reasons if reason not in text]

    assert missing_reasons == []


def test_phase_1_4c_validation_matrix_remains_documentation_only() -> None:
    text = _doc_text()

    required_terms = (
        "documentation-level validation and rejection matrix",
        "runtime validation is not implemented",
        "does not start a server",
        "access the network",
        "download geo data",
        "run rna-seq processing",
        "run snakemake",
        "call coze",
        "write real artifacts",
        "write a database",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
