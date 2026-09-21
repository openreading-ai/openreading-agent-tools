"""Server packages contain a complete connector and no provisioned parsing engine."""

import importlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from runtime.verify import ReleaseIntegrityError, inventory, verify_release


class ServerBuildTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime.build_server"))
        return importlib.import_module("runtime.build_server")

    def test_freeze_inventory_and_direct_plugin_preserve_identity_without_download(self):
        module = self.module()

        def freeze(command, **kwargs):
            destination = Path(command[command.index("--distpath") + 1]) / "openreading-worker"
            destination.mkdir(parents=True)
            (destination / "openreading-worker").write_bytes(b"synthetic executable")
            (destination / "openreading-worker").chmod(0o755)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with (
                patch.object(
                    module,
                    "identity",
                    return_value={"core_commit": "a" * 40, "core_version": "0.3.0"},
                ),
                patch.object(module.subprocess, "run", side_effect=freeze),
                patch.object(module, "notices", return_value="fixture notice"),
                patch.object(module.sys, "platform", "darwin"),
                patch.object(module.platform, "machine", return_value="arm64"),
                patch.object(module.platform, "python_version", return_value="3.11.15"),
                patch.object(module.platform, "mac_ver", return_value=("15.1", "", "")),
            ):
                runtime = module.build_runtime(root / "runtime")
                self.assertEqual(verify_release(runtime)["profile"], "core-server-client-v1")
                with self.assertRaises(ValueError):
                    module.build_runtime(runtime)
            with patch.object(module, "catalog", return_value={"tools": []}):
                archive = module.package(runtime, root / "package")
            with zipfile.ZipFile(archive) as zipped:
                names = zipped.namelist()
                self.assertNotIn("bootstrap.json", names)
                self.assertIn("runtime/openreading-worker", names)
                manifest = json.loads(zipped.read(".claude-plugin/plugin.json"))
                self.assertEqual(manifest["name"], "openreading-local-documents")
                self.assertEqual(manifest["version"], "0.2.0-alpha.14")
                self.assertIn(b"--connector", zipped.read("launch.sh"))
            release = verify_release(root / "package/plugin/runtime")
            self.assertIn("catalogs.json", release["files"])
            forbidden = runtime / "resources/model.onnx"
            forbidden.write_bytes(b"unexpected model")
            data = json.loads((runtime / "release.json").read_bytes())
            data["files"] = inventory(runtime)
            (runtime / "release.json").write_text(json.dumps(data))
            with self.assertRaises(ReleaseIntegrityError):
                verify_release(runtime)

    def test_platform_and_lock_refuse_unreviewed_environment(self):
        module = self.module()
        with patch.object(module.sys, "platform", "linux"), self.assertRaises(ValueError):
            module.build_runtime(Path("/unused"))
        with patch.object(module.metadata, "distribution") as distribution:
            distribution.return_value.read_text.return_value = '{"vcs_info":{"commit_id":"wrong"}}'
            with self.assertRaises(ValueError):
                module.identity()

    def test_cli_assembles_package_and_refuses_existing_destination(self):
        import contextlib
        import io

        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with self.assertRaises(ValueError):
                module.main(["--output", str(root)])
            with (
                patch.object(module, "build_runtime", return_value=root / "runtime") as build,
                patch.object(module, "package", return_value=root / "plugin.zip") as package,
                contextlib.redirect_stdout(io.StringIO()) as output,
            ):
                self.assertEqual(module.main(["--output", str(root / "new")]), 0)
                build.assert_called_once_with(root / "new/runtime")
                package.assert_called_once_with(root / "runtime", root / "new/package")
                self.assertIn("plugin.zip", output.getvalue())
            with (
                patch.object(
                    module, "verify_release", return_value={"profile": "local-document-proof-v2"}
                ),
                self.assertRaises(ValueError),
            ):
                module.package(root, root / "wrong")

    def test_identity_matches_pinned_core(self):
        import tomllib

        module = self.module()
        packages = tomllib.loads(module.LOCK.read_text())["package"]
        commit = next(row for row in packages if row["name"] == "openreading")["source"][
            "git"
        ].split("#")[-1]
        with (
            patch.object(module.metadata, "distribution") as distribution,
            patch.object(module.metadata, "version", return_value="0.3.0"),
        ):
            distribution.return_value.read_text.return_value = json.dumps(
                {"vcs_info": {"commit_id": commit}}
            )
            self.assertEqual(module.identity()["core_commit"], commit)
