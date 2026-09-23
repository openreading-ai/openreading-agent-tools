"""Fresh installation backs up Claude state and keeps runtime execution out of Downloads."""

import fcntl
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_chatgpt_package
from openreading.artifacts.limits import ArtifactError

from runtime.configuration import client_root


class FreshInstallTests(unittest.TestCase):
    def setUp(self):
        from runtime import fresh_install

        self.api = fresh_install
        fixture = test_chatgpt_package.ChatGPTPackageTests()
        self.addCleanup(fixture.doCleanups)
        self.source = fixture.fixture()
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.running_workers = fresh_install.running_workers
        self.enterContext(patch.object(fresh_install, "running_workers", return_value=False))

    def test_installs_verified_runtime_and_backs_up_only_claude_state(self):
        control = client_root("claude-desktop", home=self.home)
        control.mkdir(parents=True)
        (control / "marker").write_text("prior settings")
        data = self.home / ".openreading/clients/claude-desktop/v2"
        data.mkdir(parents=True)
        (data / "marker").write_text("prior documents")
        other = client_root("chatgpt", home=self.home)
        other.mkdir()
        (other / "marker").write_text("untouched")
        result = self.api.install(self.source.root, home=self.home)
        self.assertNotIn("Downloads", result["runtime"])
        self.assertTrue((Path(result["runtime"]) / "openreading-worker").is_file())
        self.assertFalse(control.exists())
        self.assertFalse(data.exists())
        backup = Path(result["backup"])
        self.assertEqual((backup / "settings/marker").read_text(), "prior settings")
        self.assertEqual((backup / "default-data/marker").read_text(), "prior documents")
        self.assertEqual((other / "marker").read_text(), "untouched")
        again = self.api.install(self.source.root, home=self.home)
        self.assertEqual(again["runtime"], result["runtime"])

    def test_active_connections_and_jobs_refuse_before_backups(self):
        with (
            patch.object(self.api, "running_workers", return_value=True),
            self.assertRaises(ValueError),
        ):
            self.api.install(self.source.root, home=self.home)
        control = client_root("claude-desktop", home=self.home)
        job = control / "v2/artifacts/jobs/grant/job"
        job.mkdir(parents=True)
        (job / "status.json").write_text(json.dumps({"state": "running"}))
        with self.assertRaises(ValueError):
            self.api.install(self.source.root, home=self.home)
        self.assertTrue(job.exists())

    def test_failed_backup_rolls_back_prior_moves(self):
        control = client_root("claude-desktop", home=self.home)
        control.mkdir(parents=True)
        (control / "marker").write_text("settings")
        data = self.home / ".openreading/clients/claude-desktop/v2"
        data.mkdir(parents=True)
        (data / "marker").write_text("data")
        original = Path.rename

        def rename(path, target):
            if path == data:
                raise OSError("synthetic disk error")
            return original(path, target)

        with patch.object(Path, "rename", rename), self.assertRaises((OSError, ArtifactError)):
            self.api.install(self.source.root, home=self.home)
        self.assertEqual((control / "marker").read_text(), "settings")
        self.assertEqual((data / "marker").read_text(), "data")

    def test_process_preflight_ignores_self_and_unrelated_clients(self):
        for command, expected in [
            (f"{os.getpid()} /tmp/openreading-worker --client claude-desktop", False),
            ("100 /tmp/openreading-worker --client chatgpt --chat-documents", False),
            ("100 /tmp/openreading-worker --client claude-desktop --settings-tools", True),
            ("100 /tmp/openreading-worker --internal-server-job /tmp/request", True),
            ("100 /Applications/Claude.app/Claude", False),
        ]:
            with patch.object(
                self.api.subprocess, "run", return_value=SimpleNamespace(stdout=command)
            ):
                self.assertEqual(self.running_workers(), expected)

    def test_locked_connection_and_corrupt_cached_runtime_are_preserved(self):
        control = client_root("claude-desktop", home=self.home)
        control.mkdir(parents=True)
        with (control / "storage.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
            with self.assertRaises(ValueError):
                self.api.install(self.source.root, home=self.home)
        result = self.api.install(self.source.root, home=self.home)
        target = Path(result["runtime"])
        (target / "openreading-worker").write_text("corrupt")
        with self.assertRaises(ValueError):
            self.api.install(self.source.root, home=self.home)
        self.assertEqual((target / "openreading-worker").read_text(), "corrupt")

    def test_custom_data_remains_and_copy_failure_changes_no_settings(self):
        from runtime.app_settings import write_private

        custom = self.home / "custom"
        custom.mkdir()
        (custom / "marker").write_text("retained")
        control = client_root("claude-desktop", home=self.home)
        write_private(control / "storage.json", {"schema_version": 1, "active_root": str(custom)})
        with (
            patch.object(self.api.shutil, "copytree", side_effect=OSError("disk full")),
            self.assertRaises((OSError, ArtifactError)),
        ):
            self.api.install(self.source.root, home=self.home)
        self.assertTrue((control / "storage.json").exists())
        result = self.api.install(self.source.root, home=self.home)
        self.assertEqual(result["custom_data_preserved"], str(custom))
        self.assertEqual((custom / "marker").read_text(), "retained")
