"""Bind native upload approval to a destination revision and immutable selected copies.

Server selection uses the existing snapshot traversal with no adapter extension filter.
Native confirmation names the URL, every filename, document count and total byte count.
Approval records live outside the input grant. They contain hashes, sizes and a batch ID.
Changed settings or copied bytes require fresh native selection and confirmation.
Cancelled dialogs and failed handoffs revoke copies and their approvals together.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import uuid
from contextlib import asynccontextmanager

import anyio
from openreading.artifacts.intake import directory, source
from openreading.artifacts.limits import ArtifactError
from openreading.artifacts.store import safe_read

from runtime.chat_selection import LocalSelectionProvider, remove_copy
from runtime.destination_settings import read_destination
from runtime.native_selection import choose, copy_snapshot
from runtime.selection import SelectionError, SelectionStore, filename
from runtime.server_transport import UPLOAD_BYTES


class ServerSelectionStore(SelectionStore):
    def __init__(self, client, *, home=None, data_root=None):
        super().__init__(client, home=home, data_root=data_root)
        self.client, self.home = client, home
        self.extensions = None
        self.approvals = self.root.parent / "server/approvals"
        with directory(self.approvals, create=True) as opened:
            os.fchmod(opened, 0o700)

    def supports_name(self, name):
        return filename(name)


def approval_name(reference):
    parts = reference.split("/")
    if len(parts) != 2 or re.fullmatch(r"[a-f0-9]{32}", parts[0]) is None or not filename(parts[1]):
        raise SelectionError("Select and confirm this document again.")
    return hashlib.sha256(reference.encode()).hexdigest() + ".json"


def write_private(path, value):
    """Atomically persist a nonsecret record without following parent or final links."""
    data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    with directory(path.parent, create=True) as parent:
        os.fchmod(parent, 0o700)
        name = ".pending-" + uuid.uuid4().hex
        fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path.name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try:
                os.unlink(name, dir_fd=parent)
            except FileNotFoundError:
                pass


def selected_digest(store, reference):
    digest, length = hashlib.sha256(), 0
    with source(store.grant, reference) as fd:
        while chunk := os.read(fd, 65536):
            length += len(chunk)
            if length > UPLOAD_BYTES:
                raise SelectionError("A selected document exceeds the 100 MiB server upload limit.")
            digest.update(chunk)
    return digest.hexdigest(), length


def check_current(store, settings):
    try:
        current = read_destination(store.client, home=store.home)
    except ValueError:
        raise SelectionError(
            "The destination settings are invalid. Restart the connection and select documents again."
        ) from None
    # Advanced limits override the session budget without changing destination consent.
    if (
        settings.mode != "server"
        or current.mode != "server"
        or current.revision != settings.revision
        or current.destination.base_url != settings.destination.base_url
    ):
        raise SelectionError(
            "The destination changed. Quit and reopen your app, then select documents again."
        )


def read_approval(store, reference, settings, *, require_current=True):
    """Refuse unapproved, changed or stale copies before HTTP submission."""
    if require_current:
        check_current(store, settings)
    try:
        value = json.loads(safe_read(store.approvals / approval_name(reference), 8192))
        digest, length = selected_digest(store, reference)
        if (
            not isinstance(value, dict)
            or set(value) != {"reference", "revision", "destination", "sha256", "bytes", "batch"}
            or value["reference"] != reference
            or value["revision"] != settings.revision
            or value["destination"] != settings.destination.identity
            or value["sha256"] != digest
            or type(value["bytes"]) is not int
            or value["bytes"] != length
            or not isinstance(value["batch"], str)
            or re.fullmatch(r"[a-f0-9]{32}", value["batch"]) is None
        ):
            raise ValueError
        return value
    except (OSError, ArtifactError, ValueError, TypeError):
        raise SelectionError("Select and confirm this document again.") from None


def display_value(value):
    """Expose invisible controls and separators without letting data forge consent rows."""
    return "".join(
        (f"\\u{ord(character):04x}" if ord(character) <= 0xFFFF else f"\\U{ord(character):08x}")
        if unicodedata.category(character).startswith("C")
        or unicodedata.category(character) in {"Zl", "Zp"}
        else character
        for character in value
    )


async def confirm(url, documents):
    """Present a fixed native alert; document names enter as JSON data through stdin."""
    details = "\n".join(
        f"{display_value(row['name'])} ({row['bytes']:,} bytes)" for row in documents
    )
    noun = "document" if len(documents) == 1 else "documents"
    message = f"Add {len(documents)} {noun} ({sum(row['bytes'] for row in documents):,} bytes) for processing at {display_value(url)}?\nChoose Process in chat to send them. The server may use external providers. Local cancellation cannot stop submitted server processing."
    # Substitute once so marker-like text in URLs and filenames stays literal data.
    values = {"__MESSAGE__": json.dumps(message), "__DETAILS__": json.dumps(details)}
    script = """ObjC.import('AppKit');
var app = $.NSApplication.sharedApplication;
app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);
var alert = $.NSAlert.alloc.init;
alert.messageText = 'Add selected documents?';
alert.informativeText = __MESSAGE__;
alert.addButtonWithTitle('Cancel');
alert.addButtonWithTitle('Add files');
var scroll = $.NSScrollView.alloc.initWithFrame($.NSMakeRect(0, 0, 560, 240));
scroll.hasVerticalScroller = true;
var text = $.NSTextView.alloc.initWithFrame($.NSMakeRect(0, 0, 540, 240));
text.editable = false;
text.verticallyResizable = true;
text.string = __DETAILS__;
scroll.documentView = text;
alert.accessoryView = scroll;
app.activateIgnoringOtherApps(true);
JSON.stringify(alert.runModal == $.NSAlertSecondButtonReturn);
"""
    script = re.sub(r"__MESSAGE__|__DETAILS__", lambda match: values[match[0]], script)
    result = await anyio.run_process(
        ["/usr/bin/osascript", "-l", "JavaScript", "-"], input=script.encode(), check=False
    )
    if result.returncode or result.stdout.strip() not in {b"true", b"false"}:
        raise SelectionError("Cannot confirm server transfer. Nothing was uploaded.")
    return result.stdout.strip() == b"true"


class ServerSelectionProvider(LocalSelectionProvider):
    def __init__(self, store, settings):
        super().__init__(store)
        self.settings = settings

    @asynccontextmanager
    async def select(self):
        check_current(self.store, self.settings)
        result, keep = None, False
        try:
            paths = await choose(None)
            if paths is not None:
                result = await copy_snapshot(self.store, paths)
                records, details = [], []
                batch = uuid.uuid4().hex
                for reference in result["references"]:
                    digest, length = await anyio.to_thread.run_sync(
                        selected_digest, self.store, reference
                    )
                    records.append(
                        {
                            "reference": reference,
                            "revision": self.settings.revision,
                            "destination": self.settings.destination.identity,
                            "sha256": digest,
                            "bytes": length,
                            "batch": batch,
                        }
                    )
                    details.append({"name": reference.split("/", 1)[1], "bytes": length})
                if records:
                    if not await confirm(self.settings.destination.base_url, details):
                        yield None
                        return
                    check_current(self.store, self.settings)
                    for record in records:
                        write_private(
                            self.store.approvals / approval_name(record["reference"]), record
                        )
            yield result
            keep = True
        finally:
            if result is not None and not keep:
                with anyio.CancelScope(shield=True):
                    for reference in result["references"]:
                        try:
                            with directory(self.store.approvals) as opened:
                                try:
                                    os.unlink(approval_name(reference), dir_fd=opened)
                                except FileNotFoundError:
                                    pass
                        except (OSError, ArtifactError):
                            # The safe directory opener wraps filesystem refusals in ArtifactError.
                            # Approval cleanup must not prevent revoking any selected copy.
                            pass
                        await remove_copy(self.store, reference)
