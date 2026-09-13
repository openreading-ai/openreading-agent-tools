"""Return an OS-selected file to core without a clipboard or model-controlled dialog.

LocalSelectionProvider implements core's optional async context-manager seam structurally.
Core owns admission, deadlines, validation, and protocol errors. This provider opens a
fixed PDF chooser in a child, then copies only its result through runtime.selection.
No publisher lock is held while the user chooses. No arguments alter dialog text or scope.
The child is killed and reaped on cancellation. Copy cancellation waits for its thread,
then removes a copy published in the cancellation race before returning control to core.
An exceptional context exit removes only this call's intake copy, not retained artifacts.
Rollback revokes its immutable published entry without the publisher lock. Failed deletion
leaves an unreadable discarded copy for the next publisher sweep. Cleanup failures emit a
fixed stderr diagnostic without replacing the original cancellation, deadline, or error.

The OS chooser's Cancel works independently of a host's Stop button. Host Stop without
MCP cancellation leaves the chooser active until local Cancel or core's finite deadline.
Source execution supports development probes only. Frozen dispatch verifies its inventory
before --internal-select-file. Nothing here claims native focus or installation acceptance.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
from anyio.lowlevel import checkpoint

from runtime.selection import Selection, SelectionStore


def command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--internal-select-file"]
    return [sys.executable, "-m", "runtime.chat_selection"]


async def choose() -> Path | None:
    # Native UI runs on its own main thread. Killing the child dismisses an unresponsive dialog.
    process = await anyio.open_process(
        command(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    try:
        output = bytearray()
        assert process.stdout is not None
        while True:
            try:
                data = await process.stdout.receive(8192)
            except anyio.EndOfStream:
                break
            output.extend(data)
            if len(output) > 8192:
                raise ValueError("Invalid local chooser response.")
        if await process.wait() != 0:
            raise ValueError("The local chooser could not open.")
        value = json.loads(output)
        if value is None:
            return None
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError("Invalid local chooser response.")
        return Path(value)
    finally:
        with anyio.CancelScope(shield=True):
            if process.returncode is None:
                process.kill()
            await process.aclose()


async def remove_copy(store: SelectionStore, reference: str) -> None:
    with anyio.CancelScope(shield=True):
        try:
            await anyio.to_thread.run_sync(store.rollback, reference)
        except Exception:
            print("Selection cleanup failed; private intake may require clearing.", file=sys.stderr)


async def copy_selected(store: SelectionStore, path: Path) -> Selection:
    await checkpoint()
    cancelled = threading.Event()

    def work():
        try:
            return store.select(path, cancelled=cancelled.is_set)
        except Exception as error:
            return error

    future = asyncio.get_running_loop().run_in_executor(None, work)
    try:
        result = await asyncio.shield(future)
    except anyio.get_cancelled_exc_class():
        cancelled.set()
        with anyio.CancelScope(shield=True):
            result = await asyncio.shield(future)
            if isinstance(result, Selection):
                await remove_copy(store, result.reference)
        raise
    if isinstance(result, Exception):
        raise result
    return result


class LocalSelectionProvider:
    def __init__(self, store: SelectionStore):
        self.store = store

    @asynccontextmanager
    async def select(self):
        selected = None
        try:
            path = await choose()
            if path is not None:
                selected = await copy_selected(self.store, path)
            await checkpoint()
            yield selected.reference if selected else None
        except BaseException:
            if selected is not None:
                await remove_copy(self.store, selected.reference)
            raise


def dialog() -> Path | None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    try:
        root.withdraw()
        root.attributes("-topmost", True)
        root.update()
        # macOS turns an explicit parent into an attached sheet. The owner is hidden,
        # so let the OS position a standalone dialog instead of anchoring it off-screen.
        selected = filedialog.askopenfilename(
            title="OpenReading: Choose one PDF",
            filetypes=[("PDF documents", "*.pdf")],
        )
        return Path(selected) if selected else None
    finally:
        root.destroy()


def main() -> int:
    try:
        selected = dialog()
        print(json.dumps(str(selected) if selected is not None else None))
        return 0
    except Exception:
        print("Local document chooser failed.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
