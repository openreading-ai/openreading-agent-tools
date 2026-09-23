"""Settings previews never save or upload, and connections require only a URL."""

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
        from runtime.destination_ui import Controller

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.controller = Controller("chatgpt", home=self.home)

    def test_preview_preserves_settings_and_only_passes_the_url(self):
        saved = save_destination(
            "chatgpt", "server", base_url="http://localhost:8787", home=self.home
        )
        check = AsyncMock(return_value={"version": "0.3.0", "backend_count": 1})
        with patch("runtime.destination_ui.check_connection", check):
            self.controller.check("http://localhost:8787")
            self.assertEqual(check.call_args.args[0].base_url, "http://localhost:8787")
            self.assertEqual(check.call_args.kwargs, {})
            self.controller.check("https://different.invalid")
            self.assertEqual(check.call_args.args[0].base_url, "https://different.invalid")
        self.assertEqual(read_destination("chatgpt", home=self.home), saved)

    def test_save_local_and_server_and_repair_invalid_settings(self):
        saved = self.controller.save("server", "http://localhost:8787")
        self.assertEqual(self.controller.current(), saved)
        next(self.home.rglob("destination.json")).write_text("broken")
        with self.assertRaises(ValueError):
            self.controller.current()
        self.assertEqual(self.controller.save("local", "").mode, "local")

    def test_native_response_limit_can_be_lowered_and_rejects_invalid_values(self):
        saved = self.controller.save("server", "http://localhost", response_mib="4")
        self.assertEqual(saved.destination.response_bytes, 4 * 1024 * 1024)
        for value in ("0", "-1", "invalid", "1.5"):
            with self.assertRaises(ValueError):
                self.controller.save("server", "http://localhost", response_mib=value)
            self.assertEqual(self.controller.current(), saved)

    def test_storage_and_delivery_are_saved_without_changing_processing(self):
        self.assertTrue(
            hasattr(self.controller, "preferences"),
            "Missing native preferences controls",
        )
        folder = self.home / "Downloads/Chosen"
        self.controller.save_preferences(str(folder), "8192")
        self.assertEqual(self.controller.preferences().data_folder, folder)
        self.assertEqual(self.controller.preferences().document_response_bytes, 8192)
        self.assertEqual(self.controller.current().mode, "local")
        with self.assertRaises(ValueError):
            self.controller.save_preferences(str(folder), "3.5")

    def test_reopened_controller_reports_saved_and_applied_storage_choice(self):
        from runtime.configuration import client_root
        from runtime.destination_ui import Controller
        from runtime.storage_settings import storage_session

        legacy = client_root("chatgpt", home=self.home) / "v2"
        legacy.mkdir(parents=True)
        self.assertEqual(self.controller.storage_choices()["application"], legacy.parent.parent)
        self.assertEqual(self.controller.storage_view()["folder"], legacy.parent.parent)
        self.controller.save_storage(str(self.home / ".openreading"))
        reopened = Controller("chatgpt", home=self.home)
        self.assertEqual(reopened.storage_view()["state"], "pending")
        with storage_session("chatgpt", home=self.home):
            self.assertEqual(reopened.storage_view()["state"], "active")
        self.assertEqual(reopened.storage_view()["folder"], self.home / ".openreading")

    def test_tab_saves_preserve_other_tabs_and_advanced_survives_local_mode(self):
        from runtime.configuration import client_root

        self.assertTrue(hasattr(self.controller, "save_advanced"))
        self.controller.save_advanced("8192", "256")
        self.assertFalse((client_root("chatgpt", home=self.home) / "preferences.json").exists())
        self.assertEqual(self.controller.limits().server_response_bytes, 256 * 1024 * 1024)
        self.controller.save_storage(str(self.home / "chosen"))
        self.assertEqual(self.controller.limits().document_response_bytes, 8192)
        self.controller.save("server", "http://localhost:8787")
        saved = self.controller.current()
        self.assertEqual(saved.destination.response_bytes, 256 * 1024 * 1024)
        self.controller.save_advanced("16384", "512")
        self.assertEqual(self.controller.current(), saved)
        self.assertEqual(self.controller.preferences().data_folder, self.home / "chosen")
        for budget, maximum in [("bad", "256"), ("8192", "0"), ("4095", "256")]:
            with self.assertRaises(ValueError):
                self.controller.save_advanced(budget, maximum)
        self.assertEqual(self.controller.limits().server_response_bytes, 512 * 1024 * 1024)
