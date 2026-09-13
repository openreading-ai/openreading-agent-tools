"""Selected-file handoff publishes only complete explicitly chosen document copies."""

import importlib
import os
import tempfile
import unittest
from pathlib import Path


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "Résumé ' $(echo nope).pdf"
        self.source.write_bytes(b"%PDF-1.4\nsynthetic\n")

    def module(self):
        return importlib.import_module("runtime.selection")

    def test_selected_copy_preserves_bytes_and_name_without_granting_source_parent(self):
        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        result = store.select(self.source)
        self.assertRegex(result.reference, r"^[0-9a-f]{32}/")
        selected = store.grant / result.reference
        self.assertEqual(selected.read_bytes(), self.source.read_bytes())
        self.assertEqual(selected.name, self.source.name)
        self.assertNotIn(str(self.source.parent), result.prompt)
        self.assertNotIn(str(store.grant), result.prompt)
        self.assertEqual(os.stat(selected).st_mode & 0o777, 0o600)
        self.assertEqual(os.stat(store.grant).st_mode & 0o777, 0o700)
        self.assertEqual(list(store.staging.iterdir()), [])
        second = store.select(self.source)
        self.assertNotEqual(result.reference, second.reference)
        self.assertEqual(
            m.SelectionStore("claude-desktop", home=self.root / "home").grant, store.grant
        )
        store.remove(result.reference)
        self.assertFalse(selected.exists())
        self.assertTrue((store.grant / second.reference).exists())

    def test_unselected_paths_symlinks_and_nonregular_files_are_refused(self):
        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        link = self.root / "link.pdf"
        link.symlink_to(self.source)
        folder = self.root / "linked"
        folder.symlink_to(self.root, target_is_directory=True)
        fifo = self.root / "fifo.pdf"
        os.mkfifo(fifo)
        for path in (
            link,
            folder / self.source.name,
            fifo,
            self.root,
            self.root / "missing.pdf",
            Path("relative.pdf"),
        ):
            with self.subTest(path=path), self.assertRaises(m.SelectionError):
                store.select(path)
        for reference in (
            "../outside.pdf",
            str(self.source),
            "a/../x.pdf",
            "x",
            "a" * 32 + "/missing.pdf",
        ):
            with self.subTest(reference=reference), self.assertRaises(m.SelectionError):
                store.remove(reference)
        self.assertEqual(self.source.read_bytes(), b"%PDF-1.4\nsynthetic\n")

    def test_caps_cancellation_and_write_failure_never_publish_partial_copies(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        for keyword, value in (("MAX_FILE_BYTES", 4), ("MAX_SELECTION_BYTES", 4)):
            with patch.object(m, keyword, value), self.assertRaises(m.SelectionError):
                store.select(self.source)
        for size in (0,):
            empty = self.root / "empty.pdf"
            empty.write_bytes(b"" * size)
            with self.assertRaises(m.SelectionError):
                store.select(empty)
        checks = []

        def cancelled():
            checks.append(1)
            return len(checks) > 2

        with self.assertRaisesRegex(m.SelectionError, "cancelled"):
            store.select(self.source, cancelled=cancelled)
        with (
            patch.object(m.os, "fsync", side_effect=OSError("secret disk path")),
            self.assertRaises(m.SelectionError) as error,
        ):
            store.select(self.source)
        self.assertNotIn("secret", str(error.exception))
        self.assertEqual(list(store.grant.iterdir()), [])
        self.assertEqual(list(store.staging.iterdir()), [])

    def test_source_edits_refuse_but_path_replacement_copies_opened_bytes(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        original = m.os.read
        changed = False

        def mutate(fd, size):
            nonlocal changed
            if not changed:
                changed = True
                self.source.write_bytes(b"changed document")
            return original(fd, size)

        with (
            patch.object(m.os, "read", side_effect=mutate),
            self.assertRaisesRegex(m.SelectionError, "changed"),
        ):
            store.select(self.source)
        old_bytes = self.source.read_bytes()

        def replace(fd, size):
            if self.source.read_bytes() == old_bytes:
                other = self.root / "other.pdf"
                other.write_bytes(b"replacement")
                other.replace(self.source)
            return original(fd, size)

        # Replacing a pathname changes the opened inode's ctime on some filesystems.
        # Refusal is safe; accepting must still copy the descriptor's original bytes.
        with patch.object(m.os, "read", side_effect=replace):
            try:
                result = store.select(self.source)
            except m.SelectionError:
                result = None
        if result is not None:
            self.assertEqual((store.grant / result.reference).read_bytes(), old_bytes)
        self.assertEqual(list(store.staging.iterdir()), [])

    def test_concurrent_publishers_are_busy_and_private_symlinks_refuse(self):
        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        with store.locked(), self.assertRaisesRegex(m.SelectionError, "in progress"):
            store.select(self.source)
        store.grant.rmdir()
        store.grant.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(m.SelectionError):
            store.select(self.source)
        self.assertEqual(list(store.staging.iterdir()), [])

    def test_private_corruption_and_reference_collision_fail_closed(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        result = store.select(self.source)
        entry = store.grant / result.reference.split("/")[0]
        with (
            patch.object(m.secrets, "token_hex", return_value=entry.name),
            self.assertRaises(m.SelectionError),
        ):
            store.select(self.source)
        extra = entry / "unexpected.pdf"
        extra.write_bytes(b"extra")
        with self.assertRaises(m.SelectionError):
            store.remove(result.reference)
        extra.unlink()
        target = store.grant / result.reference
        target.unlink()
        target.symlink_to(self.source)
        with self.assertRaises(m.SelectionError):
            store.remove(result.reference)
        with self.assertRaises(m.SelectionError):
            store.select(self.source)
        self.assertTrue(self.source.exists())

    def test_growing_source_hits_streaming_limit_before_publication(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        read = m.os.read
        initial = self.source.stat().st_size
        changed = False

        def grow(fd, size):
            nonlocal changed
            if not changed:
                changed = True
                with self.source.open("ab") as stream:
                    stream.write(b"extra")
            return read(fd, size)

        with (
            patch.object(m, "MAX_FILE_BYTES", initial),
            patch.object(m.os, "read", side_effect=grow),
            self.assertRaisesRegex(m.SelectionError, "while being copied"),
        ):
            store.select(self.source)
        self.assertEqual(list(store.grant.iterdir()), [])
        self.assertEqual(list(store.staging.iterdir()), [])
