"""The multiple-selection chooser has fixed scope and no model-provided script content."""

import asyncio
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.selection import SelectionStore


class NativeSelectionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "One.pdf"
        self.source.write_bytes(b"%PDF-one")
        self.store = SelectionStore("claude-desktop", home=self.root / "home")
        self.store.prepare()

    def module(self):
        return importlib.import_module("runtime.native_selection")

    async def test_chooser_decodes_only_absolute_paths_and_cancel(self):
        m = self.module()
        for value in [None, [str(self.source), str(self.root)]]:
            code = "print(" + repr(json.dumps(value)) + ")"
            with patch.object(m, "command", return_value=[sys.executable, "-c", code]):
                result = await m.choose()
            self.assertEqual(result, None if value is None else [Path(v) for v in value])
        for value in [[], 4, ["relative.pdf"], [3], {}, ["/" + "x" * 9000]]:
            code = "print(" + repr(json.dumps(value)) + ")"
            with (
                patch.object(m, "command", return_value=[sys.executable, "-c", code]),
                self.assertRaises(ValueError),
            ):
                await m.choose()

    async def test_provider_rolls_back_copies_on_validation_failure(self):
        m = self.module()

        async def choose(extensions):
            return [self.source]

        with patch.object(m, "choose", choose):
            with self.assertRaises(ValueError):
                async with m.SnapshotSelectionProvider(self.store).select() as batch:
                    self.assertEqual(len(batch["references"]), 1)
                    raise ValueError("core rejected receipt")
        self.assertEqual(list(self.store.grant.iterdir()), [])

    async def test_provider_retains_success_and_handles_cancel(self):
        m = self.module()

        async def choose(extensions):
            return [self.source]

        with patch.object(m, "choose", choose):
            async with m.SnapshotSelectionProvider(self.store).select() as batch:
                self.assertEqual(len(batch["references"]), 1)
        self.assertEqual(len(list(self.store.grant.iterdir())), 1)

        async def cancel(extensions):
            return None

        with patch.object(m, "choose", cancel):
            async with m.SnapshotSelectionProvider(self.store).select() as batch:
                self.assertIsNone(batch)

    def test_script_scope_is_fixed_and_uses_one_native_panel(self):
        m = self.module()
        command = m.command()
        self.assertEqual(command[:3], ["/usr/bin/osascript", "-l", "JavaScript"])
        self.assertIn("canChooseFiles = true", command[-1])
        self.assertIn("canChooseDirectories = true", command[-1])
        self.assertIn("allowsMultipleSelection = true", command[-1])
        self.assertNotIn("doShellScript", command[-1])

    def test_adapter_formats_are_forwarded_without_a_packaging_copy(self):
        from types import SimpleNamespace

        stub = SimpleNamespace(selection_extensions=lambda: ("png", "md", "pdf"))
        with patch.dict(sys.modules, {"openreading.adapters.docling_local.formats": stub}):
            self.assertEqual(self.module().adapter_extensions(), ("md", "pdf", "png"))

    def test_script_uses_only_validated_operator_formats(self):
        m = self.module()
        script = m.command(("docx", "md", "png"))[-1]
        self.assertIn('panel.allowedFileTypes = ["docx", "md", "png"]', script)
        self.assertNotIn("Choose PDFs", script)
        with self.assertRaises(ValueError):
            m.command(("pdf']; doShellScript('bad')",))

    async def test_cancel_during_copy_waits_and_revokes_publication_race(self):
        import threading

        import anyio

        m = self.module()
        entered, release = threading.Event(), threading.Event()

        def copying(store, paths, *, cancelled):
            selected = store.select(paths[0])
            entered.set()
            release.wait(3)
            self.assertTrue(cancelled())
            return {"references": (selected.reference,), "skipped": {}}

        with patch.object(m, "snapshot", copying):
            task = asyncio.create_task(m.copy_snapshot(self.store, [self.source]))
            while not entered.is_set():
                await anyio.sleep(0.001)
            task.cancel()
            await anyio.sleep(0.01)
            self.assertFalse(task.done())
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(list(self.store.grant.iterdir()), [])

    async def test_copy_failure_and_pre_cancel_do_not_publish(self):
        import anyio

        m = self.module()
        with self.assertRaises(ValueError):
            await m.copy_snapshot(self.store, [Path("relative.pdf")])
        with patch.object(m, "snapshot", side_effect=AssertionError("must not run")):
            with anyio.CancelScope() as scope:
                scope.cancel()
                await m.copy_snapshot(self.store, [self.source])
        with patch.object(m, "choose", side_effect=ValueError("chooser failed")):
            with self.assertRaises(ValueError):
                async with m.SnapshotSelectionProvider(self.store).select():
                    self.fail("no result expected")

    async def test_cancelled_native_child_is_reaped_and_errors_are_refused(self):
        import os

        import anyio

        m = self.module()
        pidfile = self.root / "child.pid"
        code = f"import os,time; from pathlib import Path; Path({str(pidfile)!r}).write_text(str(os.getpid())); time.sleep(30)"
        with patch.object(m, "command", return_value=[sys.executable, "-c", code]):
            task = asyncio.create_task(m.choose())
            while not pidfile.exists():
                await anyio.sleep(0.001)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        with self.assertRaises(ProcessLookupError):
            os.kill(int(pidfile.read_text()), 0)
        for code in ["raise SystemExit(2)", 'print("not json")']:
            with (
                patch.object(m, "command", return_value=[sys.executable, "-c", code]),
                self.assertRaises(ValueError),
            ):
                await m.choose()
