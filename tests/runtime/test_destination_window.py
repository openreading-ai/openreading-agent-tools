"""Native Settings owns UI work and keeps network checks off its event loop."""

import unittest
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock, patch

from runtime import destination_ui
from runtime.destination_settings import DestinationSettings


class Widget:
    def __init__(self, *args, **kwargs):
        self.value = kwargs.get("value", "")
        self.options = kwargs

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def add(self, *args, **kwargs):
        pass

    def pack(self, **kwargs):
        pass

    def configure(self, **kwargs):
        self.options.update(kwargs)


class WindowTests(unittest.TestCase):
    def make(self, broken=False):
        self.assertTrue(hasattr(destination_ui, "SettingsWindow"), "Missing settings window")
        controller = Mock()
        from pathlib import Path

        from runtime.app_settings import Preferences

        controller.home = Path("/synthetic")
        controller.preferences.return_value = Preferences(Path("/synthetic/.openreading"))
        controller.current.return_value = DestinationSettings()
        if broken:
            controller.current.side_effect = ValueError("Invalid destination settings")
        widgets = SimpleNamespace(
            **{
                name: Widget
                for name in (
                    "Notebook",
                    "Frame",
                    "Label",
                    "Entry",
                    "Button",
                    "Radiobutton",
                    "Checkbutton",
                )
            }
        )
        tk = SimpleNamespace(StringVar=Widget, BooleanVar=Widget)
        with patch.object(destination_ui, "ThreadPoolExecutor") as pool:
            window = destination_ui.SettingsWindow(Mock(), controller, tk, widgets)
        return window, controller, pool.return_value

    def test_saves_explicit_choice_and_clears_token_widget(self):
        window, controller, executor = self.make()
        window.mode.set("server")
        window.url.set("http://localhost:8787")
        window.token.set("synthetic")
        window.save()
        controller.save.assert_called_once_with(
            "server", "http://localhost:8787", "synthetic", False, response_mib="128"
        )
        self.assertEqual(window.token.get(), "")
        self.assertIn("Saved", window.status.get())
        controller.save.side_effect = ValueError("Invalid server URL")
        window.save()
        self.assertEqual(window.status.get(), "Invalid server URL")
        controller.save.side_effect = OSError("sensitive diagnostic")
        window.save()
        self.assertNotIn("sensitive", window.status.get())

    def test_network_check_disables_save_until_completion_and_close_waits(self):
        window, controller, executor = self.make()
        future = Future()
        executor.submit.return_value = future
        window.check()
        self.assertEqual(window.save_button.options["state"], "disabled")
        window.close()
        window.root.destroy.assert_not_called()
        future.set_result({"version": "0.3.0", "backend_count": 1})
        window.poll()
        self.assertIn("No document", window.status.get())
        window.root.destroy.assert_called_once()
        executor.shutdown.assert_called_once_with(wait=False)

    def test_check_errors_are_sanitized_and_broken_settings_can_open(self):
        window, controller, executor = self.make(broken=True)
        self.assertIn("Invalid", window.status.get())
        for error in (
            ValueError("No connection"),
            RuntimeError("sensitive diagnostic"),
        ):
            future = Future()
            future.set_exception(error)
            executor.submit.return_value = future
            window.check()
            self.assertNotIn("sensitive", window.status.get())
            self.assertEqual(window.save_button.options["state"], "normal")

    def test_run_owns_window(self):
        self.assertTrue(hasattr(destination_ui, "run"), "Missing Settings entry point")
        with (
            patch("tkinter.Tk") as root,
            patch.object(destination_ui, "SettingsWindow") as window,
        ):
            self.assertEqual(destination_ui.run("chatgpt"), 0)
            self.assertEqual(window.call_args.args[1].client, "chatgpt")
            root.return_value.mainloop.assert_called_once()

    def test_folder_choice_cancel_save_and_discard(self):
        window, controller, _ = self.make()
        original = window.folder.get()
        with patch("tkinter.filedialog.askdirectory", return_value=""):
            window.choose_folder()
        self.assertEqual(window.folder.get(), original)
        with patch("tkinter.filedialog.askdirectory", return_value="/synthetic/chosen"):
            window.choose_folder()
        self.assertEqual(window.folder.get(), "/synthetic/chosen")
        controller.save_preferences.assert_not_called()
        window.save_preferences()
        controller.save_preferences.assert_called_once_with("/synthetic/chosen", "1000000")
        window.discard_preferences()
        self.assertEqual(window.folder.get(), original)
        self.assertIn("discarded", window.preference_status.get())
        for error in (ValueError("invalid folder"), OSError("private failure")):
            controller.save_preferences.side_effect = error
            window.save_preferences()
            self.assertNotIn("private failure", window.preference_status.get())
        controller.preferences.side_effect = ValueError("bad saved preferences")
        window.discard_preferences()
        self.assertEqual(window.preference_status.get(), "bad saved preferences")

    def test_discard_destination_restores_local_and_server_values_without_saving(self):
        from runtime.server_transport import ServerDestination

        window, controller, _ = self.make()
        window.url.set("https://changed.invalid")
        window.token.set("not saved")
        window.discard_destination()
        self.assertEqual(window.mode.get(), "local")
        self.assertEqual(window.token.get(), "")
        controller.current.return_value = DestinationSettings(
            "server", "r", ServerDestination("http://localhost:8787", "r", 4194304)
        )
        window.discard_destination()
        self.assertEqual(window.url.get(), "http://localhost:8787")
        self.assertEqual(window.response_mib.get(), "4")
        controller.save.assert_not_called()
        controller.current.side_effect = ValueError("broken settings")
        window.discard_destination()
        self.assertEqual(window.status.get(), "broken settings")
