"""Git distribution contains executable client packages, not upload archives."""

import contextlib
import importlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_build_server import captured_catalog

from runtime import build_server
from runtime.verify import inventory, verify_release


class GitHubMarketplaceTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime.github_marketplace"))
        return importlib.import_module("runtime.github_marketplace")

    def runtime(self, root):
        runtime = root / "runtime"
        (runtime / "resources").mkdir(parents=True)
        (runtime / "resources/server-client.uv.lock").write_text("fixture lock")
        worker = runtime / "openreading-worker"
        worker.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
        worker.chmod(0o755)
        (runtime / "THIRD_PARTY_NOTICES.txt").write_text("fixture notices")
        files = inventory(runtime)
        (runtime / "release.json").write_text(
            json.dumps(
                {
                    "format_version": "3",
                    "release_version": build_server.VERSION,
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
            )
        )
        return runtime

    def test_git_catalogs_resolve_four_complete_executable_client_packages(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix="github package ") as temporary:
            root = Path(temporary).resolve()
            runtime = self.runtime(root)
            output = root / "distribution"
            with patch.object(build_server, "catalog", side_effect=captured_catalog):
                module.assemble(runtime, output)
            expected = {
                "openreading": "claude-code",
                "openreading-cowork": "claude-desktop",
            }
            claude = json.loads((output / ".claude-plugin/marketplace.json").read_text())
            openai = json.loads((output / ".agents/plugins/marketplace.json").read_text())
            self.assertEqual({item["name"] for item in claude["plugins"]}, set(expected))
            self.assertEqual(
                {item["name"] for item in openai["plugins"]}, {"openreading", "openreading-chatgpt"}
            )
            for catalog, clients in (
                (claude, expected),
                (openai, {"openreading": "codex", "openreading-chatgpt": "chatgpt"}),
            ):
                for entry in catalog["plugins"]:
                    with self.subTest(client=clients[entry["name"]]):
                        source = entry["source"]
                        path = source if isinstance(source, str) else source["path"]
                        plugin = output / path
                        self.assertIn(
                            "(./SECURITY.md#remove-retained-data)",
                            (plugin / "README.md").read_text(),
                        )
                        self.assertIn(
                            "## Remove retained data", (plugin / "SECURITY.md").read_text()
                        )
                        manifest = next(plugin.glob(".*-plugin/plugin.json"))
                        self.assertTrue((plugin / "CHANGELOG.md").is_file())
                        self.assertEqual(json.loads(manifest.read_text())["name"], entry["name"])
                        self.assertEqual(len(list((plugin / "skills").glob("*/SKILL.md"))), 2)
                        self.assertEqual(
                            len(json.loads((plugin / ".mcp.json").read_text())["mcpServers"]), 2
                        )
                        self.assertEqual(
                            verify_release(plugin / "runtime")["worker_sha256"],
                            verify_release(runtime)["worker_sha256"],
                        )
                        result = subprocess.run(
                            [str(plugin / "launch.sh"), "--settings-tools"],
                            env={**os.environ, "HOME": str(root)},
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        self.assertEqual(
                            result.stdout.splitlines(),
                            ["--client", clients[entry["name"]], "--connector", "--settings-tools"],
                        )
            self.assertFalse(list(output.rglob("*.zip")))
            receipt = json.loads((output / "distribution.json").read_text())
            self.assertEqual(
                set(receipt["clients"]), {"claude-code", "claude-desktop", "codex", "chatgpt"}
            )
            self.assertTrue((output / "LICENSE").is_file())
            with self.assertRaises(FileExistsError):
                module.assemble(runtime, output)

    def test_remote_catalogs_pin_git_content_not_archives_or_local_machine_paths(self):
        module = self.module()
        catalogs = module.catalogs("a" * 40)
        self.assertEqual(len(catalogs), 2)
        for catalog in catalogs.values():
            for entry in catalog["plugins"]:
                self.assertEqual(entry["source"]["source"], "git-subdir")
                self.assertEqual(
                    entry["source"]["url"],
                    "https://github.com/openreading-ai/openreading-agent-tools.git",
                )
                self.assertEqual(entry["source"]["sha"], "a" * 40)
                self.assertTrue(entry["source"]["path"].startswith("plugins/"))
                self.assertNotIn("headersHelper", entry)
        for revision in ("main", "v0.2.0", "a" * 39, "../private"):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                module.catalogs(revision)

    def test_cli_assembles_verified_runtime_without_rebuilding(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            runtime = self.runtime(root)
            with (
                patch.object(build_server, "catalog", side_effect=captured_catalog),
                contextlib.redirect_stdout(io.StringIO()) as stdout,
            ):
                self.assertEqual(
                    module.main(["--runtime", str(runtime), "--output", str(root / "dist")]), 0
                )
            self.assertIn(str(root / "dist"), stdout.getvalue())

    def test_source_catalogs_match_the_packaged_clients_and_one_immutable_commit(self):
        module = self.module()
        root = Path(module.__file__).resolve().parent.parent
        claude = json.loads((root / ".claude-plugin/marketplace.json").read_text())
        commit = claude["plugins"][0]["source"]["sha"]
        for name, expected in module.catalogs(commit).items():
            self.assertEqual(json.loads((root / name).read_text()), expected)
