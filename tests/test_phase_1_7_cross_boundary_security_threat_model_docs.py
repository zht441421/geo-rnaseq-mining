from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = (
        repo_root
        / "docs"
        / "phase-1-7-cross-boundary-security-threat-model.md"
    )

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_7_documents_scope_and_readiness() -> None:
    text = _doc_text()
    required_terms = (
        "phase 1.7",
        "cross-boundary security threat model docs/tests only",
        "scope and readiness conclusion",
        "threat model does not authorize implementation",
        "not ready for runtime security enforcement",
        "design controls are not actually enforced controls",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_7_documents_assets_and_actors() -> None:
    text = _doc_text()
    required_terms = (
        "assets",
        "task request",
        "manifest",
        "execution preview",
        "approval record",
        "validation result",
        "artifact metadata",
        "audit information",
        "credentials/secrets boundary",
        "future geo, snakemake, and coze interfaces",
        "user",
        "operator",
        "future runtime service",
        "future worker",
        "external service",
        "attacker",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_7_documents_trust_boundaries() -> None:
    text = _doc_text()
    required_terms = (
        "user input boundary",
        "manifest boundary",
        "approval boundary",
        "validation boundary",
        "sandbox boundary",
        "artifact boundary",
        "network boundary",
        "audit boundary",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_7_documents_stride_and_specific_threats() -> None:
    text = _doc_text()
    required_terms = (
        "stride",
        "spoofing",
        "tampering",
        "repudiation",
        "information disclosure",
        "denial of service",
        "elevation of privilege",
        "path traversal",
        "symlink traversal",
        "toctou",
        "overwrite abuse",
        "command injection",
        "unsafe input propagation",
        "approval bypass",
        "stale approval",
        "replay",
        "id relationship mismatch",
        "privilege escalation",
        "secret leakage",
        "local path leakage",
        "hidden persistence",
        "network exfiltration",
        "ssrf-like risk",
        "resource exhaustion",
        "cancellation failure",
        "cleanup failure",
        "audit tampering",
        "sensitive error disclosure",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_7_documents_controls_and_mapping() -> None:
    text = _doc_text()
    required_terms = (
        "existing design controls",
        "fail-closed by default",
        "report-only until future runtime approval",
        "approval/execution separation",
        "artifact validation rules",
        "path safety concepts",
        "network prohibition",
        "hidden persistence prohibition",
        "control mapping",
        "current design mitigation",
        "remaining gap",
        "future prerequisite",
    )
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_7_documents_schema_is_design_only() -> None:
    text = _doc_text()
    required_terms = (
        "threat assessment schema design",
        "not a json schema",
        "not a json\nschema",
        '"artifacts_created": false',
        '"sandbox_created": false',
        '"database_written": false',
        '"audit_persisted": false',
        '"network_performed": false',
        '"runtime_enforced": false',
        '"write_approved": false',
        '"execution_approved": false',
        '"approved_for_implementation": false',
    )
    assert any(term in text for term in ("not a json schema", "not a json\nschema"))
    assert [term for term in required_terms[2:] if term not in text] == []


def test_phase_1_7_documents_no_go_and_one_next_phase() -> None:
    text = _doc_text()
    required_terms = (
        "explicit no-go decision",
        "runtime security enforcement is not approved",
        "authentication system implementation is not approved",
        "secrets management system implementation is not approved",
        "database implementation is not approved",
        "network controls implementation is not approved",
        "sandbox implementation is not approved",
        "audit storage and audit persistence are not approved",
        "phase 1.8 secrets management and redaction",
        "recommend exactly one next topic",
        "do not directly enter real runtime implementation",
    )
    assert [term for term in required_terms if term not in text] == []
