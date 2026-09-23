"""Codex installs the server connector with its own state and portable launch paths."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from runtime import build_server


class CodexServerPackageTests(unittest.TestCase):
    def test_marketplace_relocates_both_connectors_without_changing_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            runtime = root / "runtime"
            runtime.mkdir()
            worker = runtime / "openreading-worker"
            worker.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            worker.chmod(0o755)
            release = {
                "profile": "core-server-client-v1",
                "release_version": build_server.VERSION,
                "core_commit": "a" * 40,
                "worker_sha256": "b" * 64,
            }
            with (
                patch.object(build_server, "verify_release", return_value=release),
                patch.object(build_server, "catalog", return_value={"tools": []}),
            ):
                try:
                    archive = build_server.package(runtime, root / "built", client="codex")
                except ValueError as error:
                    self.fail(f"Codex server-only packaging is unavailable: {error}")
            self.assertEqual(archive.name, "OpenReading-Codex-Plugin.zip")
            with zipfile.ZipFile(archive) as zipped:
                self.assertIn(".agents/plugins/marketplace.json", zipped.namelist())
                self.assertIn("plugins/openreading/.codex-plugin/plugin.json", zipped.namelist())
                self.assertFalse(any(".claude-plugin" in name for name in zipped.namelist()))
            moved = root / "installed café space"
            shutil.move(root / "built", moved)
            catalog = json.loads((moved / ".agents/plugins/marketplace.json").read_text())
            self.assertEqual(catalog["name"], "openreading")
            entry = catalog["plugins"][0]
            plugin = moved / entry["source"]["path"]
            self.assertEqual(entry["name"], "openreading")
            manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
            self.assertEqual(manifest["name"], "openreading")
            self.assertEqual(manifest["version"], build_server.VERSION)
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertNotIn("Docling", json.dumps(manifest))
            self.assertEqual(
                {p.name for p in (plugin / "skills").iterdir()},
                {"openreading", "openreading-settings"},
            )
            servers = json.loads((plugin / manifest["mcpServers"]).read_text())["mcpServers"]
            self.assertEqual(set(servers), {"openreading", "openreading-settings"})
            for name, flag in (
                ("openreading", "--chat-documents"),
                ("openreading-settings", "--settings-tools"),
            ):
                server = servers[name]
                # Codex resolves cwd relative to the installed plugin, not shell arguments.
                result = subprocess.run(
                    [server["command"], *server["args"]],
                    cwd=plugin / server["cwd"],
                    env={**os.environ, "HOME": str(root)},
                    text=True,
                    capture_output=True,
                    check=True,
                )
                self.assertEqual(
                    result.stdout.splitlines(),
                    ["--client", "codex", "--connector", flag],
                )
            self.assertEqual(
                worker.read_bytes(),
                (plugin / "runtime/openreading-worker").read_bytes(),
            )
            info = json.loads((moved / "build.json").read_text())
            self.assertEqual(info["client"], "codex")
            self.assertFalse(info["runtime_download"])
            self.assertIn("codex plugin add", (plugin / "README.md").read_text())

    def test_cli_accepts_codex_with_existing_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with (
                patch.object(build_server, "build_runtime") as freeze,
                patch.object(build_server, "package", return_value=root / "codex.zip") as package,
                patch("builtins.print"),
            ):
                try:
                    build_server.main(
                        [
                            "--runtime",
                            str(root / "runtime"),
                            "--client",
                            "codex",
                            "--output",
                            str(root / "build"),
                        ]
                    )
                except SystemExit as error:
                    self.fail(f"Codex package option missing: {error}")
            freeze.assert_not_called()
            package.assert_called_once_with(
                root / "runtime", root / "build/package", client="codex"
            )
