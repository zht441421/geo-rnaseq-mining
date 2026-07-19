from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = (
        repo_root
        / "docs"
        / "phase-1-8-secrets-management-redaction-boundary.md"
    )
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_8_documents_scope_and_readiness() -> None:
    text = _doc_text()
    required_terms = (
        "phase 1.8",
        "secrets management and redaction boundary design docs/tests-only",
        "secrets implementation is not approved",
        "report-only until future runtime approval",
        "validation does not access secret",
        "approval does not authorize secret disclosure",
        "design controls do not equal enforced controls",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_8_documents_secret_classification() -> None:
    text = _doc_text()
    required_terms = (
        "secret classification",
        "credentials",
        "api tokens",
        "access keys",
        "internal identifiers",
        "sensitive metadata",
        "unknown or suspected secrets",
        "unknown/suspected secrets",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_8_documents_trust_boundaries() -> None:
    text = _doc_text()
    required_terms = (
        "trust model and boundaries",
        "user boundary",
        "coze boundary",
        "api boundary",
        "runtime boundary",
        "worker boundary",
        "external service boundary",
        "audit boundary",
        "artifact boundary",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_8_documents_lifecycle_and_redaction_rules() -> None:
    text = _doc_text()
    required_terms = (
        "secret lifecycle model",
        "source -> access -> use -> redact -> discard",
        "log redaction rules",
        "error redaction rules",
        "artifact redaction rules",
        "audit redaction rules",
        "preview redaction rules",
        "validation result redaction rules",
        "must not echo the rejected raw value",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_8_documents_least_privilege_and_leakage() -> None:
    text = _doc_text()
    required_terms = (
        "least privilege principles",
        "minimum actor authority",
        "minimum service and destination scope",
        "no cross-task reuse",
        "prompt leakage",
        "log leakage",
        "artifact leakage",
        "audit leakage",
        "network exposure",
        "api exposure",
        "worker exposure",
        "future prerequisite",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_8_documents_report_only_schema() -> None:
    text = _doc_text()
    required_terms = (
        "report-only assessment schema design",
        "not a json schema",
        "pydantic model",
        "runtime object",
        '"secret_values_present": false',
        '"credential_accessed": false',
        '"environment_read": false',
        '"logs_written": false',
        '"artifacts_created": false',
        '"audit_persisted": false',
        '"network_performed": false',
        '"secret_access_approved": false',
        '"approved_for_implementation": false',
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_8_documents_no_go_decision() -> None:
    text = _doc_text()
    required_terms = (
        "explicit no-go decision",
        "secret system implementation is not approved",
        "secret loader implementation is not approved",
        "credential provider implementation is not approved",
        "credential storage and credential cache are not approved",
        "api key storage is not approved",
        "vault integration is not approved",
        "aws secrets manager integration is not approved",
        "kubernetes secret integration is not approved",
        "environment injection is not approved",
        "authentication implementation is not approved",
        "authorization implementation is not approved",
        "runtime redactor and log interceptor are not approved",
        "artifact scanner is not approved",
        "audit persistence is not approved",
        "network client and api handler are not approved",
        "worker credential delegation is not approved",
        "does not read environment variables",
        "use a real credential",
    )
    assert [term for term in required_terms if term not in text] == []
