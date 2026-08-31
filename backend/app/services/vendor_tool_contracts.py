"""Inert request contracts for verification-gated optional vendor tools.

This module performs validation only. It does not discover, install, launch, or
register a vendor tool and is intentionally not imported by any runtime route.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class VendorArtifactSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    vendor_id: str
    version: str = Field(min_length=1, max_length=64)
    platform: str = Field(min_length=1, max_length=64)
    artifact_url: str = Field(pattern=r"^https://")
    sha256: str
    license_id: str = Field(min_length=1, max_length=64)

    @field_validator("vendor_id")
    @classmethod
    def validate_vendor_id(cls, value: str) -> str:
        if not _ID_RE.fullmatch(value):
            raise ValueError("vendor_id must be a bounded identifier")
        return value

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        normalized = value.lower()
        if not _SHA256_RE.fullmatch(normalized):
            raise ValueError("sha256 must contain 64 hexadecimal characters")
        return normalized


class VendorPreflightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    vendor_id: str
    repository_id: str
    dev_mode: Literal["on"]

    @field_validator("vendor_id", "repository_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not _ID_RE.fullmatch(value):
            raise ValueError("identifier is invalid")
        return value


class VendorInvocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    vendor_id: str
    repository_id: str
    task_reference: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=16_000)
    mode: Literal["dry-run"] = "dry-run"
    timeout_seconds: int = Field(default=120, ge=1, le=300)

    @field_validator("vendor_id", "repository_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not _ID_RE.fullmatch(value):
            raise ValueError("identifier is invalid")
        return value
