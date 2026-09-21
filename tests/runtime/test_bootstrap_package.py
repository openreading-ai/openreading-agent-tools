"""The native upload includes its downloader and pins only the intended runtime asset."""

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import test_chatgpt_package

from runtime import bootstrap_package


class BootstrapPackageTests(unittest.TestCase):
    def test_small_upload_has_both_connectors_and_no_manual_installer(self):
        owner = test_chatgpt_package.ChatGPTPackageTests()
        self.addCleanup(owner.doCleanups)
        fixture = owner.fixture()
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        binary = root / "bootstrap"
        binary.write_bytes(b"synthetic frozen launcher")
        with patch.object(bootstrap_package, "catalog", return_value={"tools": []}):
            target = bootstrap_package.package(
                fixture.root, binary, root / "output", "https://example.test/runtime.tar.gz"
            )
        with zipfile.ZipFile(target) as archive:
            names = archive.namelist()
            self.assertNotIn("Install OpenReading.command", names)
            self.assertIn("openreading-bootstrap", names)
            config = json.loads(archive.read("bootstrap.json"))
            self.assertEqual(config["worker_sha256"], fixture.metadata["worker_sha256"])
            self.assertEqual(config["url"], "https://example.test/runtime.tar.gz")
            self.assertEqual(set(config["catalogs"]), {"--chat-documents", "--settings-tools"})
            self.assertEqual(len(json.loads(archive.read(".mcp.json"))["mcpServers"]), 2)
            self.assertNotIn("Downloads", archive.read("launch.sh").decode())
        self.assertTrue((root / "output/OpenReading-runtime-macOS-arm64.tar.gz").is_file())
        with self.assertRaises(ValueError):
            bootstrap_package.package(
                fixture.root, binary, root / "bad", "http://example.test/file"
            )

    def test_catalog_capture_initializes_exact_worker_and_closes_it(self):
        child = MagicMock()
        child.stdout = io.StringIO('{"id":1,"result":{}}\n{"id":2,"result":{"tools":[]}}\n')
        with patch.object(bootstrap_package.subprocess, "Popen", return_value=child):
            self.assertEqual(
                bootstrap_package.catalog(Path("/worker"), "--settings-tools"), {"tools": []}
            )
        child.stdin.close.assert_called_once()
        child.wait.assert_called_once()
        child.stdout = io.StringIO('{"id":1,"error":{}}\n')
        with (
            patch.object(bootstrap_package.subprocess, "Popen", return_value=child),
            self.assertRaises(ValueError),
        ):
            bootstrap_package.catalog(Path("/worker"), "--settings-tools")

    def test_packager_command_uses_explicit_url(self):
        with (
            patch.object(
                bootstrap_package.sys if hasattr(bootstrap_package, "sys") else __import__("sys"),
                "argv",
                [
                    "package",
                    "--runtime",
                    "/runtime",
                    "--bootstrap",
                    "/binary",
                    "--output",
                    "/output",
                    "--url",
                    "https://example.test/file",
                ],
            ),
            patch.object(
                bootstrap_package, "package", return_value=Path("/output/plugin.zip")
            ) as package,
            patch("builtins.print"),
        ):
            bootstrap_package.main()
        self.assertEqual(package.call_args.args[-1], "https://example.test/file")
