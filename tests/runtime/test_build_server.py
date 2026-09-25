"""Server packages contain a complete connector and no provisioned parsing engine."""

import importlib
import importlib.util
import json
import pyexpat
import shlex
import ssl
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime.verify import ReleaseIntegrityError, inventory, verify_release


def captured_catalog(worker, mode, *, server=False, include_instructions=False):
    """Represent metadata from the two frozen MCP servers without executing a binary."""
    tools = {"tools": []}
    if not include_instructions:
        return tools
    return {
        "catalog": tools,
        "instructions": "Require destination consent." if mode == "--chat-documents" else None,
    }


class ServerBuildTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime.build_server"))
        return importlib.import_module("runtime.build_server")

    def test_audit_covers_the_lock_used_to_freeze_the_connector(self):
        module = self.module()
        repository = Path(module.__file__).resolve().parent.parent
        commands = subprocess.run(
            ["make", "-n", "audit"], cwd=repository, check=True, capture_output=True, text=True
        ).stdout.splitlines()
        audited = set()
        for command in commands:
            parts = shlex.split(command)
            if parts[:2] == ["uv", "audit"] and "--project" in parts:
                audited.add(
                    (repository / parts[parts.index("--project") + 1] / "uv.lock").resolve()
                )
        self.assertIn(module.LOCK.resolve(), audited)

    def test_notices_follow_frozen_code_and_include_native_and_bootloader_licenses(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frozen = root / "runtime"
            (frozen / "_internal/actual").mkdir(parents=True)
            (frozen / "_internal/actual/__init__.pyc").write_bytes(b"compiled")
            (frozen / "_internal/_ssl.cpython-311-fixture.so").write_bytes(b"native fixture")
            (frozen / "_internal/unused-1.dist-info").mkdir()
            (frozen / "_internal/unused-1.dist-info/METADATA").write_text("metadata only")
            prefix = root / "python"
            (prefix / "licenses").mkdir(parents=True)
            (prefix / "licenses/LICENSE.cpython.txt").write_text("native Python license")
            (prefix / "licenses/LICENSE.ssl.txt").write_text("native SSL license")
            (prefix / "PYTHON.json").write_text(
                json.dumps(
                    {
                        "python_version": "3.11.16",
                        "license_path": "licenses/LICENSE.cpython.txt",
                        "build_info": {
                            "extensions": {
                                "_ssl": [{"license_paths": ["licenses/LICENSE.ssl.txt"]}]
                            }
                        },
                    }
                )
            )
            distributions = []
            for name, code in (
                ("Actual", "actual/__init__.py"),
                ("Unused", "unused/__init__.py"),
                ("PyInstaller", "PyInstaller/bootloader/run"),
            ):
                base = root / name
                license_path = Path(name + "-1.dist-info/licenses/LICENSE")
                (base / license_path).parent.mkdir(parents=True)
                (base / license_path).write_text(name + " license text")
                distributions.append(
                    SimpleNamespace(
                        metadata={"Name": name, "License": "MIT"},
                        version="1",
                        files=[Path(code), license_path],
                        locate_file=lambda path, base=base: base / path,
                    )
                )
            with (
                patch.object(module.metadata, "distributions", return_value=distributions),
                patch.object(module.sys, "base_prefix", str(prefix)),
                patch.object(module.platform, "python_version", return_value="3.11.16"),
            ):
                text = module.notices(frozen)
            for included in (
                "Actual license text",
                "PyInstaller license text",
                "native Python license",
                "native SSL license",
            ):
                self.assertIn(included, text)
            self.assertNotIn("Unused license text", text)
            (prefix / "licenses/LICENSE.ssl.txt").unlink()
            with (
                patch.object(module.metadata, "distributions", return_value=[]),
                patch.object(module.sys, "base_prefix", str(prefix)),
                patch.object(module.platform, "python_version", return_value="3.11.16"),
                self.assertRaises(ValueError),
            ):
                module.notices(frozen)

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
                patch.object(module.platform, "python_version", return_value="3.11.16"),
                patch.object(ssl, "OPENSSL_VERSION_INFO", (3, 5, 0, 8, 0)),
                patch.object(pyexpat, "version_info", (2, 8, 5)),
                patch.object(module.platform, "mac_ver", return_value=("15.1", "", "")),
            ):
                runtime = module.build_runtime(root / "runtime")
                self.assertEqual(verify_release(runtime)["profile"], "core-server-client-v1")
                with self.assertRaises(ValueError):
                    module.build_runtime(runtime)
            with patch.object(module, "catalog", side_effect=captured_catalog):
                archive = module.package(runtime, root / "package")
            with zipfile.ZipFile(archive) as zipped:
                names = zipped.namelist()
                self.assertNotIn("bootstrap.json", names)
                self.assertIn("runtime/openreading-worker", names)
                manifest = json.loads(zipped.read(".claude-plugin/plugin.json"))
                self.assertEqual(manifest["name"], "openreading")
                self.assertEqual(manifest["version"], module.VERSION)
                self.assertIn(b"--connector", zipped.read("launch.sh"))
            release = verify_release(root / "package/plugin/runtime")
            self.assertIn("catalogs.json", release["files"])
            self.assertIn("resources/toolchain.json", release["files"])
            metadata = json.loads((root / "package/plugin/runtime/catalogs.json").read_text())
            self.assertEqual(
                metadata.get("instructions"),
                {
                    "--chat-documents": "Require destination consent.",
                    "--settings-tools": None,
                },
            )
            self.assertEqual(metadata["catalogs"]["--chat-documents"], {"tools": []})
            forbidden = runtime / "resources/model.onnx"
            forbidden.write_bytes(b"unexpected model")
            data = json.loads((runtime / "release.json").read_bytes())
            data["files"] = inventory(runtime)
            (runtime / "release.json").write_text(json.dumps(data))
            with self.assertRaises(ReleaseIntegrityError):
                verify_release(runtime)

    def test_server_inventory_rejects_engine_modules_metadata_and_unrelated_schemas(self):
        module = self.module()
        forbidden = (
            "openreading/adapters/registry.pyc",
            "openreading/server/__init__.pyc",
            "openreading/router/router.py",
            "openreading/api.pyc",
            "openreading/artifacts/worker.pyc",
            "openreading/artifacts/service.pyc",
            "openreading/schemas/adapter-descriptor.v0.8.json",
            "openreading/schemas/strategy-config.v0.4.json",
            "openreading/types/descriptor.pyc",
            "openreading/adapters/README.md",
            "openreading-0.3.0.dist-info/METADATA",
            "pypdf/__init__.pyc",
            "pypdf-6.15.0.dist-info/METADATA",
            "puremagic/__init__.pyc",
            "yaml/__init__.pyc",
            "runtime/docling_profile.pyc",
        )
        for name in forbidden:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "resources").mkdir()
                (root / "resources/server-client.uv.lock").write_text("fixture lock")
                (root / "openreading-worker").write_bytes(b"fixture worker")
                (root / "THIRD_PARTY_NOTICES.txt").write_text("fixture licenses")
                bad = root / "_internal" / name
                bad.parent.mkdir(parents=True, exist_ok=True)
                bad.write_bytes(b"engine content")
                files = inventory(root)
                release = {
                    "format_version": "3",
                    "release_version": module.VERSION,
                    "os": "darwin",
                    "arch": "arm64",
                    "minimum_os_version": "15.1",
                    "core_commit": "a" * 40,
                    "core_version": "0.3.0",
                    "python_version": "3.11.15",
                    "files": files,
                    "licenses": ["THIRD_PARTY_NOTICES.txt"],
                    "dependency_lock_sha256": files["resources/server-client.uv.lock"]["sha256"],
                    "worker_sha256": files["openreading-worker"]["sha256"],
                    "profile": "core-server-client-v1",
                    "distribution": "development-only",
                }
                (root / "release.json").write_text(json.dumps(release))
                with self.assertRaises(ReleaseIntegrityError):
                    verify_release(root)

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
                    patch.object(module, "catalog", side_effect=captured_catalog),
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
                patch.object(module, "catalog", side_effect=captured_catalog),
            ):
                module.package(runtime, root / "package", client="claude-code")
            plugin = root / "package/plugin"
            with zipfile.ZipFile(
                root / "package/OpenReading-Claude-Code-Local-Marketplace.zip"
            ) as local:
                self.assertIn(".claude-plugin/marketplace.json", local.namelist())
                self.assertIn("plugin/.claude-plugin/plugin.json", local.namelist())
                self.assertIn("plugin/.mcp.json", local.namelist())
                self.assertIn("plugin/runtime/openreading-worker", local.namelist())
            marketplace = json.loads((root / "package/.claude-plugin/marketplace.json").read_text())
            entry = marketplace["plugins"][0]
            self.assertEqual((root / "package" / entry["source"]).resolve(), plugin.resolve())
            manifest = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
            self.assertEqual(entry["name"], manifest["name"])
            self.assertNotIn("userConfig", manifest)
            self.assertEqual(manifest["name"], "openreading")
            self.assertEqual(
                {path.name for path in (plugin / "skills").iterdir()},
                {"openreading", "openreading-settings"},
            )
            for name in ("openreading", "openreading-settings"):
                self.assertIn(
                    f"name: {name}\n", (plugin / "skills" / name / "SKILL.md").read_text()
                )

            self.assertEqual(marketplace["name"], "openreading")
            configs = json.loads((plugin / ".mcp.json").read_text())["mcpServers"]
            published = json.loads(
                (
                    Path(module.__file__).resolve().parent.parent
                    / ".claude-plugin/marketplace.json"
                ).read_text()
            )["plugins"][0]
            self.assertEqual(published["source"]["source"], "git-subdir")
            self.assertEqual(published["source"]["path"], "plugins/claude-code/openreading")
            self.assertNotIn("headersHelper", published)
            self.assertNotIn("strict", published)

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

    def test_package_refuses_missing_or_blank_document_instructions(self):
        module = self.module()
        for instructions in (None, "", " \n", []):
            with (
                self.subTest(instructions=instructions),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                runtime = root / "runtime"
                runtime.mkdir()
                with (
                    patch.object(
                        module,
                        "verify_release",
                        return_value={
                            "profile": "core-server-client-v1",
                            "release_version": module.VERSION,
                        },
                    ),
                    patch.object(
                        module,
                        "catalog",
                        return_value={
                            "catalog": {"tools": []},
                            "instructions": instructions,
                        },
                    ),
                    self.assertRaisesRegex(ValueError, "instructions"),
                ):
                    module.package(runtime, root / "package")
                self.assertFalse((root / "package").exists())

    def test_platform_and_lock_refuse_unreviewed_environment(self):
        module = self.module()
        with patch.object(module.sys, "platform", "linux"), self.assertRaises(ValueError):
            module.build_runtime(Path("/unused"))
        with patch.object(module.metadata, "distribution") as distribution:
            distribution.return_value.read_text.return_value = '{"vcs_info":{"commit_id":"wrong"}}'
            with self.assertRaises(ValueError):
                module.identity()

    def test_freezer_refuses_older_python_or_openssl_before_starting_build(self):
        module = self.module()
        for python, openssl in (("3.11.15", (3, 5, 0, 8, 0)), ("3.11.16", (3, 5, 0, 7, 0))):
            with (
                self.subTest(python=python, openssl=openssl),
                patch.object(module.sys, "platform", "darwin"),
                patch.object(module.platform, "machine", return_value="arm64"),
                patch.object(module.platform, "python_version", return_value=python),
                patch.object(ssl, "OPENSSL_VERSION_INFO", openssl),
                patch.object(
                    module,
                    "identity",
                    side_effect=AssertionError("unreviewed toolchain reached build"),
                ),
                self.assertRaises(ValueError),
            ):
                module.build_runtime(Path("/unused"))

    def test_freezer_refuses_unpatched_expat_before_starting_build(self):
        module = self.module()
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(module.sys, "platform", "darwin"),
            patch.object(module.platform, "machine", return_value="arm64"),
            patch.object(module.platform, "python_version", return_value="3.11.16"),
            patch.object(ssl, "OPENSSL_VERSION_INFO", (3, 5, 0, 8, 0)),
            patch.object(pyexpat, "version_info", (2, 8, 4)),
            patch.object(module, "identity", side_effect=AssertionError("unsafe build started")),
            self.assertRaisesRegex(ValueError, "Expat"),
        ):
            module.build_runtime(Path(temporary) / "runtime")

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
            from runtime.client_boundary import CLIENT_SUMMARY

            client_metadata = (
                f"Summary: {CLIENT_SUMMARY}\n"
                "Requires-Dist: jsonschema>=4.21\nRequires-Dist: mcp>=1.30\n"
                "Requires-Dist: psutil>=7.2\nRequires-Dist: pydantic>=2.7\n"
            )
            distribution.return_value.read_text.side_effect = lambda name: (
                client_metadata
                if name == "METADATA"
                else json.dumps({"vcs_info": {"commit_id": commit}})
            )
            self.assertEqual(module.identity()["core_commit"], commit)
