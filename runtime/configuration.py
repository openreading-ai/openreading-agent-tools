"""Persist explicit coding-client grants independently of ephemeral plugin directories.

No environment variable grants document access. Setup receives one absolute directory
through --input-root. Missing or invalid configuration refuses startup without a home grant.
The OS HOME value locates application settings and retained evidence, never source inputs.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

CLIENTS = {"claude-desktop", "claude-code", "codex"}


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
