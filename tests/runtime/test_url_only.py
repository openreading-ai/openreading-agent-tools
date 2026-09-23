"""Legacy destinations retain their URL without retaining authentication capability."""

import inspect
import unittest

from runtime.destination_settings import decode_settings, save_destination
from runtime.destination_ui import Controller
from runtime.server_transport import check_connection, parse_document


class UrlOnlyTests(unittest.TestCase):
    def test_legacy_destination_drops_reference_and_writes_current_schema(self):
        for reference in (None, "a" * 32):
            with self.subTest(reference=reference):
                settings = decode_settings(
                    {
                        "schema_version": 1,
                        "mode": "server",
                        "revision": "b" * 32,
                        "base_url": "https://core.example.test",
                        "response_bytes": 4194304,
                        "credential_ref": reference,
                    }
                )
                self.assertEqual(settings.destination.base_url, "https://core.example.test")
                self.assertEqual(settings.destination.response_bytes, 4194304)
                self.assertFalse(hasattr(settings, "credential_ref"))
                self.assertNotIn("credential_ref", settings.wire())
                self.assertEqual(settings.wire()["schema_version"], 2)
                self.assertEqual(decode_settings(settings.wire()), settings)

    def test_public_client_functions_have_no_credential_parameters(self):
        for function in (
            save_destination,
            Controller,
            Controller.save,
            Controller.check,
            parse_document,
            check_connection,
        ):
            with self.subTest(function=function):
                parameters = inspect.signature(function).parameters
                self.assertTrue({"token", "keychain", "clear"}.isdisjoint(parameters))

    def test_legacy_settings_save_removes_reference_without_changing_url_or_limit(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from runtime.destination_settings import read_destination

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            saved = save_destination(
                "codex",
                "server",
                base_url="https://core.example.test",
                response_bytes=4194304,
                home=home,
            )
            path = next(home.rglob("destination.json"))
            legacy = saved.wire() | {"schema_version": 1, "credential_ref": "c" * 32}
            path.write_text(json.dumps(legacy))
            with patch("ctypes.CDLL", side_effect=AssertionError("No Keychain access")):
                loaded = read_destination("codex", home=home)
                self.assertEqual(loaded, saved)
                updated = save_destination(
                    "codex",
                    "server",
                    base_url=loaded.destination.base_url,
                    response_bytes=loaded.destination.response_bytes,
                    home=home,
                )
            self.assertNotEqual(updated.revision, saved.revision)
            self.assertEqual(updated.destination.base_url, saved.destination.base_url)
            self.assertEqual(updated.destination.response_bytes, saved.destination.response_bytes)
            self.assertEqual(json.loads(path.read_text()), updated.wire())
            self.assertNotIn("credential_ref", path.read_text())

    def test_unknown_fields_and_invalid_legacy_references_remain_invalid(self):
        base = {
            "schema_version": 1,
            "mode": "server",
            "revision": "b" * 32,
            "base_url": "https://core.example.test",
            "response_bytes": 4194304,
        }
        for reference in (True, "../path", ""):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                decode_settings(base | {"credential_ref": reference})
        with self.assertRaises(ValueError):
            decode_settings(base)
        with self.assertRaises(ValueError):
            decode_settings(base | {"schema_version": 2, "credential_ref": None})
