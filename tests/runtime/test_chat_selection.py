"""Chat selection uses only the native dialog result and rolls back failed handoffs."""

import asyncio
import importlib
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import anyio

from runtime.selection import SelectionStore


class ChatSelectionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "Résumé ' $(echo nope).pdf"
        self.source.write_bytes(b"%PDF-1.4\nlocal-only\n")
        self.store = SelectionStore("claude-desktop", home=self.root / "home")
        self.store.prepare()

    def module(self):
        return importlib.import_module("runtime.chat_selection")

    async def test_selected_path_is_copied_and_retained_only_after_normal_handoff(self):
        m = self.module()

        async def choose():
            return self.source

        with patch.object(m, "choose", choose):
            async with m.LocalSelectionProvider(self.store).select() as reference:
                self.assertEqual(
                    (self.store.grant / reference).read_bytes(), self.source.read_bytes()
                )
                self.assertNotIn(str(self.source.parent), reference)
            self.assertTrue((self.store.grant / reference).exists())
        self.assertEqual(list(self.store.staging.iterdir()), [])

    async def test_user_cancel_never_copies_and_does_not_hold_publisher_lock(self):
        m = self.module()

        async def choose():
            with self.store.locked():
                pass
            return None

        with patch.object(m, "choose", choose):
            async with m.LocalSelectionProvider(self.store).select() as reference:
                self.assertIsNone(reference)
        self.assertEqual(list(self.store.grant.iterdir()), [])

    async def test_validation_error_and_cancellation_after_copy_remove_only_own_copy(self):
        m = self.module()
        previous = self.store.select(self.source)

        async def choose():
            return self.source

        for error in (ValueError("reject"), asyncio.CancelledError()):
            with patch.object(m, "choose", choose), self.assertRaises(type(error)):
                async with m.LocalSelectionProvider(self.store).select():
                    raise error
            self.assertEqual(
                [p.name for p in self.store.grant.iterdir()], [previous.reference.split("/")[0]]
            )
        self.assertEqual(self.source.read_bytes(), b"%PDF-1.4\nlocal-only\n")

    async def test_cancel_during_copy_waits_for_thread_and_rolls_back_publication_race(self):
        m = self.module()
        entered, release = threading.Event(), threading.Event()
        original = self.store.select

        def copying(path, *, cancelled):
            selected = original(path)
            entered.set()
            release.wait(3)
            self.assertTrue(cancelled())
            return selected

        async def choose():
            return self.source

        async def work():
            async with m.LocalSelectionProvider(self.store).select():
                self.fail("cancelled handoff returned a reference")

        with patch.object(m, "choose", choose), patch.object(self.store, "select", copying):
            task = asyncio.create_task(work())
            while not entered.is_set():
                await anyio.sleep(0.001)
            task.cancel()
            await anyio.sleep(0.01)
            self.assertFalse(task.done())
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(list(self.store.grant.iterdir()), [])

    async def test_cancel_before_copy_does_not_start_a_thread(self):
        m = self.module()
        with patch.object(self.store, "select", side_effect=AssertionError("must not copy")):
            with anyio.CancelScope() as scope:
                scope.cancel()
                await m.copy_selected(self.store, self.source)

    async def test_copy_failure_is_sanitized_by_provider(self):
        m = self.module()

        async def choose():
            return self.root / "missing.pdf"

        with patch.object(m, "choose", choose), self.assertRaises(ValueError):
            async with m.LocalSelectionProvider(self.store).select():
                self.fail("missing file accepted")

    async def test_chooser_process_decodes_only_bounded_local_output(self):
        m = self.module()
        for value, expected in ((str(self.source), self.source), (None, None)):
            code = f"print({json.dumps(json.dumps(value))})"
            with patch.object(m, "command", return_value=[sys.executable, "-c", code]):
                self.assertEqual(await m.choose(), expected)
        for code in (
            "print('x'*20000)",
            "import json; print(json.dumps('/'+'x'*10000+'.pdf'))",
            "print('not JSON')",
            "print('{}')",
            "print('42')",
            "print('\"relative.pdf\"')",
            "raise SystemExit(2)",
        ):
            with (
                patch.object(m, "command", return_value=[sys.executable, "-c", code]),
                self.assertRaises(ValueError),
            ):
                await m.choose()

    async def test_chooser_cancellation_reaps_real_child(self):
        m = self.module()
        pidfile = self.root / "pid"
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

    def test_dialog_has_fixed_owner_text_pdf_filter_and_no_clipboard(self):
        m = self.module()
        from unittest.mock import MagicMock

        root = MagicMock()
        with (
            patch("tkinter.Tk", return_value=root),
            patch("tkinter.filedialog.askopenfilename", return_value=str(self.source)) as dialog,
        ):
            self.assertEqual(m.dialog(), self.source)
        self.assertEqual(
            dialog.call_args.kwargs,
            {
                "parent": root,
                "title": "OpenReading: Choose one PDF",
                "filetypes": [("PDF documents", "*.pdf")],
            },
        )
        root.destroy.assert_called_once()
        root.clipboard_append.assert_not_called()

    def test_dialog_cancel_and_failure_destroy_native_owner(self):
        m = self.module()
        from unittest.mock import MagicMock

        for outcome in ("", RuntimeError("native failure")):
            root = MagicMock()
            with (
                patch("tkinter.Tk", return_value=root),
                patch(
                    "tkinter.filedialog.askopenfilename",
                    side_effect=outcome if isinstance(outcome, Exception) else None,
                    return_value=outcome,
                ),
            ):
                if isinstance(outcome, Exception):
                    with self.assertRaises(RuntimeError):
                        m.dialog()
                else:
                    self.assertIsNone(m.dialog())
            root.destroy.assert_called_once()

    def test_internal_command_is_fixed_for_source_and_frozen_launch(self):
        m = self.module()
        with patch.object(sys, "frozen", False, create=True):
            self.assertEqual(m.command(), [sys.executable, "-m", "runtime.chat_selection"])
        with patch.object(sys, "frozen", True, create=True):
            self.assertEqual(m.command(), [sys.executable, "--internal-select-file"])

    def test_dialog_cli_emits_only_reference_or_fixed_error(self):
        import contextlib
        import io

        m = self.module()
        for selected in (None, self.source):
            output = io.StringIO()
            with (
                patch.object(m, "dialog", return_value=selected),
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(m.main(), 0)
            self.assertEqual(json.loads(output.getvalue()), str(selected) if selected else None)
        output = io.StringIO()
        with (
            patch.object(m, "dialog", side_effect=ValueError("secret")),
            contextlib.redirect_stderr(output),
        ):
            self.assertEqual(m.main(), 2)
        self.assertNotIn("secret", output.getvalue())

    def test_chat_launcher_uses_private_intake_auto_ocr_and_leaves_settings_unchanged(self):
        from runtime.configuration import client_root
        from runtime.entrypoint import main

        base = client_root("claude-desktop", home=self.root / "home")
        for suffix in ("settings.json", "v2/settings.json"):
            path = base / suffix
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("historical settings unchanged")
        with (
            patch("runtime.entrypoint.sys.platform", "darwin"),
            patch("platform.machine", return_value="arm64"),
            patch.object(sys, "frozen", True, create=True),
            patch("runtime.entrypoint.verify_release", return_value={"format_version": "2"}),
            patch("pathlib.Path.home", return_value=self.root / "home"),
            patch("runtime.docling_profile.launch", return_value=0) as launch,
        ):
            self.assertEqual(main(["--client", "claude-desktop", "--chat-documents"]), 0)
        args = launch.call_args.args[0]
        self.assertEqual(args.input_root, self.store.grant)
        self.assertEqual(args.ocr, "true")
        self.assertIsInstance(
            launch.call_args.kwargs["selection_provider"], self.module().LocalSelectionProvider
        )
        for suffix in ("settings.json", "v2/settings.json"):
            self.assertEqual((base / suffix).read_text(), "historical settings unchanged")

    def test_chat_launcher_refuses_model_style_overrides_and_legacy_internal_dispatch(self):
        import contextlib
        import io

        from runtime.entrypoint import main

        with (
            patch("runtime.entrypoint.sys.platform", "darwin"),
            patch("platform.machine", return_value="arm64"),
            patch.object(sys, "frozen", True, create=True),
            patch("runtime.entrypoint.verify_release", return_value={"format_version": "2"}),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            for extra in (["--ocr", "false"], ["--input-root", str(self.root)], ["--configure"]):
                self.assertEqual(
                    main(["--client", "claude-desktop", "--chat-documents", *extra]), 2
                )
            with patch.object(self.module(), "main", return_value=0) as dialog:
                self.assertEqual(main(["--internal-select-file"]), 0)
                dialog.assert_called_once()
        with (
            patch("runtime.entrypoint.sys.platform", "darwin"),
            patch("platform.machine", return_value="arm64"),
            patch.object(sys, "frozen", True, create=True),
            patch("runtime.entrypoint.verify_release", return_value={}),
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit),
        ):
            main(["--internal-select-file"])
