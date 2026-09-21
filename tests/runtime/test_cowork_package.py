"""Cowork gets separate settings and document connectors without user-config placeholders."""

import json
import tempfile
import unittest
from pathlib import Path

import test_chatgpt_package

from runtime import package


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
