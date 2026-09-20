"""First-use setup is tested with tiny synthetic files and a fake downloader."""

import hashlib
import importlib
import subprocess
import tempfile
import unittest
from pathlib import Path


class BootstrapTests(unittest.TestCase):
    def fixture(self, failure=False):
        self.assertIsNotNone(importlib.util.find_spec("runtime.claude_bootstrap"))
        module = importlib.import_module("runtime.claude_bootstrap")
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        plugin = root / "plugin café"
        (plugin / "server/resources/models/model").mkdir(parents=True)
        worker = plugin / "server/openreading-worker"
        worker.write_text('#!/bin/sh\nprintf "worker:%s\\n" "$*"\n')
        worker.chmod(0o755)
        model = b"correct model"
        downloader = root / "curl"
        downloader.write_text(
            '#!/bin/sh\nwhile [ "$1" != "--output" ]; do shift; done\nshift\nprintf '
            + ("wrong" if failure else "'correct model'")
            + ' > "$1"\nprintf call >> "$HOME/downloads"\n'
        )
        downloader.chmod(0o755)
        metadata = {
            "files": {
                "resources/models/model/model.onnx": {
                    "sha256": hashlib.sha256(model).hexdigest(),
                    "length": len(model),
                },
                "openreading-worker": {"executable": True},
            },
            "worker_sha256": hashlib.sha256(worker.read_bytes()).hexdigest(),
        }
        script = module.launcher(
            metadata,
            "a" * 64,
            "https://example.invalid/pinned-model",
            "resources/models/model/model.onnx",
        )
        script = script.replace("/usr/bin/curl", str(downloader))
        launch = plugin / "launch.sh"
        launch.write_text(script)
        home = root / "home"
        home.mkdir()
        return launch, home

    def run_launcher(self, launch, home):
        return subprocess.run(
            ["/bin/sh", str(launch), "--chat-documents"],
            env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_verified_setup_reuses_cache_and_preserves_arguments(self):
        launch, home = self.fixture()
        first = self.run_launcher(launch, home)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, "worker:--client claude-desktop --chat-documents\n")
        second = self.run_launcher(launch, home)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((home / "downloads").read_text(), "call")
        self.assertFalse(list(home.rglob(".setup.*")))

    def test_download_digest_mismatch_never_launches_or_publishes(self):
        launch, home = self.fixture(failure=True)
        failed = self.run_launcher(launch, home)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(failed.stdout, "")
        self.assertIn("checksum", failed.stderr)
        self.assertFalse(list(home.rglob("openreading-worker")))
        self.assertFalse(list(home.rglob(".setup.*")))
