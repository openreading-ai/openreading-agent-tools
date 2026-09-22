"""Client packages preserve one verified runtime and never overwrite prior builds."""

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
                        self.assertTrue((path / "skills/openreading/SKILL.md").is_file())
                with self.assertRaises(ValueError):
                    package_clients(runtime, root / "packages")

    def test_invalid_runtime_creates_no_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                package_clients(root, root / "output")
            self.assertFalse((root / "output").exists())
