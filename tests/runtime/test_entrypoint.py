"""The launcher checks integrity before dispatch and keeps client grants explicit."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.entrypoint import main
from runtime.verify import ReleaseIntegrityError


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("runtime.entrypoint.sys.platform", "darwin"))
        self.enterContext(patch("platform.machine", return_value="arm64"))
        self.enterContext(patch("runtime.entrypoint.sys.frozen", True, create=True))

    def test_background_dispatch_follows_integrity_and_telemetry_setup(self):
        import os
        import sys
        from types import SimpleNamespace

        events = []

        def verify(root):
            events.append("verified")
            return {"format_version": "2"}

        def job(args):
            self.assertEqual(events, ["verified"])
            self.assertEqual(os.environ["ORT_DISABLE_TELEMETRY"], "1")
            self.assertEqual(args, ["/private/job"])
            return 0

        with (
            patch("runtime.entrypoint.verify_release", side_effect=verify),
            patch.dict(sys.modules, {"openreading.artifacts.jobs": SimpleNamespace(main=job)}),
            patch.dict(os.environ, {"ORT_DISABLE_TELEMETRY": "0"}),
        ):
            self.assertEqual(main(["--internal-artifact-job", "/private/job"]), 0)

    def test_bad_inventory_refuses_even_version_probe(self):
        with (
            patch(
                "runtime.entrypoint.verify_release",
                side_effect=ReleaseIntegrityError("invalid"),
            ),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(["--version"]), 2)

    def test_version_reports_metadata_without_starting_core(self):
        output = io.StringIO()
        with (
            patch(
                "runtime.entrypoint.verify_release",
                return_value={
                    "release_version": "0.1.0",
                    "core_commit": "a" * 40,
                    "worker_sha256": "b" * 64,
                },
            ),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(main(["--version"]), 0)
        self.assertIn('"core_commit": "' + "a" * 40, output.getvalue())

    def test_setup_and_launch_use_persisted_grant(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            grant = root / "documents"
            grant.mkdir()
            with (
                patch("runtime.entrypoint.verify_release", return_value={}),
                patch("pathlib.Path.home", return_value=root),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(main(["--client", "codex"]), 2)
                self.assertEqual(main(["--client", "codex", "--configure"]), 2)
                self.assertEqual(
                    main(["--client", "codex", "--configure", "--input-root", str(grant)]),
                    0,
                )
                with patch("openreading.mcp_server.main.main", return_value=0) as launch:
                    self.assertEqual(main(["--client", "codex"]), 0)
                    self.assertEqual(launch.call_args.args[0][3], str(grant))
                with patch("openreading.artifacts.worker.main", return_value=0) as worker:
                    self.assertEqual(
                        main(["--internal-artifact-worker", "--job-file", "job.json"]),
                        0,
                    )
                    self.assertEqual(worker.call_args.args[0], ["--job-file", "job.json"])

    def test_unsupported_host_refuses_before_inventory_or_document_access(self):
        for operating_system, machine in [("linux", "arm64"), ("darwin", "x86_64")]:
            with (
                self.subTest(os=operating_system, machine=machine),
                patch("runtime.entrypoint.sys.platform", operating_system),
                patch("platform.machine", return_value=machine),
                patch(
                    "runtime.entrypoint.verify_release",
                    return_value={
                        "release_version": "0.1.0",
                        "core_commit": "a" * 40,
                        "worker_sha256": "b" * 64,
                    },
                ) as verify,
                contextlib.redirect_stderr(io.StringIO()) as output,
            ):
                self.assertEqual(main(["--version"]), 2)
                verify.assert_not_called()
                self.assertIn("Apple Silicon", output.getvalue())

    def test_source_launch_reports_packaging_requirement(self):
        with (
            patch("runtime.entrypoint.sys.frozen", False, create=True),
            patch(
                "runtime.entrypoint.verify_release",
                return_value={
                    "release_version": "0.1.0",
                    "core_commit": "a" * 40,
                    "worker_sha256": "b" * 64,
                },
            ) as verify,
            contextlib.redirect_stderr(io.StringIO()) as output,
        ):
            self.assertEqual(main(["--version"]), 2)
            verify.assert_not_called()
            self.assertIn("packaged", output.getvalue())

    def test_selection_server_uses_private_intake_without_overwriting_saved_grants(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            client = root / "Library/Application Support/OpenReading/agent-tools/claude-desktop"
            (client / "v2").mkdir(parents=True)
            saved = [client / "config.json", client / "v2/config.json"]
            for path in saved:
                path.write_bytes(b"existing settings must not be read or replaced")
            with (
                patch("runtime.entrypoint.verify_release", return_value={"format_version": "2"}),
                patch("pathlib.Path.home", return_value=root),
                patch("runtime.docling_profile.launch", return_value=0) as launch,
            ):
                self.assertEqual(
                    main(["--client", "claude-desktop", "--selected-documents", "--ocr", "false"]),
                    0,
                )
                args = launch.call_args.args[0]
                self.assertEqual(
                    args.input_root,
                    root
                    / "Library/Application Support/OpenReading/agent-tools/claude-desktop/v2/selection/ready",
                )
                self.assertTrue(args.input_root.is_dir())
                for path in saved:
                    self.assertEqual(
                        path.read_bytes(), b"existing settings must not be read or replaced"
                    )
                for forbidden in (["--input-root", str(root)], ["--configure"]):
                    with contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(
                            main(
                                ["--client", "claude-desktop", "--selected-documents", *forbidden]
                            ),
                            2,
                        )

    def test_picker_dispatch_has_no_source_or_settings_override(self):
        with (
            patch("runtime.entrypoint.verify_release", return_value={"format_version": "2"}),
            patch("runtime.selection_ui.run", return_value=0) as picker,
        ):
            self.assertEqual(main(["--client", "claude-desktop", "--select-document"]), 0)
            picker.assert_called_once()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main(["--client", "claude-desktop", "--select-document", "--ocr", "true"]), 2
                )

    def test_selection_startup_does_not_wait_for_publisher(self):
        from threading import Event, Thread

        from runtime.selection import SelectionStore

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            store = SelectionStore("claude-desktop", home=root)
            held, release = Event(), Event()

            def copy_in_progress():
                with store.locked():
                    held.set()
                    release.wait(5)

            worker = Thread(target=copy_in_progress)
            worker.start()
            try:
                self.assertTrue(held.wait(2))
                with (
                    patch(
                        "runtime.entrypoint.verify_release", return_value={"format_version": "2"}
                    ),
                    patch("pathlib.Path.home", return_value=root),
                    patch("runtime.docling_profile.launch", return_value=0) as launch,
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(
                        main(["--client", "claude-desktop", "--selected-documents"]), 0
                    )
                    launch.assert_called_once()
            finally:
                release.set()
                worker.join(2)

    def test_destination_settings_and_server_child_require_verified_v2(self):
        with (
            patch(
                "runtime.entrypoint.verify_release", return_value={"format_version": "2"}
            ) as verify,
            patch("runtime.destination_ui.run", return_value=0) as settings,
        ):
            self.assertEqual(main(["--client", "chatgpt", "--destination-settings"]), 0)
            settings.assert_called_once_with("chatgpt")
            verify.assert_called_once()
        with (
            patch("runtime.entrypoint.verify_release", return_value={"format_version": "2"}),
            patch("runtime.server_profile.job_main", return_value=0) as child,
        ):
            self.assertEqual(main(["--internal-server-job", "/private/job"]), 0)
            self.assertEqual(child.call_args.args[0], ["/private/job"])
        with (
            patch("runtime.entrypoint.verify_release", return_value={"format_version": "2"}),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(
                main(
                    ["--client", "chatgpt", "--destination-settings", "--input-root", "/documents"]
                ),
                2,
            )

    def test_chat_destination_default_local_and_explicit_server_dispatch(self):
        from runtime.destination_settings import save_destination

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            with (
                patch("pathlib.Path.home", return_value=home),
                patch("runtime.entrypoint.verify_release", return_value={"format_version": "2"}),
                patch("runtime.docling_profile.launch", return_value=0) as local,
                patch("runtime.server_profile.launch", return_value=0) as server,
                patch("runtime.native_selection.adapter_extensions", return_value=("pdf",)),
            ):
                self.assertEqual(main(["--client", "chatgpt", "--chat-documents"]), 0)
                local.assert_called_once()
                server.assert_not_called()
                setting = save_destination("chatgpt", "server", base_url="http://localhost:8787")
                self.assertEqual(main(["--client", "chatgpt", "--chat-documents"]), 0)
                self.assertEqual(server.call_args.args[2], setting)
                self.assertEqual(local.call_count, 1)
                next(home.rglob("destination.json")).write_text("broken")
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(["--client", "chatgpt", "--chat-documents"]), 2)
                self.assertEqual(server.call_count, 1)
