"""Server selection requires native consent bound to immutable selected bytes."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from runtime.destination_settings import save_destination
from runtime.selection import SelectionError


class ServerSelectionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.server_selection"),
            "Missing server selection",
        )
        from runtime.server_selection import (
            ServerSelectionProvider,
            ServerSelectionStore,
        )

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.settings = save_destination(
            "chatgpt", "server", base_url="http://localhost:8787", home=self.home
        )
        self.store = ServerSelectionStore("chatgpt", home=self.home)
        self.provider = ServerSelectionProvider(self.store, self.settings)
        self.source = self.home / "unlisted.custom"
        self.source.write_bytes(b"synthetic chosen bytes")

    async def test_consent_binds_destination_names_count_bytes_and_digest(self):
        from runtime.server_selection import read_approval

        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.confirm", AsyncMock(return_value=True)) as confirm,
        ):
            async with self.provider.select() as result:
                reference = result["references"][0]
        details = confirm.call_args.args[1]
        self.assertEqual(details, [{"name": "unlisted.custom", "bytes": 22}])
        self.assertEqual(confirm.call_args.args[0], "http://localhost:8787")
        approved = read_approval(self.store, reference, self.settings)
        self.assertEqual(approved["bytes"], 22)
        self.assertEqual(approved["revision"], self.settings.revision)
        self.assertEqual(len(approved["sha256"]), 64)
        self.assertEqual(len(approved["batch"]), 32)
        self.assertTrue(self.store.supports_name("no-extension"))
        self.assertFalse(self.store.supports_name("../bad"))

    async def test_rejected_consent_rolls_back_and_never_publishes_authorization(self):
        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.confirm", AsyncMock(return_value=False)),
        ):
            async with self.provider.select() as result:
                self.assertIsNone(result)
        self.assertEqual(list(self.store.grant.iterdir()), [])
        self.assertEqual(list(self.store.approvals.iterdir()), [])

    async def test_settings_change_during_confirmation_invalidates_new_and_old_selection(
        self,
    ):
        from runtime.server_selection import read_approval

        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.confirm", AsyncMock(return_value=True)),
        ):
            async with self.provider.select() as result:
                reference = result["references"][0]
        save_destination("chatgpt", "local", home=self.home)
        with self.assertRaises(SelectionError):
            read_approval(self.store, reference, self.settings)
        with self.assertRaises(SelectionError):
            async with self.provider.select():
                self.fail("Stale connection cannot select")

    async def test_changed_bytes_and_unapproved_references_refuse_upload(self):
        from runtime.server_selection import read_approval

        selection = self.store.select(self.source)
        with self.assertRaises(SelectionError):
            read_approval(self.store, selection.reference, self.settings)
        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.confirm", AsyncMock(return_value=True)),
        ):
            async with self.provider.select() as result:
                reference = result["references"][0]
        (self.store.grant / reference).write_bytes(b"replacement")
        with self.assertRaises(SelectionError):
            read_approval(self.store, reference, self.settings)

    async def test_cancel_empty_and_host_delivery_failure_do_not_leave_approval(self):
        with patch("runtime.server_selection.choose", AsyncMock(return_value=None)):
            async with self.provider.select() as result:
                self.assertIsNone(result)
        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.confirm", AsyncMock(return_value=True)),
        ):
            with self.assertRaisesRegex(RuntimeError, "host disconnected"):
                async with self.provider.select():
                    raise RuntimeError("host disconnected")
        self.assertEqual(list(self.store.grant.iterdir()), [])
        self.assertEqual(list(self.store.approvals.iterdir()), [])

    async def test_cleanup_removes_snapshot_when_approval_directory_is_unreadable(self):
        broken = patch("runtime.server_selection.directory", side_effect=OSError)
        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.confirm", AsyncMock(return_value=True)),
        ):
            try:
                with self.assertRaisesRegex(RuntimeError, "host disconnected"):
                    async with self.provider.select():
                        broken.start()
                        raise RuntimeError("host disconnected")
            finally:
                broken.stop()
        self.assertEqual(list(self.store.grant.iterdir()), [])

    async def test_confirmation_uses_stdin_json_and_refuses_errors(self):
        from types import SimpleNamespace

        from runtime.server_selection import confirm

        documents = [{"name": "quote'\".pdf", "bytes": 5}]
        for output, status, expected in (
            (b"true\n", 0, True),
            (b"false\n", 0, False),
            (b"bad", 0, None),
            (b"true", 1, None),
        ):
            with patch(
                "runtime.server_selection.anyio.run_process",
                AsyncMock(return_value=SimpleNamespace(stdout=output, returncode=status)),
            ) as process:
                if expected is None:
                    with self.assertRaises(SelectionError):
                        await confirm("http://localhost", documents)
                else:
                    self.assertEqual(await confirm("http://localhost", documents), expected)
                args = process.call_args.args[0]
                self.assertEqual(args, ["/usr/bin/osascript", "-l", "JavaScript", "-"])
                script = process.call_args.kwargs["input"].decode()
                self.assertIn("external providers", script)
                self.assertIn("1 document (5 bytes)", script)
                self.assertIn("NSAlertSecondButtonReturn", script)

    async def test_change_while_confirmation_open_and_oversized_input_roll_back(self):
        async def change(*args):
            save_destination("chatgpt", "local", home=self.home)
            return True

        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.confirm", change),
        ):
            with self.assertRaises(SelectionError):
                async with self.provider.select():
                    self.fail("No stale consent")
        self.assertEqual(list(self.store.grant.iterdir()), [])
        self.settings = save_destination(
            "chatgpt", "server", base_url="http://localhost:8787", home=self.home
        )
        self.provider.settings = self.settings
        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.source])),
            patch("runtime.server_selection.UPLOAD_BYTES", 1),
        ):
            with self.assertRaises(SelectionError):
                async with self.provider.select():
                    self.fail("No oversized upload consent")
        self.assertEqual(list(self.store.grant.iterdir()), [])

    async def test_empty_snapshot_returns_skips_without_confirmation(self):
        with (
            patch("runtime.server_selection.choose", AsyncMock(return_value=[self.home])),
            patch(
                "runtime.server_selection.copy_snapshot",
                AsyncMock(return_value={"references": (), "skipped": {"symlink": 1}}),
            ),
            patch("runtime.server_selection.confirm", AsyncMock()) as confirm,
        ):
            async with self.provider.select() as result:
                self.assertEqual(result["skipped"], {"symlink": 1})
            confirm.assert_not_called()

    async def test_confirmation_preserves_template_markers_as_literal_user_data(self):
        import json
        import subprocess
        from types import SimpleNamespace

        from runtime.server_selection import confirm

        url = "http://localhost/__DETAILS__"
        documents = [
            {
                "name": 'quote"__MESSAGE____DETAILS__\u2028fake.txt\u2029end\u202e.pdf',
                "bytes": 5,
            }
        ]
        with patch(
            "runtime.server_selection.anyio.run_process",
            AsyncMock(return_value=SimpleNamespace(stdout=b"true", returncode=0)),
        ) as process:
            self.assertTrue(await confirm(url, documents))
        script = process.call_args.kwargs["input"].decode()
        # Execute the generated JavaScript without opening AppKit or a native dialog.
        harness = """
const captured = {};
const stubAlert = {addButtonWithTitle() {}, runModal: 1001,
  set informativeText(value) { captured.message = value; }};
const stubText = {set string(value) { captured.details = value; }};
const ObjC = {import() {}};
const $ = {
  NSApplication: {sharedApplication: {setActivationPolicy() {},
    activateIgnoringOtherApps() {}}},
  NSAlert: {alloc: {init: stubAlert}}, NSAlertSecondButtonReturn: 1001,
  NSScrollView: {alloc: {initWithFrame() { return {}; }}},
  NSTextView: {alloc: {initWithFrame() { return stubText; }}},
  NSMakeRect() {}
};
"""
        result = subprocess.run(
            ["node", "-"],
            input=harness + script + "\nconsole.log(JSON.stringify(captured));",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        displayed = json.loads(result.stdout)
        self.assertIn(url, displayed["message"])
        self.assertEqual(
            displayed["details"],
            'quote"__MESSAGE____DETAILS__\\u2028fake.txt\\u2029end\\u202e.pdf (5 bytes)',
        )


class DisplayValueTests(unittest.TestCase):
    def test_controls_and_line_separators_are_visible_without_rewriting_other_text(self):
        from runtime.server_selection import display_value

        self.assertEqual(
            display_value("café\n\u2028\u2029\u202e\U000e0001"),
            "café\\u000a\\u2028\\u2029\\u202e\\U000e0001",
        )
