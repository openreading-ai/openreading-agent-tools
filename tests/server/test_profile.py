"""The trusted launcher fixes destination, storage roots and child execution."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from runtime.destination_settings import save_destination


class ServerProfileTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.server_profile"), "Missing trusted server launch"
        )
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.enterContext(patch("pathlib.Path.home", return_value=self.home))
        self.settings = save_destination("chatgpt", "server", base_url="http://localhost:8787")
        self.metadata = {
            "core_commit": "a" * 40,
            "core_version": "0.3.0",
            "worker_sha256": "b" * 64,
        }

    def test_launcher_configures_fixed_service_and_original_destination_snapshot(self):
        from runtime.server_profile import launch

        args = SimpleNamespace(client="chatgpt", document_response_bytes=1000000)
        with patch("openreading.mcp_server.session.serve", AsyncMock()) as serve:
            self.assertEqual(launch(args, self.metadata, self.settings), 0)
        config = serve.call_args.args[0]
        options = serve.call_args.kwargs
        self.assertIsNone(config.docling)
        self.assertIsNone(config.limits.deadline_seconds)
        self.assertIsNone(config.limits.store_bytes)
        self.assertEqual(config.limits.source_bytes, 100 * 1024**2)
        self.assertEqual(options["document_export_root"], self.home / "Downloads/OpenReading")
        execution = options["execution"]
        self.assertEqual(execution.command[-1], "--internal-server-job")
        self.assertEqual(
            execution.snapshot, {"client": "chatgpt", "destination": self.settings.wire()}
        )
        service = options["service_factory"](config)
        self.addCleanup(service.close)
        self.assertEqual(service.identity.backend_id, "external-response")
        self.assertEqual(service.identity.core_commit, "a" * 40)
        self.assertEqual(service.identity.extraction_settings["retaining_worker_sha256"], "b" * 64)

    def test_child_factory_rejects_changed_roots_limits_and_unknown_execution_fields(self):
        from dataclasses import asdict

        from runtime.server_profile import config_for, job_main

        config, selection = config_for("chatgpt", self.settings)
        request = {
            "execution": {"client": "chatgpt", "destination": self.settings.wire()},
            "input_root": str(config.input_root),
            "artifact_root": str(config.artifact_root),
            "limits": asdict(config.limits),
            "docling": None,
        }

        def run(argv, *, service_factory):
            self.assertEqual(argv, ["/private/job"])
            service = service_factory(request)
            self.addCleanup(service.close)
            for key, value in (
                ("input_root", "/different"),
                ("artifact_root", "/different"),
                ("limits", {}),
                ("docling", {}),
                ("execution", {**request["execution"], "module": "injected"}),
            ):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    service_factory({**request, key: value})
            return 0

        with patch("openreading.artifacts.jobs.main", side_effect=run):
            self.assertEqual(job_main(["/private/job"], self.metadata), 0)

    def test_current_runtime_and_integration_pins_match_installed_core(self):
        import importlib.metadata
        import json
        import re
        import tomllib

        repository = Path(__file__).resolve().parents[2]
        expected = None
        for name in ("server_client", "testing"):
            project = tomllib.loads((repository / "runtime" / name / "pyproject.toml").read_text())
            dependency = next(
                value
                for value in project["project"]["dependencies"]
                if value.startswith("openreading")
            )
            commit = re.search(r"@([a-f0-9]{40})(?:#.*)?$", dependency).group(1)
            if expected is None:
                expected = commit
            self.assertEqual(commit, expected)
        installed = json.loads(
            importlib.metadata.distribution("openreading").read_text("direct_url.json")
        )
        self.assertEqual(installed["vcs_info"]["commit_id"], expected)

    def test_native_data_root_is_snapshotted_and_mismatched_children_are_refused(self):
        from dataclasses import asdict

        from runtime.destination_settings import DestinationSettings
        from runtime.server_profile import config_for, job_main, launch
        from runtime.storage_settings import storage_session

        with self.assertRaises(ValueError):
            config_for("chatgpt", DestinationSettings())
        with storage_session("chatgpt") as root:
            args = SimpleNamespace(
                client="chatgpt", document_response_bytes=8192, runtime_data_root=root
            )
            with patch("openreading.mcp_server.session.serve", AsyncMock()) as serve:
                launch(args, self.metadata, self.settings)
            config = serve.call_args.args[0]
            options = serve.call_args.kwargs
            self.assertEqual(options["document_export_root"], root / "exports")
            self.assertEqual(options["document_response_bytes"], 8192)
            request = {
                "execution": options["execution"].snapshot,
                "input_root": str(config.input_root),
                "artifact_root": str(config.artifact_root),
                "limits": asdict(config.limits),
                "docling": None,
            }

            def run(argv, *, service_factory):
                service = service_factory(request)
                service.close()
                bad = {
                    **request,
                    "execution": {**request["execution"], "storage_root": "/elsewhere"},
                }
                with self.assertRaisesRegex(ValueError, "data location"):
                    service_factory(bad)
                return 0

            with patch("openreading.artifacts.jobs.main", side_effect=run):
                self.assertEqual(job_main(["synthetic"], self.metadata), 0)

    def test_launcher_returns_interrupt_exit_code(self):
        from runtime.server_profile import launch

        args = SimpleNamespace(client="chatgpt", document_response_bytes=1_000_000)
        with patch(
            "openreading.mcp_server.session.serve", AsyncMock(side_effect=KeyboardInterrupt)
        ):
            self.assertEqual(launch(args, self.metadata, self.settings), 130)

    def test_launcher_reports_unsafe_configuration_without_traceback(self):
        import contextlib
        import io

        from runtime.server_profile import config_for, launch

        _, selection = config_for("chatgpt", self.settings)
        saved = selection.approvals.with_name("original-approvals")
        selection.approvals.rename(saved)
        selection.approvals.symlink_to(saved, target_is_directory=True)
        args = SimpleNamespace(client="chatgpt", document_response_bytes=1_000_000)
        stderr = io.StringIO()
        with (
            contextlib.redirect_stderr(stderr),
            patch("openreading.mcp_server.session.serve", AsyncMock()) as serve,
        ):
            self.assertEqual(launch(args, self.metadata, self.settings), 2)
        serve.assert_not_called()
        self.assertTrue(stderr.getvalue().strip())
        self.assertNotIn("Traceback", stderr.getvalue())
