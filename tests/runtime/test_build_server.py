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
            # zipimport bytecode contains ZIP magic constants but is not an archive.
            (destination / "zipimport.pyc").write_bytes(
                b"bytecode constants PK\x05\x06\xe9\xff\xff\x00\x00c" + bytes(24)
            )

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
                self.assertEqual(manifest["version"], "0.2.0-alpha.17")
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

    def test_package_refuses_nested_zip_before_publishing_upload(self):
        module = self.module()
        for name in ("base_library.zip", "BASE_LIBRARY.ZIP", "renamed-library.bin"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                runtime = root / "runtime"
                (runtime / "_internal").mkdir(parents=True)
                (runtime / "openreading-worker").write_bytes(b"synthetic worker")
                with zipfile.ZipFile(runtime / "_internal" / name, "w") as nested:
                    nested.writestr("encodings/__init__.pyc", b"synthetic bytecode")
                with (
                    patch.object(
                        module,
                        "verify_release",
                        return_value={
                            "profile": "core-server-client-v1",
                            "release_version": module.VERSION,
                            "core_commit": "a" * 40,
                            "worker_sha256": "b" * 64,
                        },
                    ),
                    patch.object(module, "catalog", return_value={"tools": []}),
                    self.assertRaisesRegex(ValueError, "nested ZIP"),
                ):
                    module.package(runtime, root / "package")
                self.assertFalse((root / "package/OpenReading-Claude-Plugin.zip").exists())

    def test_claude_code_launcher_and_marketplace_use_isolated_client(self):
        import os
        import subprocess

        module = self.module()
        with tempfile.TemporaryDirectory(prefix="code package ") as temporary:
            root = Path(temporary).resolve()
            runtime = root / "runtime"
            runtime.mkdir()
            worker = runtime / "openreading-worker"
            worker.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            worker.chmod(0o755)
            release = {
                "profile": "core-server-client-v1",
                "release_version": module.VERSION,
                "core_commit": "a" * 40,
                "worker_sha256": "b" * 64,
            }
            with (
                patch.object(module, "verify_release", return_value=release),
                patch.object(module, "catalog", return_value={"tools": []}),
            ):
                module.package(runtime, root / "package", client="claude-code")
            plugin = root / "package/plugin"
            marketplace = json.loads((root / "package/.claude-plugin/marketplace.json").read_text())
            entry = marketplace["plugins"][0]
            self.assertEqual((root / "package" / entry["source"]).resolve(), plugin.resolve())
            manifest = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
            self.assertEqual(entry["name"], manifest["name"])
            self.assertNotIn("userConfig", manifest)
            self.assertEqual(marketplace["name"], "openreading-local")
            configs = json.loads((plugin / ".mcp.json").read_text())["mcpServers"]
            published = json.loads(
                (
                    Path(module.__file__).resolve().parent.parent
                    / ".claude-plugin/marketplace.json"
                ).read_text()
            )["plugins"][0]
            self.assertEqual(published["mcpServers"], configs)
            self.assertEqual(published["skills"], "./skills")
            self.assertFalse(published["strict"])

            self.assertEqual(set(configs), {"openreading", "openreading-settings"})
            for name, flag in (
                ("openreading", "--chat-documents"),
                ("openreading-settings", "--settings-tools"),
            ):
                config = configs[name]
                args = [arg.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin)) for arg in config["args"]]
                result = subprocess.run(
                    [config["command"], *args],
                    env={**os.environ, "HOME": str(root)},
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(
                    result.stdout.splitlines(), ["--client", "claude-code", "--connector", flag]
                )
            self.assertEqual(
                json.loads((root / "package/build.json").read_text())["client"], "claude-code"
            )
            # Authenticated archive sources require the marketplace to own all components.
            # Even an identity-only plugin.json conflicts in Claude Code 2.1.278.
            marketplace_archive = root / "package/OpenReading-Claude-Code-Marketplace.zip"
            with zipfile.ZipFile(marketplace_archive) as zipped:
                self.assertNotIn(".claude-plugin/plugin.json", zipped.namelist())
                self.assertNotIn(".mcp.json", zipped.namelist())
                self.assertEqual(zipped.read("runtime/openreading-worker"), worker.read_bytes())
                self.assertIn("skills/openreading-settings/SKILL.md", zipped.namelist())
            from runtime.verify import sha256

            self.assertEqual(
                json.loads((root / "package/build.json").read_text())["marketplace_sha256"],
                sha256(marketplace_archive),
            )
            self.assertIn("claude plugin", (plugin / "README.md").read_text())
            self.assertNotIn("Upload this plugin ZIP", (plugin / "README.md").read_text())
            self.assertEqual(
                worker.read_bytes(), (plugin / "runtime/openreading-worker").read_bytes()
            )

    def test_cli_packages_existing_runtime_for_code_without_rebuilding(self):
        import contextlib
        import io

        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with (
                patch.object(module, "build_runtime") as build,
                patch.object(module, "package", return_value=root / "plugin.zip") as package,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                module.main(
                    [
                        "--runtime",
                        str(root / "verified"),
                        "--client",
                        "claude-code",
                        "--output",
                        str(root / "new"),
                    ]
                )
            build.assert_not_called()
            package.assert_called_once_with(
                root / "verified", root / "new/package", client="claude-code"
            )
            with self.assertRaisesRegex(ValueError, "Unsupported client"):
                module.package(root, root / "invalid", client="other")

    def test_reused_runtime_version_must_match_plugin(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                patch.object(
                    module,
                    "verify_release",
                    return_value={
                        "profile": "core-server-client-v1",
                        "release_version": "0.2.0-alpha.16",
                    },
                ),
                patch.object(
                    module,
                    "catalog",
                    side_effect=AssertionError(
                        "Old runtime catalog was queried before checking its version"
                    ),
                ) as catalog,
                self.assertRaisesRegex(ValueError, "version"),
            ):
                module.package(root, root / "package", client="claude-code")
            catalog.assert_not_called()
            self.assertFalse((root / "package").exists())

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
                package.assert_called_once_with(
                    root / "runtime", root / "new/package", client="claude-desktop"
                )
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
