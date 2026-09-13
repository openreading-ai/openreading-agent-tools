"""Hand one user-selected file to core through an atomic private intake copy.

The GUI or trusted chat selection provider supplies a chosen absolute path. References are
random-entry/original-filename paths under CLIENT/v2/selection/ready. Source directories
never become grants. Staging and the advisory publisher lock remain outside that root.
Core supplies safe source opening and owns subsequent parsing and artifact identity.
This module bounds and hashes only the byte handoff; it never constructs a core artifact.
The helper refuses observed source edits rather than publishing a possibly mixed copy.

Each selection allows 25 MiB, with 512 MiB total ready and unfinished copies. This quota
is separate from core's artifact quota. Copies persist until explicitly removed; removing
intake does not erase already retained artifacts or excerpts delivered to the assistant.
Catchable copy failures clean current staging. SIGKILL can leave private unfinished data,
but the next publisher-lock holder removes abandoned staging before quota accounting.
Server startup validates directories without that lock and never removes staging.
Explicit clearing removes all completed intake copies, including earlier picker sessions.
The shared CLIENT/v2/artifacts store remains untouched. No environment variable selects
a source grant. HOME locates application data through runtime.configuration only.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from openreading.artifacts.intake import directory, source
from openreading.artifacts.limits import ArtifactError

from runtime.configuration import client_root

MAX_FILE_BYTES = 25 * 1024**2
MAX_SELECTION_BYTES = 512 * 1024**2


class SelectionError(ValueError):
    """A sanitized selection refusal suitable for the local picker."""


@dataclass(frozen=True)
class Selection:
    reference: str
    sha256: str
    length: int

    @property
    def prompt(self) -> str:
        return (
            "Use OpenReading to import this selected local document: "
            + json.dumps({"path": self.reference}, ensure_ascii=True)
            + ". Then answer my question using search and read, citing the physical page and evidence ID."
        )


def filename(name: str) -> bool:
    return (
        bool(name)
        and name.lower().endswith(".pdf")
        and not any(
            character in "/\\" or ord(character) < 32 or ord(character) == 127 for character in name
        )
    )


class SelectionStore:
    def __init__(self, client: str, *, home: Path | None = None):
        self.root = client_root(client, home=home) / "v2/selection"
        self.grant = self.root / "ready"
        self.staging = self.root / "staging"

    @contextmanager
    def directories(self):
        try:
            with (
                directory(self.root, create=True) as root,
                directory(self.grant, create=True) as ready,
                directory(self.staging, create=True) as staging,
            ):
                for opened in (root, ready, staging):
                    os.fchmod(opened, 0o700)
                yield root, ready, staging
        except (ArtifactError, OSError):
            raise SelectionError(
                "Cannot access the selected file or private intake. Symlinks are unsupported; "
                "choose a regular file through real folders, and check permissions and free space."
            ) from None

    @contextmanager
    def locked(self, *, wait: bool = False):
        with self.directories() as (root, ready, staging):
            lock = os.open("lock", os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR, 0o600, dir_fd=root)
            try:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
                except BlockingIOError:
                    # Convert inside directory(), which otherwise sanitizes OSError first.
                    raise SelectionError(
                        "Another selection is in progress. Try again shortly."
                    ) from None
                # A live publisher holds this lock for its whole copy. Existing staging is abandoned.
                for name in os.listdir(staging):
                    if not re.fullmatch(r"[0-9a-f]{32}", name) or not stat.S_ISDIR(
                        os.stat(name, dir_fd=staging, follow_symlinks=False).st_mode
                    ):
                        raise SelectionError(
                            "The private staging area contains an unexpected entry."
                        )
                    shutil.rmtree(name, dir_fd=staging)
                yield ready, staging
            finally:
                os.close(lock)

    def prepare(self) -> Path:
        # Readers need only the published directory, never ownership of the publisher lock.
        with self.directories():
            return self.grant

    def clear(self) -> int:
        with self.locked() as (ready, _):
            names = os.listdir(ready)
            # Validate the whole set before deletion; never turn unknown data into quota recovery.
            for name in names:
                if not re.fullmatch(r"[0-9a-f]{32}", name):
                    raise SelectionError("The private intake contains an unexpected entry.")
                with directory(self.grant / name) as opened:
                    files = os.listdir(opened)
                    if (
                        len(files) != 1
                        or not filename(files[0])
                        or not stat.S_ISREG(
                            os.stat(files[0], dir_fd=opened, follow_symlinks=False).st_mode
                        )
                    ):
                        raise SelectionError("The private intake contains an unexpected entry.")
            for name in names:
                shutil.rmtree(name, dir_fd=ready)
            return len(names)

    def used_bytes(self) -> int:
        total = 0
        for parent in (self.grant, self.staging):
            for entry in parent.iterdir():
                with directory(entry) as opened:
                    for name in os.listdir(opened):
                        info = os.stat(name, dir_fd=opened, follow_symlinks=False)
                        if not stat.S_ISREG(info.st_mode):
                            raise SelectionError("The private intake contains an unexpected entry.")
                        total += info.st_size
        return total

    def select(self, path: Path, *, cancelled: Callable[[], bool] = lambda: False) -> Selection:
        if not path.is_absolute() or not filename(path.name):
            raise SelectionError("Choose one local PDF file.")

        def check():
            if cancelled():
                raise SelectionError("Selection cancelled. Nothing was added.")

        with self.locked() as (ready, staging):
            check()
            available = MAX_SELECTION_BYTES - self.used_bytes()
            name = secrets.token_hex(16)
            if (self.grant / name).exists():
                raise SelectionError("Selection name collision. Try again.")
            os.mkdir(name, 0o700, dir_fd=staging)
            scratch = self.staging / name
            try:
                with source(path.parent, path.name) as opened:
                    before = os.fstat(opened)
                    if before.st_size <= 0:
                        raise SelectionError("The selected document is empty.")
                    if before.st_size > MAX_FILE_BYTES:
                        raise SelectionError(
                            "The selected document exceeds the 25 MiB input limit."
                        )
                    if before.st_size > available:
                        raise SelectionError(
                            "Selection storage is full. Use Clear selected copies before adding another."
                        )
                    digest = hashlib.sha256()
                    length = 0
                    with (scratch / path.name).open("xb") as output:
                        os.fchmod(output.fileno(), 0o600)
                        while True:
                            check()
                            chunk = os.read(opened, min(65536, MAX_FILE_BYTES - length + 1))
                            if not chunk:
                                break
                            length += len(chunk)
                            if length > min(MAX_FILE_BYTES, available):
                                raise SelectionError(
                                    "The document exceeded the input or storage limit while being copied."
                                )
                            output.write(chunk)
                            digest.update(chunk)
                        output.flush()
                        os.fsync(output.fileno())
                    after = os.fstat(opened)
                    changed = (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                    )
                    if changed:
                        raise SelectionError(
                            "The document changed while being copied. Select it again."
                        )

                check()
                with directory(scratch) as complete:
                    os.fsync(complete)
                os.rename(name, name, src_dir_fd=staging, dst_dir_fd=ready)
                return Selection(f"{name}/{path.name}", digest.hexdigest(), length)
            finally:
                # Published entries moved away; only this operation's unfinished copy is removed.
                if scratch.exists():
                    shutil.rmtree(scratch)

    def remove(self, reference: str, *, wait: bool = False) -> None:
        parts = reference.split("/")
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{32}", parts[0]) or not filename(parts[1]):
            raise SelectionError("Choose a reference created by this picker.")
        with self.locked(wait=wait) as (ready, _), directory(self.grant / parts[0]) as entry:
            if os.listdir(entry) != [parts[1]]:
                raise SelectionError("The selected copy no longer matches this reference.")
            info = os.stat(parts[1], dir_fd=entry, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise SelectionError("The selected copy is not a regular file.")
            os.unlink(parts[1], dir_fd=entry)
            os.rmdir(parts[0], dir_fd=ready)
