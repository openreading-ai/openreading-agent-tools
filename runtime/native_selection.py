"""Use one fixed macOS file-and-folder panel for snapshot selection.

The system JXA interpreter only presents NSOpenPanel and serializes the user's choices.
No document, path, model argument or setting is interpolated into its script. Cancellation
kills and reaps the dialog process. Snapshot copying runs in an owned thread; cancellation
waits for rollback before releasing the selection slot. No native acceptance is implied.
The older single-file developer picker remains in runtime.chat_selection.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
from anyio.lowlevel import checkpoint

from runtime.chat_selection import LocalSelectionProvider, remove_copy
from runtime.snapshot_selection import snapshot

_SCRIPT = """ObjC.import('AppKit');
var app = $.NSApplication.sharedApplication;
app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);
var panel = $.NSOpenPanel.openPanel;
panel.title = 'OpenReading: Choose PDFs or folders';
panel.message = 'Selected PDFs are copied locally. Folders include nested PDFs, excluding hidden entries, packages and symbolic links.';
panel.canChooseFiles = true;
panel.canChooseDirectories = true;
panel.allowsMultipleSelection = true;
panel.resolvesAliases = false;
panel.allowedFileTypes = ['pdf'];
panel.treatsFilePackagesAsDirectories = false;
app.activateIgnoringOtherApps(true);
var result = null;
if (panel.runModal == $.NSModalResponseOK) {
    result = [];
    var urls = panel.URLs;
    for (var i = 0; i < urls.count; i++) result.push(ObjC.unwrap(urls.objectAtIndex(i).path));
}
JSON.stringify(result);
"""


def command() -> list[str]:
    return ["/usr/bin/osascript", "-l", "JavaScript", "-e", _SCRIPT]


async def choose() -> list[Path] | None:
    process = await anyio.open_process(
        command(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    try:
        output = bytearray()
        if process.stdout is None:
            raise ValueError("The local chooser could not open.")
        while True:
            try:
                output.extend(await process.stdout.receive(65536))
            except anyio.EndOfStream:
                break
        if await process.wait() != 0:
            raise ValueError("The local chooser could not open.")
        value = json.loads(output)
        if value is None:
            return None
        if (
            not isinstance(value, list)
            or not value
            or any(
                not isinstance(p, str)
                or not Path(p).is_absolute()
                or len(p.encode()) > 8192
                or "\x00" in p
                for p in value
            )
        ):
            raise ValueError("Invalid local chooser response.")
        return [Path(p) for p in value]
    finally:
        with anyio.CancelScope(shield=True):
            if process.returncode is None:
                process.kill()
            await process.aclose()


async def copy_snapshot(store, paths):
    await checkpoint()
    cancelled = threading.Event()

    def work():
        try:
            return snapshot(store, paths, cancelled=cancelled.is_set)
        except Exception as error:
            return error

    future = asyncio.get_running_loop().run_in_executor(None, work)
    try:
        result = await asyncio.shield(future)
    except anyio.get_cancelled_exc_class():
        cancelled.set()
        with anyio.CancelScope(shield=True):
            result = await asyncio.shield(future)
            if isinstance(result, dict):
                for reference in result["references"]:
                    await remove_copy(store, reference)
        raise
    if isinstance(result, Exception):
        raise result
    return result


class SnapshotSelectionProvider(LocalSelectionProvider):
    @asynccontextmanager
    async def select(self):
        result = None
        try:
            paths = await choose()
            if paths is not None:
                result = await copy_snapshot(self.store, paths)
            await checkpoint()
            yield result
        except BaseException:
            if result is not None:
                for reference in result["references"]:
                    await remove_copy(self.store, reference)
            raise
