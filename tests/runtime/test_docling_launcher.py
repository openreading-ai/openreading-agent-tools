"""The selected release, not ambient settings, chooses the local Docling launch."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.entrypoint import main
from runtime.verify import ReleaseIntegrityError, inventory, sha256, verify_release


class DoclingLaunchTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        for name in [
            "openreading-worker",
            "THIRD_PARTY_NOTICES.txt",
            "resources/docling-runtime.uv.lock",
            "resources/models/docling-project--docling-layout-heron-onnx/model.onnx",
            "resources/tessdata/eng.traineddata",
            "resources/tessdata/osd.traineddata",
            "resources/tessdata/configs/tsv",
            "resources/tesseract/bin/tesseract",
        ]:
            path = self.bundle / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic asset")
        (self.bundle / "resources/tesseract/bin/tesseract").chmod(0o755)
        self.metadata = {
            "format_version": "2",
            "release_version": "0.2.0-p0",
            "os": "darwin",
            "arch": "arm64",
            "minimum_os_version": "15.1",
            "core_commit": "a" * 40,
            "core_version": "0.3.0",
            "python_version": "3.11.15",
            "dependency_lock_sha256": sha256(self.bundle / "resources/docling-runtime.uv.lock"),
            "profile": "local-document-proof-v2",
            "distribution": "development-only",
            "licenses": ["THIRD_PARTY_NOTICES.txt"],
        }
        self.write_release()
        self.enterContext(patch("runtime.entrypoint.sys.platform", "darwin"))
        self.enterContext(patch("platform.machine", return_value="arm64"))
        self.enterContext(patch("runtime.entrypoint.sys.frozen", True, create=True))
        self.enterContext(
            patch("runtime.entrypoint.sys.executable", str(self.bundle / "openreading-worker"))
        )
        self.enterContext(patch("pathlib.Path.home", return_value=self.home))
        self.grant = self.root / "documents"
        self.grant.mkdir()

    def write_release(self):
        self.metadata["files"] = inventory(self.bundle)
        self.metadata["worker_sha256"] = self.metadata["files"]["openreading-worker"]["sha256"]
        (self.bundle / "release.json").write_text(json.dumps(self.metadata))

    def test_docling_release_launches_private_unique_profile_and_removes_it_on_exit(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(
                main(
                    [
                        "--client",
                        "chatgpt",
                        "--configure",
                        "--input-root",
                        str(self.grant),
                        "--ocr",
                        "true",
                    ]
                ),
                0,
            )
        paths = []

        def serve(args):
            self.assertEqual(args[:2], ["--profile", "local-document-proof-v2"])
            path = Path(args[args.index("--profile-config") + 1])
            self.assertTrue(path.is_absolute())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            value = json.loads(path.read_bytes())
            for key in (
                "pages",
                "source_bytes",
                "extraction_bytes",
                "store_bytes",
                "deadline_seconds",
            ):
                self.assertIsNone(value[key])
            self.assertEqual(value["worker_memory_bytes"], 4 * 1024**3)
            self.assertTrue(value["docling"]["ocr"])
            self.assertEqual(
                value["docling"]["tesseract_cmd"],
                str(self.bundle / "resources/tesseract/bin/tesseract"),
            )
            self.assertEqual(
                value["docling"]["dependency_lock"],
                str(self.bundle / "resources/docling-runtime.uv.lock"),
            )
            self.assertEqual(
                Path(args[args.index("--artifact-root") + 1]).parts[-2:], ("v2", "artifacts")
            )
            paths.append(path)
            return 0

        with patch("openreading.mcp_server.main.main", side_effect=serve):
            self.assertEqual(main(["--client", "chatgpt"]), 0)
            self.assertEqual(main(["--client", "chatgpt"]), 0)
        self.assertNotEqual(paths[0], paths[1])
        self.assertTrue(all(not p.parent.exists() for p in paths))

    def test_profile_cleanup_survives_core_failure_and_invalid_setup_never_launches(self):
        self.assertEqual(verify_release(self.bundle)["format_version"], "2")
        captured = []

        def fail(args):
            captured.append(Path(args[args.index("--profile-config") + 1]))
            raise RuntimeError("synthetic core failure")

        with patch("openreading.mcp_server.main.main", side_effect=fail):
            with self.assertRaises(RuntimeError):
                main(["--client", "codex", "--input-root", str(self.grant)])
        self.assertFalse(captured[0].parent.exists())
        with (
            patch("openreading.mcp_server.main.main") as launch,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            for args in [
                ["--client", "codex"],
                ["--client", "codex", "--ocr", "off"],
                ["--client", "codex", "--configure"],
                ["--client", "codex", "--input-root", "relative"],
                ["--client", "codex", "--input-root", str(self.grant), "--ocr", "1"],
            ]:
                self.assertEqual(main(args), 2)
            launch.assert_not_called()

    def test_inventory_profile_and_lock_are_consistent_before_dispatch(self):
        self.assertEqual(verify_release(self.bundle)["profile"], "local-document-proof-v2")
        original = self.metadata.copy()
        for key, value in [
            ("profile", "hosted"),
            ("distribution", "signed"),
            ("dependency_lock_sha256", "0" * 64),
        ]:
            self.metadata = {**original, key: value}
            self.write_release()
            with self.assertRaises(ReleaseIntegrityError):
                verify_release(self.bundle)
        self.metadata = original
        missing = self.bundle / "resources/tessdata/configs/tsv"
        missing.unlink()
        self.write_release()
        with self.assertRaises(ReleaseIntegrityError):
            verify_release(self.bundle)

    def test_store_handles_close_before_handoff_and_environment_restores_on_refusal(self):
        from openreading.artifacts.store import Store

        closed = []

        def store(config):
            value = Store(config)
            value.close = lambda: closed.append(config.artifact_root)
            return value

        with (
            patch("openreading.artifacts.store.Store", side_effect=store),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(
                main(["--client", "codex", "--configure", "--input-root", str(self.grant)]), 0
            )
            with patch("openreading.mcp_server.main.main", return_value=0):
                self.assertEqual(main(["--client", "codex"]), 0)
        self.assertEqual(len(closed), 2)
        import os

        output = io.StringIO()
        with (
            patch.dict(os.environ, {"HF_HUB_OFFLINE": "original", "TRANSFORMERS_OFFLINE": "other"}),
            patch("openreading.artifacts.store.Store", side_effect=OSError("private path")),
            contextlib.redirect_stderr(output),
        ):
            self.assertEqual(main(["--client", "codex", "--input-root", str(self.grant)]), 2)
            self.assertEqual(os.environ["HF_HUB_OFFLINE"], "original")
            self.assertEqual(os.environ["TRANSFORMERS_OFFLINE"], "other")
        self.assertIn("configuration_required", output.getvalue())
        self.assertNotIn("private path", output.getvalue())

    def test_diagnostic_bundle_cannot_enter_historical_client_packages(self):
        from runtime.package import package_clients

        output = self.root / "client-packages"
        with self.assertRaisesRegex(ValueError, "Docling"):
            package_clients(self.bundle, output)
        self.assertFalse(output.exists())

    def test_parallel_profile_lifetimes_are_independent(self):
        from runtime.configuration import Settings
        from runtime.docling_profile import profile_file

        settings = Settings(self.grant, False)
        with profile_file("codex", settings, self.bundle) as (first, _):
            first_content = first.read_bytes()
            with profile_file("codex", settings, self.bundle) as (second, _):
                self.assertNotEqual(first, second)
                self.assertEqual(first.read_bytes(), first_content)
                self.assertTrue(second.exists())
            self.assertTrue(first.exists())
            self.assertFalse(second.parent.exists())
        self.assertFalse(first.parent.exists())

    def test_chat_launcher_forwards_provider_through_real_profile_launch(self):
        from runtime.chat_selection import LocalSelectionProvider

        def core_boundary(args, *, selection_provider=None):
            self.assertIsInstance(selection_provider, LocalSelectionProvider)
            self.assertEqual(
                Path(args[args.index("--input-root") + 1]), selection_provider.store.grant
            )
            profile = json.loads(Path(args[args.index("--profile-config") + 1]).read_text())
            self.assertTrue(profile["docling"]["ocr"])
            return 0

        with patch("openreading.mcp_server.main.main", side_effect=core_boundary):
            self.assertEqual(main(["--client", "claude-desktop", "--chat-documents"]), 0)

    def test_frozen_worker_suppresses_ort_before_internal_core_dispatch(self):
        import builtins
        import os

        original_import = builtins.__import__
        observed = []

        def importing(name, *args, **kwargs):
            if name == "openreading.artifacts.worker":
                observed.append(name)
                self.assertEqual(os.environ.get("ORT_DISABLE_TELEMETRY"), "1")
            return original_import(name, *args, **kwargs)

        def worker(args):
            self.assertEqual(os.environ.get("ORT_DISABLE_TELEMETRY"), "1")
            return 0

        with (
            patch.dict(os.environ, {"ORT_DISABLE_TELEMETRY": "0"}),
            patch("openreading.artifacts.worker.main", side_effect=worker),
            patch("builtins.__import__", side_effect=importing),
        ):
            self.assertEqual(main(["--internal-artifact-worker"]), 0)
        self.assertEqual(observed, ["openreading.artifacts.worker"])
