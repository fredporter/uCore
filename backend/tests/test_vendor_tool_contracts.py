import pytest
from pydantic import ValidationError

from app.services.vendor_tool_contracts import (
    VendorArtifactSpec,
    VendorInvocationRequest,
    VendorPreflightRequest,
)


def test_artifact_contract_requires_pinned_https_provenance():
    spec = VendorArtifactSpec(
        vendor_id="nanocoder",
        version="1.2.3",
        platform="darwin-arm64",
        artifact_url="https://example.invalid/nanocoder-1.2.3",
        sha256="a" * 64,
        license_id="MIT",
    )

    assert spec.sha256 == "a" * 64


@pytest.mark.parametrize(
    "field,value",
    [("artifact_url", "http://example.invalid/tool"), ("sha256", "unverified")],
)
def test_artifact_contract_rejects_unpinned_inputs(field: str, value: str):
    payload = {
        "vendor_id": "nanocoder",
        "version": "1.2.3",
        "platform": "darwin-arm64",
        "artifact_url": "https://example.invalid/tool",
        "sha256": "b" * 64,
        "license_id": "MIT",
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        VendorArtifactSpec(**payload)


def test_preflight_requires_dev_mode_and_repository_identifier():
    with pytest.raises(ValidationError):
        VendorPreflightRequest(
            vendor_id="nanocoder",
            repository_id="../../outside",
            dev_mode="off",
        )


def test_invocation_contract_is_dry_run_only_and_rejects_environment_injection():
    with pytest.raises(ValidationError):
        VendorInvocationRequest(
            vendor_id="nanocoder",
            repository_id="ucore",
            task_reference="task-123",
            prompt="Inspect the selected task",
            mode="write",
            environment={"TOKEN": "secret"},
        )


def test_invocation_contract_accepts_bounded_dry_run():
    request = VendorInvocationRequest(
        vendor_id="nanocoder",
        repository_id="ucore",
        task_reference="task-123",
        prompt="Inspect the selected task",
    )

    assert request.mode == "dry-run"
    assert request.timeout_seconds == 120
