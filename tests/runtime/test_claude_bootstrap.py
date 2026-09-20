"""Runtime setup uses synthetic archives and a fake downloader, never real installs."""

import hashlib
import importlib
import shlex
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


class BootstrapTests(unittest.TestCase):
    def fixture(self, failure=None, client="claude-desktop"):
        module = importlib.import_module("runtime.claude_bootstrap")
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        plugin = root / "plugin café"
        plugin.mkdir()
        runtime = root / "runtime"
        runtime.mkdir()
        worker = runtime / "openreading-worker"
        worker.write_text('#!/bin/sh\nprintf "worker:%s\\n" "$*"\n')
        worker.chmod(0o755)
        (runtime / "release.json").write_text('{"synthetic": true}')
        payload = root / "runtime.tar.gz"
        with tarfile.open(payload, "w:gz") as packed:
            for name in ("openreading-worker", "release.json"):
                packed.add(runtime / name, arcname=name)

        def sha(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()

        metadata = {"worker_sha256": sha(worker)}
        if failure == "identity":
            metadata["worker_sha256"] = "c" * 64
        download = {
            "url": "https://example.invalid/v1/runtime.tar.gz",
            "sha256": sha(payload),
            "length": payload.stat().st_size,
        }
        if failure == "digest":
            download["sha256"] = "b" * 64
        if failure == "length":
            download["length"] += 1
        if failure == "archive":
            payload.write_bytes(b"not an archive")
            download.update(sha256=sha(payload), length=payload.stat().st_size)
        downloader = root / "curl"
        downloader.write_text(
            '#!/bin/sh\nprintf call >> "$HOME/downloads"\n'
            + (
                "exit 22\n"
                if failure == "network"
                else 'while [ "$1" != "--output" ]; do shift; done\nshift\n/bin/cp '
                + shlex.quote(str(payload))
                + ' "$1"\n'
            )
        )
        downloader.chmod(0o755)
        script = module.launcher(metadata, sha(runtime / "release.json"), download, client=client)
        script = script.replace("/usr/bin/curl", shlex.quote(str(downloader)))
        launch = plugin / "launch.sh"
        launch.write_text(script)
        home = root / "home"
        home.mkdir()
        return launch, home

    def run_launcher(self, launch, home, *args):
        return subprocess.run(
            ["/bin/sh", str(launch), *(args or ["--chat-documents"])],
            env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_verified_setup_reuses_cache_and_preserves_settings_entrypoint(self):
        launch, home = self.fixture()
        first = self.run_launcher(launch, home)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, "worker:--client claude-desktop --chat-documents\n")
        second = self.run_launcher(launch, home, "--destination-settings")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second.stdout, "worker:--client claude-desktop --destination-settings\n")
        self.assertEqual((home / "downloads").read_text(), "call")
        self.assertIn("setup", first.stderr)
        self.assertNotIn("setup", second.stderr)
        self.assertFalse(list(home.rglob("payload.tar.gz")))

    def test_download_failures_never_launch_or_publish_partial_runtime(self):
        for failure in ("digest", "length", "network", "archive", "identity"):
            with self.subTest(failure=failure):
                launch, home = self.fixture(failure)
                failed = self.run_launcher(launch, home)
                self.assertNotEqual(failed.returncode, 0)
                self.assertEqual(failed.stdout, "")
                self.assertFalse(list(home.rglob("openreading-worker")))
                self.assertFalse(list(home.rglob(".runtime.*")))
                self.assertFalse([p for p in home.rglob("*") if p.is_symlink()])

    def test_cached_worker_and_inventory_tampering_refuse_without_redownload(self):
        for name in ("openreading-worker", "release.json"):
            with self.subTest(name=name):
                launch, home = self.fixture()
                self.assertEqual(self.run_launcher(launch, home).returncode, 0)
                next(home.rglob(name)).write_text("changed")
                failed = self.run_launcher(launch, home)
                self.assertNotEqual(failed.returncode, 0)
                self.assertEqual(failed.stdout, "")
                self.assertIn("checksum", failed.stderr)
                self.assertEqual((home / "downloads").read_text(), "call")

    def test_shared_launcher_binds_client_without_changing_destination(self):
        launch, home = self.fixture(client="chatgpt")
        result = self.run_launcher(launch, home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "worker:--client chatgpt --chat-documents\n")
        self.assertFalse(list(home.rglob("destination.json")))

    def test_concurrent_starts_reuse_one_complete_runtime(self):
        launch, home = self.fixture()
        processes = [
            subprocess.Popen(
                ["/bin/sh", str(launch), "--chat-documents"],
                env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(3)
        ]
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertIn("worker:", stdout)
        self.assertEqual(len(list(home.rglob("openreading-worker"))), 1)
        self.assertEqual(len([p for p in home.rglob("*") if p.is_symlink()]), 1)

    def test_wrong_platform_refuses_before_downloading(self):
        launch, home = self.fixture()
        launch.write_text(launch.read_text().replace("/usr/bin/uname", "/usr/bin/false"))
        result = self.run_launcher(launch, home)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Apple Silicon", result.stderr)
        self.assertFalse((home / "downloads").exists())

    def test_unexpected_cache_entry_refuses_and_preserves_it(self):
        for broken in (False, True):
            with self.subTest(broken=broken):
                launch, home = self.fixture()
                self.assertEqual(self.run_launcher(launch, home).returncode, 0)
                cache = next(p for p in home.rglob("*") if p.is_symlink())
                cache.unlink()
                if broken:
                    cache.symlink_to(home / "missing")
                else:
                    cache.write_text("preserve")
                result = self.run_launcher(launch, home)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((home / "downloads").read_text(), "call")
                self.assertTrue(cache.is_symlink() if broken else cache.read_text() == "preserve")

    def test_interruption_after_publication_keeps_complete_cache_reusable(self):
        launch, home = self.fixture()
        link = launch.parent / "link-and-interrupt"
        link.write_text('#!/bin/sh\n/bin/ln "$@"\nkill -TERM "$PPID"\n')
        link.chmod(0o755)
        original = launch.read_text()
        launch.write_text(original.replace("/bin/ln", shlex.quote(str(link))))
        stopped = self.run_launcher(launch, home)
        self.assertNotEqual(stopped.returncode, 0)
        launch.write_text(original)
        resumed = self.run_launcher(launch, home)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertIn("worker:", resumed.stdout)
        self.assertEqual((home / "downloads").read_text(), "call")
