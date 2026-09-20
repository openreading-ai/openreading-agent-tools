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
            picker = module.Picker(
                root, Mock(), SimpleNamespace(StringVar=Widget), widgets, files, Mock()
            )
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

    def test_clear_confirmation_recovers_older_copies_and_keeps_artifacts(self):
        from runtime.selection import SelectionError, SelectionStore
        from runtime.selection_ui import Controller, Picker

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            pdf = home / "source.pdf"
            pdf.write_bytes(b"selected bytes")
            store = SelectionStore("claude-desktop", home=home)
            first, second = store.select(pdf), store.select(pdf)
            picker = object.__new__(Picker)
            picker.root = Mock()
            picker.messagebox = Mock()
            picker.controller = Controller(SelectionStore("claude-desktop", home=home))
            picker.status, picker.reference, picker.state = Mock(), Mock(), Mock()
            picker.messagebox.askyesno.return_value = False
            picker.clear()
            self.assertTrue((store.grant / first.reference).exists())
            picker.messagebox.askyesno.return_value = True
            picker.clear()
            self.assertFalse((store.grant / second.reference).exists())
            self.assertEqual(list(store.grant.iterdir()), [])
            self.assertTrue(pdf.exists())
            self.assertIn("2", picker.status.set.call_args.args[0])
            picker.controller.store.clear = Mock(side_effect=SelectionError("Cannot clear."))
            picker.clear()
            picker.status.set.assert_called_with("Cannot clear.")

    def test_real_background_copy_updates_controller_before_poll(self):
        from concurrent.futures import ThreadPoolExecutor

        from runtime.selection import SelectionStore
        from runtime.selection_ui import Controller, Picker

        with tempfile.TemporaryDirectory() as temporary, ThreadPoolExecutor(1) as executor:
            home = Path(temporary).resolve()
            pdf = home / "source.pdf"
            pdf.write_bytes(b"selected bytes")
            picker = object.__new__(Picker)
            picker.controller = Controller(SelectionStore("claude-desktop", home=home))
            picker.reference, picker.status, picker.state = Mock(), Mock(), Mock()
            picker.closing = False
            picker.future = executor.submit(picker.controller.choose, str(pdf))
            result = picker.future.result(timeout=2)
            picker.poll()
            self.assertIs(picker.controller.selection, result)
            picker.reference.set.assert_called_once_with(result.reference)
