"""The server-only connector refuses local parsing and preserves saved server settings."""

import importlib
import importlib.util
import io
import tempfile
import unittest
from contextlib import nullcontext, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime.destination_settings import read_destination, save_destination


class ServerOnlyTests(unittest.TestCase):
    def connector_config(self):
        return {
            "catalogs": {"--chat-documents": {"tools": []}, "--settings-tools": {"tools": []}},
            "instructions": {"--chat-documents": "Require consent.", "--settings-tools": None},
        }

    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime.server_entrypoint"))
        return importlib.import_module("runtime.server_entrypoint")

    def test_cli_failure_never_prints_exception_text_or_traceback(self):
        from openreading.artifacts.limits import ArtifactError

        module = self.module()
        self.assertTrue(
            callable(getattr(module, "cli", None)), "Missing sanitized dispatch boundary"
        )
        for error in (
            OSError("/private/synthetic-secret"),
            ValueError("synthetic-secret"),
            RuntimeError("synthetic-secret"),
            ArtifactError("access_denied"),
        ):
            with self.subTest(error=type(error).__name__), redirect_stderr(io.StringIO()) as stderr:
                with patch.object(module, "main", side_effect=error):
                    self.assertEqual(module.cli([]), 2)
                self.assertTrue(stderr.getvalue())
                self.assertNotIn("synthetic-secret", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())
        with (
            patch.object(module, "main", side_effect=KeyboardInterrupt),
            redirect_stderr(io.StringIO()) as stderr,
        ):
            self.assertEqual(module.cli([]), 130)
            self.assertEqual(stderr.getvalue(), "")

    def test_storage_failure_has_safe_child_status_without_changing_public_exit(self):
        module = self.module()
        self.assertTrue(
            callable(getattr(module, "cli", None)), "Missing sanitized dispatch boundary"
        )
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("pathlib.Path.home", return_value=Path(temporary).resolve()),
        ):
            save_destination("codex", "server", base_url="http://localhost:8787")
            for argv, expected in (([], 2), (["--internal-startup-status"], 72)):
                with (
                    self.subTest(argv=argv),
                    patch.object(
                        module,
                        "main",
                        side_effect=lambda _: module.launch(
                            SimpleNamespace(client="codex", document_response_bytes=None), {}
                        ),
                    ),
                    patch.object(
                        module,
                        "storage_session",
                        side_effect=PermissionError("/private/synthetic-secret"),
                    ),
                    redirect_stderr(io.StringIO()) as stderr,
                ):
                    self.assertEqual(module.cli(argv), expected)
                self.assertIn("storage", stderr.getvalue().lower())
                self.assertNotIn("synthetic-secret", stderr.getvalue())

    def test_manager_never_exposes_unexpected_destination_error(self):
        module = self.module()
        manager = module.EmbeddedManager(
            self.connector_config(), Path("/unused"), Path("/unused"), "codex", "--chat-documents"
        )
        with patch.object(
            module, "require_server", side_effect=OSError("/private/synthetic-secret")
        ):
            manager.start()
        self.assertIsNone(manager.root)
        self.assertIn("Settings", manager.status)
        self.assertNotIn("synthetic-secret", manager.status)

    def test_no_settings_or_old_local_choice_requires_server_without_overwriting(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            for saved in (None, "local"):
                if saved:
                    save_destination("claude-desktop", saved, home=home)
                before = read_destination("claude-desktop", home=home)
                with self.assertRaisesRegex(ValueError, "Settings.*server URL"):
                    module.require_server("claude-desktop", home=home)
                self.assertEqual(read_destination("claude-desktop", home=home), before)
            settings = save_destination(
                "claude-desktop", "server", base_url="http://localhost:7777", home=home
            )
            self.assertEqual(module.require_server("claude-desktop", home=home), settings)

    def test_integrity_and_settings_failures_have_distinct_private_statuses(self):
        from runtime.verify import ReleaseIntegrityError

        module = self.module()
        with (
            patch.object(module, "main", side_effect=ReleaseIntegrityError("synthetic-secret")),
            redirect_stderr(io.StringIO()) as stderr,
        ):
            self.assertEqual(module.cli(["--internal-startup-status"]), 73)
        self.assertIn("verify", stderr.getvalue())
        self.assertNotIn("synthetic-secret", stderr.getvalue())
        with (
            patch.object(
                module,
                "main",
                side_effect=lambda _: module.launch(SimpleNamespace(client="codex"), {}),
            ),
            patch.object(module, "require_server", side_effect=ValueError("synthetic-secret")),
            redirect_stderr(io.StringIO()) as stderr,
        ):
            self.assertEqual(module.cli(["--internal-startup-status"]), 71)
        self.assertIn("Settings", stderr.getvalue())
        self.assertNotIn("synthetic-secret", stderr.getvalue())

    def test_launch_retains_advanced_limits_without_rewriting_destination(self):
        module = self.module()
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("pathlib.Path.home", return_value=Path(temporary).resolve()),
        ):
            from runtime.app_settings import save_limits

            saved = save_destination("claude-desktop", "server", base_url="http://localhost:7777")
            save_limits("claude-desktop", 8192, 512 * 1024 * 1024)
            args = SimpleNamespace(client="claude-desktop", document_response_bytes=None)
            with (
                patch.object(module, "storage_session", return_value=nullcontext(Path(temporary))),
                patch("runtime.server_profile.launch", return_value=0) as launch,
            ):
                self.assertEqual(module.launch(args, {}), 0)
                self.assertEqual(args.document_response_bytes, 8192)
                self.assertEqual(
                    launch.call_args.args[2].destination.response_bytes, 512 * 1024 * 1024
                )
                self.assertEqual(read_destination("claude-desktop"), saved)

    def test_manager_exposes_setup_error_and_settings_remains_available(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            for mode in ("--chat-documents", "--settings-tools"):
                manager = module.EmbeddedManager(
                    self.connector_config(), home, home / "runtime", "codex", mode
                )
                from runtime.build_server import VERSION

                self.assertEqual(manager.server_info["version"], VERSION)
                manager.start()
                if mode == "--chat-documents":
                    self.assertIsNone(manager.root)
                    self.assertIn("server URL", manager.status)
                    save_destination(
                        "codex", "server", base_url="https://server.invalid", home=home
                    )
                    manager.start()
                self.assertEqual(manager.root, home / "runtime")

    def test_current_connector_refuses_missing_or_invalid_packaged_instructions(self):
        module = self.module()
        invalid = [None, [], {}, {"--chat-documents": "Require consent."}]
        invalid += [
            {"--chat-documents": text, "--settings-tools": None}
            for text in (None, "", " \n", [], 1)
        ]
        invalid += [{"--chat-documents": "Require consent.", "--settings-tools": []}]
        for instructions in invalid:
            config = self.connector_config()
            if instructions is None:
                config.pop("instructions")
            else:
                config["instructions"] = instructions
            with (
                self.subTest(instructions=instructions),
                self.assertRaisesRegex(ValueError, "instructions"),
            ):
                module.EmbeddedManager(
                    config, Path("/unused"), Path("/unused"), "codex", "--settings-tools"
                )

    def test_advanced_download_limit_does_not_invalidate_selection_approval(self):
        from dataclasses import replace

        from runtime.server_selection import check_current

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            saved = save_destination(
                "codex", "server", base_url="https://server.invalid", home=home
            )
            effective = replace(
                saved, destination=replace(saved.destination, response_bytes=512 * 1024 * 1024)
            )
            store = SimpleNamespace(client="codex", home=home)
            check_current(store, effective)
            save_destination("codex", "server", base_url="https://other.invalid", home=home)
            with self.assertRaises(ValueError):
                check_current(store, effective)

    def test_native_dispatch_rejects_local_flags_and_keeps_settings_independent(self):
        import contextlib
        import io
        import json
        from unittest.mock import AsyncMock

        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "catalogs.json").write_text(json.dumps(self.connector_config()))
            with (
                patch.object(module.sys, "frozen", True, create=True),
                patch.object(module.sys, "platform", "darwin"),
                patch.object(module.platform, "machine", return_value="arm64"),
                patch.object(module.sys, "executable", str(root / "openreading-worker")),
                patch.object(
                    module,
                    "verify_release",
                    return_value={
                        "profile": "core-server-client-v1",
                        "release_version": "0.2.0-alpha.19",
                        "core_commit": "a" * 40,
                        "worker_sha256": "b" * 64,
                    },
                ) as verify,
            ):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(module.main(["--version"]), 0)
                self.assertEqual(json.loads(output.getvalue())["release_version"], "0.2.0-alpha.19")
                with patch("runtime.server_profile.job_main", return_value=0) as job:
                    self.assertEqual(module.main(["--internal-server-job", "id"]), 0)
                    self.assertEqual(job.call_args.args[0], ["id"])
                with patch("runtime.destination_ui.run", return_value=0) as ui:
                    self.assertEqual(
                        module.main(["--client", "codex", "--destination-settings"]), 0
                    )
                    ui.assert_called_once_with("codex")
                with patch("runtime.settings_server.serve", new_callable=AsyncMock) as settings:
                    self.assertEqual(module.main(["--client", "codex", "--settings-tools"]), 0)
                    settings.assert_awaited_once_with("codex")
                with patch.object(module, "launch", return_value=0) as launch:
                    self.assertEqual(module.main(["--client", "codex", "--chat-documents"]), 0)
                    self.assertEqual(launch.call_args.args[0].client, "codex")
                for flag in ("--settings-tools", "--chat-documents"):
                    with patch("runtime.connector_proxy.serve") as serve:
                        self.assertEqual(module.main(["--client", "codex", "--connector", flag]), 0)
                        self.assertEqual(serve.call_args.args[1], flag)
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    module.main(["--client", "codex", "--input-root", "/tmp"])
                verify.return_value = {"profile": "local-document-proof-v2"}
                with self.assertRaisesRegex(ValueError, "server-only"):
                    module.main(["--version"])
            with self.assertRaisesRegex(ValueError, "packaged"):
                module.main(["--version"])
