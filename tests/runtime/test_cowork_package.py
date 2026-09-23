"""Cowork gets separate settings and document connectors without user-config placeholders."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import test_chatgpt_package

from runtime import package
from runtime.verify import inventory, sha256


class CoworkPackageTests(unittest.TestCase):
    def test_package_discovers_namespaced_settings_and_retains_core_connector(self):
        self.assertTrue(
            hasattr(package, "package_cowork_plugin"), "Missing Cowork settings packaging"
        )
        fixture = test_chatgpt_package.ChatGPTPackageTests()
        self.addCleanup(fixture.doCleanups)
        source = fixture.fixture()
        root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "plugin"
        package.package_cowork_plugin(source.root, root)
        config = json.loads((root / ".mcp.json").read_text())["mcpServers"]
        self.assertEqual(set(config), {"openreading", "openreading-settings"})
        self.assertEqual(config["openreading-settings"]["args"][-1], "--settings-tools")
        self.assertEqual(config["openreading"]["args"][-1], "--chat-documents")
        self.assertNotIn("user_config", (root / ".mcp.json").read_text())
        self.assertTrue((root / "skills/openreading-settings/SKILL.md").is_file())

    def test_fresh_installer_contains_complete_runtime_and_small_native_plugin(self):
        self.assertTrue(hasattr(package, "package_cowork_installer"))
        fixture = test_chatgpt_package.ChatGPTPackageTests()
        self.addCleanup(fixture.doCleanups)
        source = fixture.fixture()
        root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "install"
        package.package_cowork_installer(source.root, root)
        self.assertTrue((root / "runtime/openreading-worker").is_file())
        setup = (root / "Install OpenReading.command").read_text()
        self.assertIn('cd "$HOME"', setup)
        self.assertIn("--fresh-install", setup)
        self.assertNotIn("/Users/akshay", setup)
        with zipfile.ZipFile(root / "OpenReading-Claude.zip") as archive:
            self.assertIn("skills/openreading-settings/SKILL.md", archive.namelist())
            launcher = archive.read("launch.sh").decode()
            self.assertIn("Library/Application Support/OpenReading", launcher)
            self.assertNotIn("Downloads", launcher)
            self.assertNotIn("runtime/openreading-worker", launcher)

    @unittest.skipUnless(sys.platform == "darwin", "macOS setup uses built-in ditto")
    def test_setup_runs_from_home_after_copy_and_does_not_require_python(self):
        fixture = test_chatgpt_package.ChatGPTPackageTests()
        self.addCleanup(fixture.doCleanups)
        source = fixture.fixture()
        worker = source.root / "openreading-worker"
        worker.write_text('#!/bin/sh\npwd\nprintf "%s\\n" "$0" "$@"\n')
        worker.chmod(0o755)
        source.metadata["worker_sha256"] = sha256(worker)
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        base = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        home = base / "Home with spaces"
        home.mkdir()
        root = base / "Downloads/Setup with spaces"
        package.package_cowork_installer(source.root, root)
        result = subprocess.run(
            ["/bin/sh", str(root / "Install OpenReading.command")],
            env={**os.environ, "HOME": str(home), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(home) + "\n", result.stdout)
        self.assertIn("/Application Support/OpenReading/agent-tools/.setup.", result.stdout)
        self.assertIn("--fresh-install", result.stdout)
        self.assertFalse(list(home.rglob(".setup.*")))
