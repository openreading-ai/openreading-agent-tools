"""The server-only freezer preserves its pinned identity and required release profile."""

import importlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


class ServerBuildTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime.build_server"))
        return importlib.import_module("runtime.build_server")

    def test_freezer_outputs_a_verified_server_client_and_never_overwrites(self):
        module = self.module()
        from runtime.verify import verify_release

        def freeze(command, **kwargs):
            destination = Path(command[command.index("--distpath") + 1]) / "openreading-worker"
            destination.mkdir(parents=True)
            (destination / "openreading-worker").write_bytes(b"synthetic worker")
            (destination / "openreading-worker").chmod(0o755)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                patch.object(
                    module,
                    "selected_environment",
                    return_value={"core_commit": "a" * 40, "packages": {"openreading": "0.3.0"}},
                ),
                patch.object(module.platform, "machine", return_value="arm64"),
                patch.object(module.platform, "mac_ver", return_value=("15.1", "", "")),
                patch.object(module.platform, "python_version", return_value="3.11.15"),
                patch.object(module.sys, "platform", "darwin"),
                patch.object(module.subprocess, "run", side_effect=freeze),
                patch.object(module, "notices", return_value="fixture notices"),
            ):
                output = module.build_runtime(root / "output")
                release = verify_release(output)
                self.assertEqual(release["profile"], "server-client-v1")
                self.assertEqual(release["distribution"], "development-only")
                self.assertTrue((output / "resources/server-runtime.uv.lock").is_file())
                with self.assertRaises(ValueError):
                    module.build_runtime(output)
            with patch.object(module.sys, "platform", "linux"), self.assertRaises(ValueError):
                module.build_runtime(root / "other")

    def test_spec_excludes_local_parsers_and_keeps_runtime_sources(self):
        module = self.module()
        hooks = ModuleType("PyInstaller.utils.hooks")
        hooks.collect_data_files = lambda name: [("schema", "openreading")]
        hooks.copy_metadata = lambda name: []
        analyses = []

        def analyze(*args, **kwargs):
            analyses.append(kwargs)
            return SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])

        with patch.dict("sys.modules", {"PyInstaller.utils.hooks": hooks}):
            scope = {
                "Analysis": analyze,
                "PYZ": lambda *a: None,
                "EXE": lambda *a, **k: None,
                "COLLECT": lambda *a, **k: None,
            }
            exec(module.spec_text(), scope)
        self.assertIn("docling", analyses[0]["excludes"])
        self.assertIn("runtime.server_profile", analyses[0]["hiddenimports"])
        self.assertEqual(analyses[0]["module_collection_mode"]["openreading"], "pyz+py")

    def test_cli_resolves_its_output_path(self):
        import contextlib
        import io

        module = self.module()
        with (
            patch.object(module, "build_runtime", return_value=Path("/synthetic/output")) as build,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(module.main(["--output", "out"]), 0)
        self.assertTrue(build.call_args.args[0].is_absolute())
        self.assertEqual(output.getvalue().strip(), "/synthetic/output")
