"""Keep destination choices separate from legacy document grants and plugin caches.

Settings live in CLIENT/destination.json with mode 0600 and a fresh revision on each save.
An absent file has the legacy local marker; the server-only launcher requests setup.
Invalid explicit settings never fall back to local processing.
Schema 2 stores only the URL, response limit, mode and revision.
Schema 1 is readable for upgrades, but its credential reference is discarded.
Existing Keychain items are neither accessed nor deleted by the connector.
No setting grants document access, sends a document, or starts a server.
"""

from __future__ import annotations

import json
import os
import re
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path

from openreading.artifacts.intake import directory
from openreading.artifacts.limits import ArtifactError

from runtime.configuration import client_root
from runtime.server_transport import ServerDestination


@dataclass(frozen=True)
class DestinationSettings:
    mode: str = "local"
    revision: str = "default"
    destination: ServerDestination | None = None

    def wire(self):
        value = {"schema_version": 2, "mode": self.mode, "revision": self.revision}
        if self.destination is not None:
            value.update(
                base_url=self.destination.base_url,
                response_bytes=self.destination.response_bytes,
            )
        return value


def decode_settings(value: dict) -> DestinationSettings:
    """Validate the same closed, nonsecret settings shape for launch and detached jobs."""
    if (
        not isinstance(value, dict)
        or type(value.get("schema_version")) is not int
        or value["schema_version"] not in {1, 2}
    ):
        raise ValueError("Invalid destination settings.")
    revision = value.get("revision")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{32}", revision) is None:
        raise ValueError("Invalid destination settings.")
    if value.get("mode") == "local" and set(value) == {"schema_version", "mode", "revision"}:
        return DestinationSettings(revision=revision)
    fields = {"schema_version", "mode", "revision", "base_url", "response_bytes"}
    if value["schema_version"] == 1:
        fields.add("credential_ref")
    if value.get("mode") != "server" or set(value) != fields:
        raise ValueError("Invalid destination settings.")
    if value["schema_version"] == 1:
        key = value["credential_ref"]
        if key is not None and (
            not isinstance(key, str) or re.fullmatch(r"[0-9a-f]{32}", key) is None
        ):
            raise ValueError("Invalid destination settings.")
    if not isinstance(value["base_url"], str):
        raise ValueError("Invalid destination settings.")
    destination = ServerDestination(value["base_url"], revision, value["response_bytes"])
    return DestinationSettings("server", revision, destination)


def read_destination(client: str, *, home: Path | None = None) -> DestinationSettings:
    path = client_root(client, home=home) / "destination.json"
    try:
        with directory(path.parent, create=True) as parent:
            try:
                fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            except FileNotFoundError:
                return DestinationSettings()
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError("Invalid destination settings file.")
                data = stream.read(16385)
                if len(data) > 16384:
                    raise ValueError("Oversized destination settings.")
                return decode_settings(json.loads(data))
    except (ArtifactError, OSError, ValueError, TypeError):
        raise ValueError(
            "Cannot read the explicit destination settings. Open OpenReading Settings."
        ) from None


def save_destination(
    client: str,
    mode: str,
    *,
    base_url: str = "",
    response_bytes: int = 256 * 1024 * 1024,
    home: Path | None = None,
) -> DestinationSettings:
    """Save a URL-only destination with a new revision for selection consent."""
    revision = uuid.uuid4().hex
    if mode == "local":
        settings = DestinationSettings(revision=revision)
    elif mode == "server":
        destination = ServerDestination(base_url, revision, response_bytes)
        settings = DestinationSettings(mode, revision, destination)
    else:
        raise ValueError("Invalid processing destination mode.")
    root = client_root(client, home=home)
    with directory(root, create=True) as parent:
        os.fchmod(parent, 0o700)
        name = ".destination-" + revision
        fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(settings.wire(), stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, "destination.json", src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try:
                os.unlink(name, dir_fd=parent)
            except FileNotFoundError:
                pass
    return settings
