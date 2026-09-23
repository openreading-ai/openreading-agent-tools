"""Client packages preserve one verified runtime and never overwrite prior builds."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.package import package_clients


class PackagingTests(unittest.TestCase):
    def test_clients_receive_shared_skill_and_identical_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            runtime.mkdir()
            (runtime / "openreading-worker").write_bytes(b"synthetic runtime")
            (runtime / "release.json").write_text("{}")
            with patch(
                "runtime.package.verify_release",
                return_value={"format_version": "1", "worker_sha256": "a" * 64},
            ):
                paths = package_clients(runtime, root / "packages")
                for client, path in paths.items():
                    self.assertEqual(
                        (path / "server/openreading-worker").read_bytes(),
                        b"synthetic runtime",
                    )
                    self.assertFalse((path / "docling").exists())
                    self.assertFalse((path / "selection").exists())
                    if client == "claude-desktop":
                        guide = (path / "README.md").read_text()
                        self.assertIn("Historical revision 1", guide)
                        self.assertNotIn("Docling", guide)
                        self.assertIn("claude-desktop/v1/", guide)
                        self.assertFalse((path / "historical").exists())
                    if client != "claude-desktop":
                        self.assertTrue((path / "skills/read-local-document/SKILL.md").is_file())
                        manifest_path = (
                            ".claude-plugin/plugin.json"
                            if client == "claude-code"
                            else "plugin.json"
                        )
                        config_path = ".mcp.json" if client == "claude-code" else "mcp.json"
                        manifest = json.loads((path / manifest_path).read_text())
                        config = json.loads((path / config_path).read_text())
                        self.assertEqual(manifest["name"], "openreading-local-proof")
                        self.assertEqual(manifest["version"], "0.1.0-alpha.1")
                        self.assertIn("Historical revision 1", (path / "README.md").read_text())
                        self.assertFalse((path / "historical").exists())
                        args = config["mcpServers"]["openreading"]["args"]
                        args = [
                            str(root) if arg == "${user_config.input_root}" else arg for arg in args
                        ]
                        from runtime.entrypoint import main

                        with (
                            patch("sys.platform", "darwin"),
                            patch("platform.machine", return_value="arm64"),
                            patch("sys.frozen", True, create=True),
                            patch(
                                "runtime.entrypoint.verify_release",
                                return_value={"format_version": "1"},
                            ),
                            patch("runtime.entrypoint.read_grant", return_value=root),
                            patch("openreading.mcp_server.main.main", return_value=0) as core_main,
                        ):
                            self.assertEqual(main(args), 0)
                        self.assertIn("local-document-proof-v1", core_main.call_args.args[0])
                with self.assertRaises(ValueError):
                    package_clients(runtime, root / "packages")

    def test_invalid_runtime_creates_no_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                package_clients(root, root / "output")
            self.assertFalse((root / "output").exists())
