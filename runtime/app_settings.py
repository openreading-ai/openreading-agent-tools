"""Persist native storage and delivery preferences outside the movable data directory.

CLIENT/preferences.json is a closed mode-0600 record. Absence means ~/.openreading and
one million serialized MCP response bytes. Invalid explicit settings refuse startup.
The selected directory is a storage destination, never a source grant. Each client owns
its own partition beneath it. Saving requests a switch; storage_session applies it only
when previous connections and import supervisors have stopped. Environment variables do
not select settings. The OS home directory locates the private control record.

Advanced limits live separately in CLIENT/advanced.json. Saving those limits must not
request a storage move or apply an unsaved server destination. When absent, legacy limits
remain effective; new installations allow one million inline bytes and 256 MiB downloads.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from openreading.artifacts.intake import directory
from openreading.artifacts.limits import ArtifactError
from openreading.artifacts.store import safe_read

from runtime.configuration import client_root


@dataclass(frozen=True)
class Preferences:
    data_folder: Path
    document_response_bytes: int = 1_000_000


@dataclass(frozen=True)
class Limits:
    document_response_bytes: int = 1_000_000
    server_response_bytes: int = 256 * 1024 * 1024


def validate_limits(budget, maximum):
    if type(budget) is not int or not 4096 <= budget <= 1_000_000_000:
        raise ValueError("Response file threshold must be from 4096 to 1000000000 bytes.")
    if type(maximum) is not int or maximum < 1024 * 1024:
        raise ValueError("Maximum downloaded response must be at least 1 MiB.")
    return Limits(budget, maximum)


def read_limits(client, *, home=None):
    path = client_root(client, home=home) / "advanced.json"
    if not path.exists() and not path.is_symlink():
        from runtime.destination_settings import read_destination

        destination = read_destination(client, home=home).destination
        return Limits(
            read_preferences(client, home=home).document_response_bytes,
            destination.response_bytes if destination else Limits().server_response_bytes,
        )
    try:
        value = json.loads(safe_read(path, 16384))
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "document_response_bytes", "server_response_bytes"}
            or type(value["schema_version"]) is not int
            or value["schema_version"] != 1
        ):
            raise ValueError
        return validate_limits(value["document_response_bytes"], value["server_response_bytes"])
    except (ValueError, OSError, ArtifactError):
        raise ValueError(
            "Cannot read Advanced settings. Open OpenReading Settings to repair them."
        ) from None


def save_limits(client, budget, maximum, *, home=None):
    value = validate_limits(budget, maximum)
    try:
        write_private(
            client_root(client, home=home) / "advanced.json",
            {
                "schema_version": 1,
                "document_response_bytes": value.document_response_bytes,
                "server_response_bytes": value.server_response_bytes,
            },
        )
    except (ArtifactError, OSError):
        raise ValueError(
            "Cannot save Advanced settings. Check local permissions and free space."
        ) from None
    return value


def validate(folder, budget):
    if (
        not isinstance(folder, Path)
        or not folder.is_absolute()
        or ".." in folder.parts
        or "\x00" in str(folder)
        or type(budget) is not int
        or not 4096 <= budget <= 1_000_000_000
    ):
        raise ValueError(
            "Choose an absolute data folder and a response budget from 4096 to 1000000000 bytes."
        )
    return Preferences(folder, budget)


def read_preferences(client: str, *, home: Path | None = None) -> Preferences:
    path = client_root(client, home=home) / "preferences.json"
    if not path.exists() and not path.is_symlink():
        return Preferences((home or Path.home()) / ".openreading")
    try:
        value = json.loads(safe_read(path, 16384))
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "data_folder", "document_response_bytes"}
            or type(value["schema_version"]) is not int
            or value["schema_version"] != 1
            or not isinstance(value["data_folder"], str)
        ):
            raise ValueError
        return validate(Path(value["data_folder"]), value["document_response_bytes"])
    except (ValueError, OSError, ArtifactError):
        raise ValueError(
            "Cannot read OpenReading preferences. Open OpenReading Settings to repair them."
        ) from None


def write_private(path: Path, value: dict):
    """Publish one bounded control record without following links or exposing partial writes."""
    with directory(path.parent, create=True) as parent:
        os.fchmod(parent, 0o700)
        name = ".settings-" + uuid.uuid4().hex
        fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(value, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path.name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try:
                os.unlink(name, dir_fd=parent)
            except FileNotFoundError:
                pass


def save_preferences(client, data_folder, document_response_bytes, *, home=None):
    value = validate(data_folder, document_response_bytes)
    try:
        write_private(
            client_root(client, home=home) / "preferences.json",
            {
                "schema_version": 1,
                "data_folder": str(value.data_folder),
                "document_response_bytes": value.document_response_bytes,
            },
        )
    except (ArtifactError, OSError):
        raise ValueError(
            "Cannot save OpenReading preferences. Check folder permissions and free space."
        ) from None
    return value
