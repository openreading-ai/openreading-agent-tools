"""Destination settings are private, revisioned, and independent of legacy grants."""

import json
import tempfile
import unittest
from pathlib import Path

from runtime.destination_settings import read_destination, save_destination


class DestinationSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()

    def save(self, mode="server", url="http://localhost:8787"):
        return save_destination("chatgpt", mode, base_url=url, home=self.home)

    def test_missing_settings_default_local_and_server_has_private_file(self):
        self.assertEqual(read_destination("chatgpt", home=self.home).mode, "local")
        first = self.save()
        loaded = read_destination("chatgpt", home=self.home)
        self.assertEqual(loaded, first)
        path = next(self.home.rglob("destination.json"))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("synthetic-secret", path.read_text())
        self.assertEqual(json.loads(path.read_text())["schema_version"], 2)

    def test_new_saves_change_revision_and_preserve_previous_snapshot(self):
        first = self.save()
        second = self.save(url="https://different.invalid")
        self.assertNotEqual(first.revision, second.revision)
        self.assertEqual(first.destination.base_url, "http://localhost:8787")
        self.assertEqual(second.destination.base_url, "https://different.invalid")

    def test_local_mode_and_client_namespaces_remain_separate(self):
        self.save()
        self.assertEqual(read_destination("codex", home=self.home).mode, "local")
        local = self.save(mode="local")
        self.assertEqual(local.mode, "local")
        self.assertIsNone(local.destination)

    def test_invalid_saved_settings_fail_closed(self):
        self.save()
        path = next(self.home.rglob("destination.json"))
        original = json.loads(path.read_text())
        for value in (
            {},
            {**original, "token": "must-not-be-here"},
            {**original, "mode": "unknown"},
            {**original, "revision": "invalid"},
            {**original, "credential_ref": "../path"},
            {**original, "response_bytes": True},
        ):
            with self.subTest(value=value):
                path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError, "destination settings"):
                    read_destination("chatgpt", home=self.home)

    def test_symlink_settings_and_parent_are_refused(self):
        self.save()
        path = next(self.home.rglob("destination.json"))
        target = self.home / "unrelated.json"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        with self.assertRaises(ValueError):
            read_destination("chatgpt", home=self.home)

    def test_explicit_save_can_repair_broken_settings(self):
        self.save()
        path = next(self.home.rglob("destination.json"))
        path.write_text("broken settings")
        with self.assertRaises(ValueError):
            read_destination("chatgpt", home=self.home)
        self.assertEqual(self.save(mode="local").mode, "local")

    def test_large_and_nonregular_settings_are_refused(self):
        self.save()
        path = next(self.home.rglob("destination.json"))
        path.write_text("x" * 16385)
        with self.assertRaises(ValueError):
            read_destination("chatgpt", home=self.home)
        path.unlink()
        path.mkdir()
        with self.assertRaises(ValueError):
            read_destination("chatgpt", home=self.home)

    def test_invalid_mode_or_url_preserves_previous_settings(self):
        first = self.save()
        with self.assertRaises(ValueError):
            self.save(mode="unknown")
        with self.assertRaises(ValueError):
            self.save(url="http://remote.invalid")
        self.assertEqual(read_destination("chatgpt", home=self.home), first)


if __name__ == "__main__":
    unittest.main()
