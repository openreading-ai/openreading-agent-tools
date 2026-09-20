"""Persist explicit client grants independently of ephemeral plugin directories.

No environment variable grants document access. Setup receives one absolute directory
through --input-root. Missing or invalid configuration refuses startup without a home grant.
The OS HOME value locates application settings and retained evidence, never source inputs.
Version 2 uses CLIENT/v2/config.json with exactly schema_version=2, input_root and boolean ocr.
It never reads or replaces legacy settings. Direct setup and persisted setup never merge.
Core validates the grant/store boundary before an atomic mode-0600 settings replacement.
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path

CLIENTS = {"claude-desktop", "claude-code", "codex", "chatgpt"}


def client_root(client: str, *, home: Path | None = None) -> Path:
    if client not in CLIENTS:
        raise ValueError("Unknown client.")
    return (home or Path.home()) / "Library/Application Support/OpenReading/agent-tools" / client


def configure(client: str, grant: Path, *, home: Path | None = None) -> None:
    from openreading.artifacts.intake import directory
    from openreading.artifacts.limits import ArtifactError, ProfileConfig
    from openreading.artifacts.store import Store

    root = client_root(client, home=home)
    try:
        Store(ProfileConfig(grant, root / "v1"))
        with directory(root):
            fd, name = tempfile.mkstemp(prefix=".config-", dir=root)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(json.dumps({"input_root": str(grant)}).encode())
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(name, root / "config.json")
            finally:
                Path(name).unlink(missing_ok=True)
    except (ArtifactError, OSError):
        raise ValueError(
            "Choose an existing absolute document directory outside the retained store."
        ) from None


def read_grant(client: str, *, home: Path | None = None) -> Path:
    from openreading.artifacts.limits import ArtifactError
    from openreading.artifacts.store import safe_read

    try:
        value = json.loads(safe_read(client_root(client, home=home) / "config.json", 8192))
        if (
            not isinstance(value, dict)
            or set(value) != {"input_root"}
            or not isinstance(value["input_root"], str)
        ):
            raise ValueError("Invalid configuration")
        grant = Path(value["input_root"])
        if not grant.is_absolute():
            raise ValueError("Relative grant")
        return grant
    except (ArtifactError, OSError, ValueError):
        raise ValueError(
            "Configure an explicit document directory before starting this client."
        ) from None


@dataclass(frozen=True)
class Settings:
    """One explicit grant and a setup-only OCR choice."""

    input_root: Path
    ocr: bool = False


def ocr_value(value: str | None) -> bool:
    if value in (None, "", "off", "false"):
        return False
    if value in ("on", "true"):
        return True
    raise ValueError("configuration_required: OCR must be on, off, true, or false.")


def configure_v2(client: str, grant: Path, ocr: bool = False, *, home: Path | None = None) -> None:
    from openreading.artifacts.intake import directory
    from openreading.artifacts.limits import ArtifactError, ProfileConfig
    from openreading.artifacts.store import Store

    root = client_root(client, home=home) / "v2"
    try:
        if type(ocr) is not bool:
            raise ValueError
        # Open ancestors before Store can canonicalize them into another settings directory.
        with directory(root, create=True) as parent:
            store = Store(ProfileConfig(grant, root / "artifacts"))
            close = getattr(store, "close", None)
            if close:
                close()
            name = ".config-" + secrets.token_hex(16)
            fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=parent)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(
                        json.dumps(
                            {"schema_version": 2, "input_root": str(grant), "ocr": ocr}
                        ).encode()
                    )
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(name, "config.json", src_dir_fd=parent, dst_dir_fd=parent)
            finally:
                try:
                    os.unlink(name, dir_fd=parent)
                except FileNotFoundError:
                    pass
    except (ArtifactError, OSError, ValueError):
        raise ValueError(
            "configuration_required: Choose an existing absolute document directory outside the retained store."
        ) from None


def read_settings(client: str, *, home: Path | None = None) -> Settings:
    from openreading.artifacts.limits import ArtifactError
    from openreading.artifacts.store import safe_read

    try:
        value = json.loads(safe_read(client_root(client, home=home) / "v2/config.json", 8192))
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "input_root", "ocr"}
            or type(value["schema_version"]) is not int
            or value["schema_version"] != 2
            or type(value["ocr"]) is not bool
            or not isinstance(value["input_root"], str)
        ):
            raise ValueError
        grant = Path(value["input_root"])
        if not grant.is_absolute():
            raise ValueError
        return Settings(grant, value["ocr"])
    except (ArtifactError, OSError, ValueError):
        raise ValueError(
            "configuration_required: Configure a document directory before startup."
        ) from None


def select_settings(
    client: str, grant: Path | None, ocr: str | None, *, home: Path | None = None
) -> Settings:
    if grant is not None:
        return Settings(grant, ocr_value(ocr))
    if ocr is not None:
        raise ValueError(
            "configuration_required: An OCR override requires an explicit document directory."
        )
    return read_settings(client, home=home)
