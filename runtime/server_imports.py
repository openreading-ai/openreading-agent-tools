"""Submit native-approved snapshots once and retain complete downloads through Core.

A client-wide advisory lock serializes HTTP submissions across detached jobs and tools.
A durable attempt marker precedes HTTP. An interrupted attempt never uploads again.
Batch markers stop siblings after local cancellation, shared failures or process death during a request.
Select and confirm the remaining files again to recover. Submitted server work may continue.
Document-specific HTTP rejections release the batch for its remaining selected documents.
Complete responses are atomically saved before retention, outside Core's staging sweep.
An explicit later import can retry local retention from that saved result without another POST.
These private transfer files persist with the selected copies until the user removes them.
No remote cancellation, remote job identity, or exactly-once server execution is claimed.
"""

from __future__ import annotations

import asyncio
import fcntl
import hashlib
import os
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from openreading.artifacts.intake import directory
from openreading.artifacts.limits import ArtifactError
from openreading.artifacts.service import ArtifactService
from openreading.artifacts.store import safe_read

from runtime.selection import SelectionError
from runtime.server_selection import approval_name, read_approval, write_private
from runtime.server_transport import (
    REQUEST,
    DestinationError,
    ServerResult,
    _decode,
    notify_progress,
    parse_document,
)


class ServerProcessingFailed(ArtifactError):
    """Preserve the transport's fixed diagnostic without exposing server response bodies."""

    def __init__(self, message):
        super().__init__("parse_failed")
        self.message = message

    def envelope(self):
        value = super().envelope()
        value.error.message = self.message
        return value


class SelectionStopped(ArtifactError):
    """Explain refusal of a consumed selection without exposing transport diagnostics."""

    def __init__(self):
        super().__init__("access_denied")

    def envelope(self):
        value = super().envelope()
        value.error.message = (
            "This selection stopped after cancellation, a shared failure, or an interrupted attempt. "
            "Select and confirm the remaining files again. Submitted server processing may continue."
        )
        return value


class ServerArtifactService(ArtifactService):
    def __init__(self, config, *, settings, selection, identity, keychain=None, transport=None):
        super().__init__(config, identity=identity)
        self.settings, self.selection = settings, selection
        self.keychain, self.transport = keychain, transport
        self.transfers = selection.root.parent / "server/transfers"
        with directory(self.transfers, create=True) as opened:
            os.fchmod(opened, 0o700)

    @contextmanager
    def _serial(self):
        with directory(self.transfers) as parent:
            fd = os.open("lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise ArtifactError("busy") from None
                yield
            finally:
                os.close(fd)

    def _retain(self, path, result, cancelled):
        from openreading.artifacts.retention import retain_response

        return retain_response(
            self,
            path,
            result.response,
            source_sha256=result.source_sha256,
            destination_sha256=result.destination_sha256,
            request_sha256=result.request_sha256,
            cancelled=cancelled,
        )

    def import_document(self, path, *, cancelled=None, progress=None, page_progress=None):
        def check():
            if cancelled is not None and cancelled.is_set():
                raise ArtifactError("cancelled")

        check()
        try:
            with self._serial():
                name = approval_name(path)
                response_path = self.transfers / (name + ".response")
                approval = read_approval(
                    self.selection,
                    path,
                    self.settings,
                    require_current=not os.path.lexists(response_path),
                )
                check()
                attempt_path = self.transfers / (name + ".attempt")
                batch_path = self.transfers / (approval["batch"] + ".active")
                if os.path.lexists(response_path):
                    value = _decode(
                        safe_read(
                            response_path, self.settings.destination.response_bytes * 6 + 4096
                        ),
                        max_depth=65,
                    )
                    if set(value) != {
                        "response",
                        "source_sha256",
                        "destination_sha256",
                        "request_sha256",
                    } or not isinstance(value["response"], dict):
                        raise ArtifactError("artifact_corrupt")
                    result = ServerResult(**value)
                else:
                    if os.path.lexists(attempt_path) or os.path.lexists(batch_path):
                        raise SelectionStopped()
                    # A process death from this point stops the batch, including queued siblings.
                    write_private(batch_path, {"reference": path})
                    token = None
                    if self.settings.credential_ref:
                        keychain = self.keychain
                        if keychain is None:
                            from runtime.server_keychain import ServerKeychain

                            keychain = ServerKeychain()
                        token = keychain.get(self.settings.credential_ref)
                    with self.store.source(path) as fd:
                        digest = hashlib.sha256()
                        while chunk := os.read(fd, 65536):
                            check()
                            digest.update(chunk)
                        if digest.hexdigest() != approval["sha256"]:
                            raise ArtifactError("access_denied")
                        os.lseek(fd, 0, os.SEEK_SET)
                        write_private(attempt_path, approval)
                        try:
                            result = asyncio.run(
                                parse_document(
                                    self.settings.destination,
                                    Path(path),
                                    token=token,
                                    cancelled=cancelled,
                                    progress=progress,
                                    transport=self.transport,
                                    source_fd=fd,
                                )
                            )
                        except DestinationError as error:
                            if not error.shared_failure:
                                with directory(self.transfers) as parent:
                                    os.unlink(batch_path.name, dir_fd=parent)
                            raise
                    write_private(response_path, asdict(result))
                    with directory(self.transfers) as parent:
                        os.unlink(batch_path.name, dir_fd=parent)
                        os.fsync(parent)
                if (
                    result.source_sha256 != approval["sha256"]
                    or result.destination_sha256 != self.settings.destination.identity
                    or result.request_sha256 != hashlib.sha256(REQUEST.encode()).hexdigest()
                ):
                    raise ArtifactError("artifact_corrupt")
                check()
                notify_progress(progress, "retaining")
                return self._retain(path, result, cancelled)
        except SelectionError:
            raise ArtifactError("access_denied") from None
        except DestinationError as error:
            check()
            raise ServerProcessingFailed(str(error)) from None
        except (ValueError, OSError):
            raise ArtifactError("parse_failed") from None
