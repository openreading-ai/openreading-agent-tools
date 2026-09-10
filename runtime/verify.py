"""Verify a runtime inventory before exposing document tools.

Hashes detect changes relative to release metadata. They do not authenticate a publisher;
a signed archive and reviewed distribution evidence supply that separate boundary.
Internal framework symlinks are recorded explicitly and must resolve inside the runtime.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


class ReleaseIntegrityError(ValueError):
    """The runtime cannot establish a complete, internally consistent file inventory."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict:
    root = root.resolve(strict=True)
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == "release.json":
            continue
        if path.is_symlink():
            try:
                target = path.resolve(strict=True)
                target.relative_to(root)
            except (OSError, ValueError, RuntimeError):
                raise ReleaseIntegrityError("Runtime symlink escapes its inventory.") from None
            result[relative] = {"symlink": os.readlink(path)}
        elif path.is_file():
            result[relative] = {
                "length": path.stat().st_size,
                "sha256": sha256(path),
                "executable": bool(path.stat().st_mode & 0o111),
            }
        elif not path.is_dir():
            raise ReleaseIntegrityError("Runtime contains a non-regular entry.")
    return result


def verify_release(root: Path) -> dict:
    try:
        metadata_path = root / "release.json"
        if metadata_path.is_symlink() or metadata_path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Invalid release metadata")
        metadata = json.loads(metadata_path.read_bytes())
        expected = {
            "format_version",
            "release_version",
            "os",
            "arch",
            "minimum_os_version",
            "core_commit",
            "core_version",
            "python_version",
            "dependency_lock_sha256",
            "worker_sha256",
            "files",
            "licenses",
        }
        if not isinstance(metadata, dict) or set(metadata) != expected:
            raise ValueError("Unexpected release fields")
        if (
            metadata["format_version"] != "1"
            or metadata["os"] != "darwin"
            or metadata["arch"] != "arm64"
        ):
            raise ValueError("Unsupported runtime platform")
        for name, length in [
            ("core_commit", 40),
            ("dependency_lock_sha256", 64),
            ("worker_sha256", 64),
        ]:
            if not isinstance(metadata[name], str) or not re.fullmatch(
                f"[0-9a-f]{{{length}}}", metadata[name]
            ):
                raise ValueError("Invalid release digest")
        for name in ["release_version", "core_version", "python_version", "minimum_os_version"]:
            if not isinstance(metadata[name], str) or not re.fullmatch(
                r"[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[a-z0-9.]+)?", metadata[name]
            ):
                raise ValueError("Invalid version")
        actual = inventory(root)
        if metadata["files"] != actual:
            raise ValueError("Runtime inventory mismatch")
        if metadata["worker_sha256"] != actual["openreading-worker"]["sha256"]:
            raise ValueError("Worker digest mismatch")
        if (
            not isinstance(metadata["licenses"], list)
            or not metadata["licenses"]
            or any(name not in actual for name in metadata["licenses"])
        ):
            raise ValueError("Missing dependency notice")
        return metadata
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise ReleaseIntegrityError(
            "Runtime integrity verification failed. Reinstall a verified package."
        ) from None
