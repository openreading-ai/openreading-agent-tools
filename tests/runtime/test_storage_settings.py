"""Storage switches preserve data and refuse concurrent writers or occupied targets."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime.app_settings import save_preferences
from runtime.configuration import client_root


class StorageSettingsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.storage_settings"), "Missing storage lifecycle"
        )
        from runtime import storage_settings

        self.api = storage_settings
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()

    def test_default_partition_and_exports_do_not_grant_selected_folder(self):
        with self.api.storage_session("chatgpt", home=self.home) as root:
            self.assertEqual(root, self.home / ".openreading/clients/chatgpt/v2")
            self.assertEqual(self.api.data_root("chatgpt", home=self.home), root)
        self.assertEqual(
            self.api.data_root("codex", home=self.home), self.home / ".openreading/clients/codex/v2"
        )

    def test_save_stages_change_and_reconnect_copies_without_deleting_original(self):
        with self.api.storage_session("chatgpt", home=self.home) as old:
            (old / "retained.txt").write_text("synthetic retained bytes")
            save_preferences("chatgpt", self.home / "Downloads/My Data", 8192, home=self.home)
            self.assertEqual(self.api.data_root("chatgpt", home=self.home), old)
            with self.assertRaisesRegex(ValueError, "connection"):
                with self.api.storage_session("chatgpt", home=self.home):
                    pass
        with self.api.storage_session("chatgpt", home=self.home) as new:
            self.assertEqual(new, self.home / "Downloads/My Data/clients/chatgpt/v2")
            self.assertEqual((new / "retained.txt").read_text(), "synthetic retained bytes")
            self.assertEqual((old / "retained.txt").read_text(), "synthetic retained bytes")

    def test_copy_failure_or_occupied_target_preserves_active_root(self):
        with self.api.storage_session("chatgpt", home=self.home) as old:
            (old / "retained.txt").write_text("original")
        chosen = self.home / "new"
        save_preferences("chatgpt", chosen, 8192, home=self.home)
        with patch.object(self.api, "copy_tree", side_effect=OSError("disk full")):
            with self.assertRaises(ValueError):
                with self.api.storage_session("chatgpt", home=self.home):
                    pass
        self.assertEqual(self.api.data_root("chatgpt", home=self.home), old)
        target = chosen / "clients/chatgpt/v2"
        target.mkdir(parents=True, exist_ok=True)
        (target / "unrelated").write_text("untouched")
        with self.assertRaises(ValueError):
            with self.api.storage_session("chatgpt", home=self.home):
                pass
        self.assertEqual((target / "unrelated").read_text(), "untouched")

    def test_legacy_store_and_other_client_are_preserved(self):
        legacy = client_root("chatgpt", home=self.home) / "v2"
        legacy.mkdir(parents=True)
        (legacy / "retained.txt").write_text("legacy")
        with self.api.storage_session("chatgpt", home=self.home) as root:
            self.assertEqual((root / "retained.txt").read_text(), "legacy")
        self.assertEqual((legacy / "retained.txt").read_text(), "legacy")

    def test_abandoned_legacy_profile_does_not_block_move_or_follow_data(self):
        legacy = client_root("chatgpt", home=self.home) / "v2"
        launch = legacy / "launch/abandoned"
        launch.mkdir(parents=True)
        (launch / "profile.json").write_text("{}")
        (legacy / "retained.txt").write_text("kept")
        save_preferences("chatgpt", self.home / ".openreading", 8192, home=self.home)
        with patch(
            "subprocess.run",
            return_value=SimpleNamespace(returncode=0, stdout=f"{os.getpid()} python", stderr=""),
        ):
            with self.api.storage_session("chatgpt", home=self.home) as new:
                self.assertEqual((new / "retained.txt").read_text(), "kept")
                self.assertFalse((new / "launch").exists())
        self.assertTrue((launch / "profile.json").exists())

    def test_saved_choice_and_blocking_reason_survive_reopening(self):
        legacy = client_root("chatgpt", home=self.home) / "v2"
        legacy.mkdir(parents=True)
        initial = self.api.storage_view("chatgpt", home=self.home)
        self.assertEqual(initial["folder"], legacy.parent.parent)
        self.assertEqual(initial["state"], "active")
        save_preferences("chatgpt", self.home / ".openreading", 8192, home=self.home)
        self.assertEqual(self.api.storage_view("chatgpt", home=self.home)["state"], "pending")
        with patch.object(self.api, "migrate", side_effect=ValueError("Synthetic move blocked")):
            with self.assertRaisesRegex(ValueError, "Synthetic"):
                with self.api.storage_session("chatgpt", home=self.home):
                    pass
        blocked = self.api.storage_view("chatgpt", home=self.home)
        self.assertEqual(blocked["folder"], self.home / ".openreading")
        self.assertEqual(blocked["state"], "blocked")
        self.assertIn("Synthetic move blocked", blocked["message"])
        with self.api.storage_session("chatgpt", home=self.home):
            pass
        self.assertEqual(self.api.storage_view("chatgpt", home=self.home)["state"], "active")

    def test_application_storage_choice_keeps_existing_partition(self):
        legacy = client_root("chatgpt", home=self.home) / "v2"
        legacy.mkdir(parents=True)
        save_preferences("chatgpt", legacy.parent.parent, 8192, home=self.home)
        with self.api.storage_session("chatgpt", home=self.home) as active:
            self.assertEqual(active, legacy)

    def test_profile_lease_and_legacy_inspection_fail_closed(self):
        import fcntl
        import subprocess

        launch = client_root("chatgpt", home=self.home) / "v2/launch/test"
        launch.mkdir(parents=True)
        profile = launch / "profile.json"
        profile.write_text("{}")
        lease = launch / "session.lock"
        with lease.open("w") as opened:
            fcntl.flock(opened, fcntl.LOCK_EX)
            self.assertTrue(self.api.profile_in_use(profile))
        self.assertFalse(self.api.profile_in_use(profile))
        lease.unlink()
        for result in [
            SimpleNamespace(returncode=2, stdout="", stderr="failed"),
            SimpleNamespace(returncode=0, stdout="unparseable\n123 unknown", stderr=""),
            OSError("missing"),
            subprocess.TimeoutExpired("ps", 5),
        ]:
            with patch(
                "subprocess.run",
                **(
                    {"side_effect": result}
                    if isinstance(result, Exception)
                    else {"return_value": result}
                ),
            ):
                with self.assertRaisesRegex(ValueError, "Cannot verify"):
                    self.api.profile_in_use(profile)
        with patch(
            "subprocess.run",
            return_value=SimpleNamespace(returncode=0, stdout=f"123 worker {profile}", stderr=""),
        ):
            self.assertTrue(self.api.profile_in_use(profile))

    def test_nonterminal_jobs_and_symlinks_block_migration(self):
        import json

        with self.api.storage_session("chatgpt", home=self.home) as old:
            job = old / "artifacts/jobs/grant/j1_synthetic"
            job.mkdir(parents=True)
            (job / "status.json").write_text(json.dumps({"state": "running"}))
        save_preferences("chatgpt", self.home / "new", 8192, home=self.home)
        with self.assertRaisesRegex(ValueError, "import"):
            with self.api.storage_session("chatgpt", home=self.home):
                pass
        (job / "status.json").write_text(json.dumps({"state": "succeeded"}))
        (old / "link").symlink_to(self.home)
        with self.assertRaises(ValueError):
            with self.api.storage_session("chatgpt", home=self.home):
                pass

    def test_bad_active_record_and_legacy_live_profile_refuse_migration(self):
        control = client_root("chatgpt", home=self.home)
        control.mkdir(parents=True)
        record = control / "storage.json"
        for value in ["{}", '{"schema_version":1,"active_root":"relative"}', "not json"]:
            record.write_text(value)
            with self.assertRaises(ValueError):
                self.api.data_root("chatgpt", home=self.home)
        record.unlink()
        legacy = control / "v2/launch/process"
        legacy.mkdir(parents=True)
        (legacy / "profile.json").write_text("{}")
        save_preferences("chatgpt", self.home / ".openreading", 8192, home=self.home)
        with patch(
            "subprocess.run",
            return_value=SimpleNamespace(
                returncode=0,
                stdout="999999 /app/openreading-worker --client chatgpt --chat-documents",
                stderr="",
            ),
        ):
            with self.assertRaisesRegex(ValueError, "connection"):
                with self.api.storage_session("chatgpt", home=self.home):
                    pass

    def test_nested_target_and_pointer_failure_preserve_previous_store(self):
        with self.api.storage_session("chatgpt", home=self.home) as old:
            (old / "kept").write_text("unchanged")
        save_preferences("chatgpt", old / "nested", 8192, home=self.home)
        with self.assertRaisesRegex(ValueError, "outside"):
            with self.api.storage_session("chatgpt", home=self.home):
                pass
        save_preferences("chatgpt", self.home / "new", 8192, home=self.home)
        with patch.object(self.api, "write_private", side_effect=OSError("full disk")):
            with self.assertRaises(ValueError):
                with self.api.storage_session("chatgpt", home=self.home):
                    pass
        self.assertEqual(self.api.data_root("chatgpt", home=self.home), old)
        self.assertFalse((self.home / "new/clients/chatgpt/v2").exists())
        self.assertEqual((old / "kept").read_text(), "unchanged")

    def test_switch_can_initialize_an_empty_previous_location(self):
        from runtime.app_settings import write_private

        write_private(
            client_root("chatgpt", home=self.home) / "storage.json",
            {"schema_version": 1, "active_root": str(self.home / "not-created")},
        )
        with self.api.storage_session("chatgpt", home=self.home) as root:
            self.assertTrue(root.is_dir())

    def test_missing_job_status_is_not_assumed_finished(self):
        with self.api.storage_session("chatgpt", home=self.home) as old:
            (old / "artifacts/jobs/grant/j1_unknown").mkdir(parents=True)
        save_preferences("chatgpt", self.home / "new", 8192, home=self.home)
        with self.assertRaises(ValueError):
            with self.api.storage_session("chatgpt", home=self.home):
                pass

    def test_existing_installation_can_finish_jobs_before_requesting_storage_migration(self):
        import json

        legacy = client_root("chatgpt", home=self.home) / "v2"
        job = legacy / "artifacts/jobs/grant/j1_pending"
        job.mkdir(parents=True)
        (job / "status.json").write_text(json.dumps({"state": "running"}))
        with self.api.storage_session("chatgpt", home=self.home) as root:
            self.assertEqual(root, legacy)

    def test_rechecks_exclusive_ownership_if_active_pointer_changes_during_startup(self):
        save_preferences("chatgpt", self.home / "current", 8192, home=self.home)
        with self.api.storage_session("chatgpt", home=self.home) as current:
            chosen = self.home / "next"
            target = chosen / "clients/chatgpt/v2"
            save_preferences("chatgpt", chosen, 8192, home=self.home)
            # Reproduce a stale initial pointer read while another connection holds its lease.
            with patch.object(self.api, "data_root", side_effect=[target, current]):
                with self.assertRaisesRegex(ValueError, "connection"):
                    with self.api.storage_session("chatgpt", home=self.home):
                        pass
            self.assertFalse(target.exists())
