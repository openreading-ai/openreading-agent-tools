"""Settings previews never save or upload, and credentials stay outside widget results."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from runtime.destination_settings import read_destination, save_destination


class SettingsControllerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.destination_ui"),
            "Missing native settings interface",
        )
        from test_destination_settings import Keychain

        from runtime.destination_ui import Controller

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.keys = Keychain()
        self.controller = Controller("chatgpt", home=self.home, keychain=self.keys)

    def test_preview_preserves_settings_and_only_reuses_matching_credentials(self):
        saved = save_destination(
            "chatgpt",
            "server",
            base_url="http://localhost:8787",
            token="synthetic",
            home=self.home,
            keychain=self.keys,
        )
        check = AsyncMock(return_value={"version": "0.3.0", "backend_count": 1})
        with patch("runtime.destination_ui.check_connection", check):
            self.controller.check("http://localhost:8787", "", False)
            self.assertEqual(check.call_args.kwargs["token"], "synthetic")
            self.controller.check("https://different.invalid", "", False)
            self.assertIsNone(check.call_args.kwargs["token"])
            self.controller.check("http://localhost:8787", "", True)
            self.assertIsNone(check.call_args.kwargs["token"])
            self.controller.check("http://localhost:8787", "replacement", False)
            self.assertEqual(check.call_args.kwargs["token"], "replacement")
        self.assertEqual(read_destination("chatgpt", home=self.home), saved)
        self.assertEqual(len(self.keys.values), 1)

    def test_save_local_and_server_and_repair_invalid_settings(self):
        saved = self.controller.save("server", "http://localhost:8787", "synthetic", False)
        self.assertEqual(self.controller.current(), saved)
        self.assertIsNone(
            self.controller.save("server", "http://localhost:8787", "", True).credential_ref
        )
        next(self.home.rglob("destination.json")).write_text("broken")
        with self.assertRaises(ValueError):
            self.controller.current()
        self.assertEqual(self.controller.save("local", "", "", False).mode, "local")

    def test_save_local_ignores_server_response_limit(self):
        saved = self.controller.save("local", "", "", False, response_mib="")
        self.assertEqual(saved.mode, "local")

    def test_native_response_limit_can_be_lowered_and_rejects_invalid_values(self):
        saved = self.controller.save("server", "http://localhost", "", False, response_mib="4")
        self.assertEqual(saved.destination.response_bytes, 4 * 1024 * 1024)
        for value in ("0", "-1", "invalid", "1.5"):
            with self.assertRaises(ValueError):
                self.controller.save("server", "http://localhost", "", False, response_mib=value)
            self.assertEqual(self.controller.current(), saved)
