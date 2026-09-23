"""Native preferences are private, client scoped, and never grant source access."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.configuration import client_root


class AppSettingsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.app_settings"),
            "Missing real application preferences",
        )
        from runtime import app_settings

        self.api = app_settings
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()

    def test_defaults_saved_values_and_client_isolation(self):
        default = self.api.read_preferences("chatgpt", home=self.home)
        self.assertEqual(default.data_folder, self.home / ".openreading")
        self.assertEqual(default.document_response_bytes, 1_000_000)
        folder = self.home / "Downloads/OpenReading"
        saved = self.api.save_preferences("chatgpt", folder, 8192, home=self.home)
        self.assertEqual(self.api.read_preferences("chatgpt", home=self.home), saved)
        self.assertEqual(self.api.read_preferences("codex", home=self.home), default)
        self.assertFalse(folder.exists(), "Saving stages a choice; launch owns migration")
        path = client_root("chatgpt", home=self.home) / "preferences.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("input_root", json.loads(path.read_text()))

    def test_invalid_save_preserves_prior_values_and_bad_file_never_falls_back(self):
        saved = self.api.save_preferences("chatgpt", self.home / "data", 4096, home=self.home)
        for folder, budget in [
            (Path("relative"), 4096),
            (self.home, 4095),
            (self.home, True),
            (self.home, "8192"),
        ]:
            with self.assertRaises(ValueError):
                self.api.save_preferences("chatgpt", folder, budget, home=self.home)
            self.assertEqual(self.api.read_preferences("chatgpt", home=self.home), saved)
        path = client_root("chatgpt", home=self.home) / "preferences.json"
        path.write_text("{}")
        with self.assertRaises(ValueError):
            self.api.read_preferences("chatgpt", home=self.home)

    def test_failed_replace_keeps_current_preferences(self):
        saved = self.api.save_preferences("chatgpt", self.home / "data", 8192, home=self.home)
        with (
            patch("os.replace", side_effect=OSError("disk full")),
            self.assertRaises(ValueError),
        ):
            self.api.save_preferences("chatgpt", self.home / "other", 4096, home=self.home)
        self.assertEqual(self.api.read_preferences("chatgpt", home=self.home), saved)

    def test_advanced_defaults_legacy_values_and_private_independent_save(self):
        from runtime.destination_settings import save_destination

        self.assertTrue(hasattr(self.api, "read_limits"))
        self.assertEqual(
            self.api.read_limits("chatgpt", home=self.home).server_response_bytes,
            256 * 1024 * 1024,
        )
        self.api.save_preferences("chatgpt", self.home / "data", 8192, home=self.home)
        save_destination(
            "chatgpt",
            "server",
            base_url="http://localhost",
            response_bytes=4194304,
            home=self.home,
        )
        legacy = self.api.read_limits("chatgpt", home=self.home)
        self.assertEqual(
            (legacy.document_response_bytes, legacy.server_response_bytes),
            (8192, 4194304),
        )
        self.api.save_limits("chatgpt", 16384, 8388608, home=self.home)
        saved = self.api.read_limits("chatgpt", home=self.home)
        self.assertEqual(
            (saved.document_response_bytes, saved.server_response_bytes),
            (16384, 8388608),
        )
        path = client_root("chatgpt", home=self.home) / "advanced.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        for maximum in (0, True, "256"):
            with self.assertRaises(ValueError):
                self.api.save_limits("chatgpt", 8192, maximum, home=self.home)
        with (
            patch("os.replace", side_effect=OSError("disk full")),
            self.assertRaises(ValueError),
        ):
            self.api.save_limits("chatgpt", 8192, 4194304, home=self.home)
        self.assertEqual(self.api.read_limits("chatgpt", home=self.home), saved)
        for bad in (
            {},
            {
                "schema_version": 1,
                "document_response_bytes": 8192,
                "server_response_bytes": 0,
            },
        ):
            path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                self.api.read_limits("chatgpt", home=self.home)
