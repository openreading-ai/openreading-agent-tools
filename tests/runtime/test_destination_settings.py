"""Destination settings are private, revisioned, and independent of legacy grants."""

import json
import tempfile
import unittest
from pathlib import Path

from runtime.destination_settings import read_destination, save_destination


class Keychain:
    def __init__(self):
        self.values = {}

    def put(self, reference, token):
        self.values[reference] = token

    def get(self, reference):
        return self.values[reference]


class DestinationSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.keys = Keychain()

    def save(self, mode="server", url="http://localhost:8787", token=None):
        return save_destination(
            "chatgpt", mode, base_url=url, token=token, home=self.home, keychain=self.keys
        )

    def test_missing_settings_default_local_and_server_has_private_file(self):
        self.assertEqual(read_destination("chatgpt", home=self.home).mode, "local")
        first = self.save(token="synthetic-secret")
        loaded = read_destination("chatgpt", home=self.home)
        self.assertEqual(loaded, first)
        self.assertEqual(self.keys.get(first.credential_ref), "synthetic-secret")
        path = next(self.home.rglob("destination.json"))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("synthetic-secret", path.read_text())
        self.assertEqual(json.loads(path.read_text())["schema_version"], 1)

    def test_new_url_does_not_inherit_credentials_and_jobs_keep_old_reference(self):
        first = self.save(token="synthetic-secret")
        second = self.save(url="https://different.invalid")
        self.assertIsNone(second.credential_ref)
        self.assertNotEqual(first.revision, second.revision)
        self.assertEqual(self.keys.get(first.credential_ref), "synthetic-secret")
        self.assertEqual(first.destination.base_url, "http://localhost:8787")

    def test_same_url_preserves_key_unless_explicitly_cleared(self):
        first = self.save(token="synthetic-secret")
        second = self.save()
        self.assertEqual(first.credential_ref, second.credential_ref)
        self.assertNotEqual(first.revision, second.revision)
        self.assertIsNone(self.save(token="").credential_ref)

    def test_local_mode_and_client_namespaces_remain_separate(self):
        first = self.save(token="synthetic-secret")
        self.assertEqual(read_destination("codex", home=self.home).mode, "local")
        local = self.save(mode="local")
        self.assertEqual(local.mode, "local")
        self.assertIsNone(local.destination)
        self.assertIsNone(local.credential_ref)
        self.assertEqual(self.keys.get(first.credential_ref), "synthetic-secret")

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

    def test_save_validates_mode_and_uses_default_keychain(self):
        from unittest.mock import patch

        with self.assertRaises(ValueError):
            self.save(mode="unknown")
        with patch("runtime.server_keychain.ServerKeychain", return_value=self.keys):
            result = save_destination(
                "chatgpt", "server", base_url="http://localhost", token="synthetic", home=self.home
            )
        self.assertEqual(self.keys.get(result.credential_ref), "synthetic")

    def test_keychain_failure_preserves_previous_settings(self):
        first = self.save()

        def fail(reference, token):
            raise ValueError("Keychain unavailable")

        self.keys.put = fail
        with self.assertRaises(ValueError):
            self.save(token="new-token")
        self.assertEqual(read_destination("chatgpt", home=self.home), first)


if __name__ == "__main__":
    unittest.main()
