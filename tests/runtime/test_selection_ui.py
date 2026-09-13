"""Picker actions keep cancellation, references and explicit clipboard writes separate."""

import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock


class SelectionControllerTests(unittest.TestCase):
    def test_cancel_success_copy_and_remove(self):
        module = importlib.import_module("runtime.selection_ui")
        from runtime.selection import SelectionStore

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            pdf = home / "source.pdf"
            pdf.write_bytes(b"synthetic")
            controller = module.Controller(SelectionStore("claude-desktop", home=home))
            self.assertIsNone(controller.choose(""))
            self.assertIsNone(controller.selection)
            result = controller.choose(str(pdf))
            self.assertIs(controller.selection, result)
            clipboard = Mock()
            controller.copy(clipboard)
            clipboard.assert_called_once_with(result.prompt)
            controller.remove()
            self.assertIsNone(controller.selection)
            with self.assertRaises(ValueError):
                controller.copy(clipboard)
            controller.remove()

    def test_failed_replacement_preserves_previous_reference(self):
        module = importlib.import_module("runtime.selection_ui")
        from runtime.selection import SelectionError

        store = Mock()
        store.select.return_value = object()
        controller = module.Controller(store)
        previous = controller.choose("/chosen.pdf")
        store.select.side_effect = SelectionError("refused")
        with self.assertRaises(SelectionError):
            controller.choose("/another.pdf")
        self.assertIs(controller.selection, previous)

    def test_picker_buttons_async_completion_errors_and_close(self):
        from concurrent.futures import Future
        from types import SimpleNamespace
        from unittest.mock import patch

        module = importlib.import_module("runtime.selection_ui")
        from runtime.selection import Selection, SelectionError

        class Widget:
            def __init__(self, *args, **kwargs):
                self.options = kwargs
                self.value = kwargs.get("value", "")

            def pack(self, **kwargs):
                pass

            def configure(self, **kwargs):
                self.options.update(kwargs)

            def set(self, value):
                self.value = value

        widgets = SimpleNamespace(Frame=Widget, Label=Widget, Entry=Widget, Button=Widget)
        root = Mock()
        files = Mock()
        executor = Mock()
        with patch.object(module, "ThreadPoolExecutor", return_value=executor):
            picker = module.Picker(root, Mock(), SimpleNamespace(StringVar=Widget), widgets, files)
        files.askopenfilename.return_value = ""
        picker.choose()
        executor.submit.assert_not_called()
        for failure in (None, SelectionError("Selection refused."), RuntimeError("planted secret")):
            future = Future()
            files.askopenfilename.return_value = "/chosen.pdf"
            executor.submit.return_value = future
            picker.choose()
            root.after.assert_called_with(50, picker.poll)
            self.assertEqual(picker.choose_button.options["state"], "disabled")
            if failure is None:
                result = Selection("a" * 32 + "/chosen.pdf", "b" * 64, 12)
                picker.controller.selection = result
                future.set_result(result)
            else:
                future.set_exception(failure)
            picker.poll()
            self.assertNotIn("planted secret", picker.status.value)
            self.assertEqual(picker.choose_button.options["state"], "normal")
        picker.copy()
        root.clipboard_append.assert_called_once_with(result.prompt)
        picker.controller.store.remove.side_effect = SelectionError("Cannot remove.")
        picker.remove()
        self.assertEqual(picker.status.value, "Cannot remove.")
        picker.controller.store.remove.side_effect = None
        picker.remove()
        self.assertEqual(picker.reference.value, "")
        future = Future()
        picker.future = future
        picker.close()
        self.assertTrue(picker.cancelled.is_set())
        root.destroy.assert_not_called()
        future.set_exception(SelectionError("Selection cancelled."))
        picker.poll()
        root.destroy.assert_called_once()
        executor.shutdown.assert_called_once_with(wait=False)

    def test_gui_entrypoint_owns_its_event_loop(self):
        from unittest.mock import patch

        module = importlib.import_module("runtime.selection_ui")
        with patch("tkinter.Tk") as root, patch.object(module, "Picker") as picker:
            store = Mock()
            self.assertEqual(module.run(store), 0)
            self.assertIs(picker.call_args.args[1], store)
            root.return_value.mainloop.assert_called_once()
