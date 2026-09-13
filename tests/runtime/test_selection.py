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
        with self.assertRaises(m.SelectionError):
            store.clear()
        extra.unlink()
        target = store.grant / result.reference
        target.unlink()
        target.symlink_to(self.source)
        with self.assertRaises(m.SelectionError):
            store.remove(result.reference)
        with self.assertRaises(m.SelectionError):
            store.select(self.source)
        with self.assertRaises(m.SelectionError):
            store.clear()
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

    def test_full_store_can_be_cleared_from_a_new_session(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        with patch.object(m, "MAX_SELECTION_BYTES", self.source.stat().st_size * 2):
            store.select(self.source)
            store.select(self.source)
            reopened = m.SelectionStore("claude-desktop", home=self.root / "home")
            with self.assertRaisesRegex(m.SelectionError, "storage is full"):
                reopened.select(self.source)
            artifact = store.root.parent / "artifacts/keep"
            artifact.parent.mkdir()
            artifact.write_bytes(b"retained evidence")
            self.assertEqual(reopened.clear(), 2)
            self.assertEqual(artifact.read_bytes(), b"retained evidence")
            self.assertEqual(self.source.read_bytes(), b"%PDF-1.4\nsynthetic\n")
            self.assertTrue((store.grant / reopened.select(self.source).reference).exists())

    def test_abandoned_staging_is_reclaimed_only_by_a_publisher(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        with store.locked():
            abandoned = store.staging / ("a" * 32)
            abandoned.mkdir()
            (abandoned / "unfinished.pdf").write_bytes(b"x" * 100)
            with self.assertRaisesRegex(m.SelectionError, "in progress"):
                store.select(self.source)
            self.assertTrue(abandoned.exists())
        with patch.object(m, "MAX_SELECTION_BYTES", self.source.stat().st_size):
            result = store.select(self.source)
        self.assertFalse(abandoned.exists())
        self.assertTrue((store.grant / result.reference).exists())

    def test_recovery_does_not_follow_links_or_delete_unexpected_ready_data(self):
        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        store.prepare()
        abandoned = store.staging / ("a" * 32)
        abandoned.mkdir()
        (abandoned / "link").symlink_to(self.source)
        store.clear()
        self.assertTrue(self.source.exists())
        alien = store.grant / "unexpected"
        alien.mkdir()
        (alien / "leave.pdf").write_bytes(b"unrecognized")
        with self.assertRaises(m.SelectionError):
            store.clear()
        self.assertTrue((alien / "leave.pdf").exists())

    def test_symlink_refusal_explains_that_links_are_unsupported(self):
        m = self.module()
        folder = self.root / "linked-folder"
        folder.symlink_to(self.root, target_is_directory=True)
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        with self.assertRaisesRegex(m.SelectionError, "[Ss]ymlink"):
            store.select(folder / self.source.name)

    def test_force_killed_publisher_leaves_recoverable_staging(self):
        import queue
        import subprocess
        import sys
        from threading import Thread
        from unittest.mock import patch

        m = self.module()
        home = self.root / "home"
        script = """
import signal,sys
from pathlib import Path
from runtime.selection import SelectionStore
store=SelectionStore('claude-desktop',home=Path(sys.argv[1]))
with store.locked():
 entry=store.staging/('a'*32)
 entry.mkdir()
 (entry/'unfinished.pdf').write_bytes(b'x'*100)
 print('copying',flush=True)
 signal.pause()
"""
        with subprocess.Popen(
            [sys.executable, "-c", script, str(home)], stdout=subprocess.PIPE, text=True
        ) as child:
            output = queue.Queue()
            reader = Thread(target=lambda: output.put(child.stdout.readline()), daemon=True)
            reader.start()
            try:
                self.assertEqual(output.get(timeout=5).strip(), "copying")
            finally:
                child.kill()
                child.wait(timeout=5)
                reader.join(1)
        store = m.SelectionStore("claude-desktop", home=home)
        self.assertTrue(list(store.staging.iterdir()))
        with patch.object(m, "MAX_SELECTION_BYTES", self.source.stat().st_size):
            result = store.select(self.source)
        self.assertEqual(list(store.staging.iterdir()), [])
        self.assertTrue((store.grant / result.reference).exists())

    def test_staging_recovery_refuses_unknown_names_and_linked_entries(self):
        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        store.prepare()
        for name in ("unknown", "a" * 32):
            entry = store.staging / name
            entry.symlink_to(self.root, target_is_directory=True)
            with self.assertRaises(m.SelectionError):
                store.clear()
            self.assertTrue(self.source.exists())
            entry.unlink()

    def test_rollback_revokes_before_failed_deletion_and_next_publisher_sweeps(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        selected = store.select(self.source)
        size = self.source.stat().st_size
        with patch.object(m.shutil, "rmtree", side_effect=OSError("disk failure")):
            with self.assertRaises(m.SelectionError):
                store.rollback(selected.reference)
        self.assertFalse((store.grant / selected.reference).exists())
        self.assertEqual(store.used_bytes(), size)
        with patch.object(m, "MAX_SELECTION_BYTES", size):
            fresh = store.select(self.source)
        self.assertEqual(list(store.discarded.iterdir()), [])
        self.assertTrue((store.grant / fresh.reference).exists())
        store.rollback(fresh.reference)
        store.rollback(fresh.reference)
        self.assertEqual(store.used_bytes(), 0)

    def test_rollback_refuses_corruption_and_preserves_unrelated_copies(self):
        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        selected = store.select(self.source)
        for reference in ("../outside.pdf", "invalid"):
            with self.assertRaises(m.SelectionError):
                store.rollback(reference)
        selected_path = store.grant / selected.reference
        extra = selected_path.parent / "other.pdf"
        extra.write_bytes(b"keep")
        with self.assertRaises(m.SelectionError):
            store.rollback(selected.reference)
        self.assertTrue(extra.exists())
        extra.unlink()
        selected_path.unlink()
        selected_path.symlink_to(self.source)
        with self.assertRaises(m.SelectionError):
            store.rollback(selected.reference)
        self.assertTrue(self.source.exists())

    def test_concurrent_revoked_sweep_tolerates_already_removed_entries(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        store.prepare()
        with store.directories() as (_, _, staging):
            with patch.object(m.os, "listdir", return_value=["a" * 32]):
                store.sweep(staging)

    def test_rollback_between_listing_and_open_does_not_break_select_or_clear(self):
        from unittest.mock import patch

        m = self.module()
        for operation in ("select", "clear"):
            with self.subTest(operation=operation):
                store = m.SelectionStore("claude-desktop", home=self.root / operation)
                rollback = store.select(self.source)
                keep = store.select(self.source)
                target = rollback.reference.split("/")[0]
                original = m.os.open
                injected = False

                def opening(
                    path,
                    flags,
                    *args,
                    target=target,
                    store=store,
                    rollback=rollback,
                    original=original,
                    **kwargs,
                ):
                    nonlocal injected
                    if path == target and flags & os.O_DIRECTORY and not injected:
                        injected = True
                        store.rollback(rollback.reference)
                    return original(path, flags, *args, **kwargs)

                with patch.object(m.os, "open", side_effect=opening):
                    if operation == "select":
                        fresh = store.select(self.source)
                        self.assertTrue((store.grant / fresh.reference).exists())
                        self.assertTrue((store.grant / keep.reference).exists())
                    else:
                        self.assertEqual(store.clear(), 1)
                        self.assertEqual(list(store.grant.iterdir()), [])
                self.assertTrue(injected)
                self.assertFalse((store.grant / rollback.reference).exists())

    def test_clear_tolerates_rollback_after_validation_before_delete(self):
        from unittest.mock import patch

        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        rollback = store.select(self.source)
        keep = store.select(self.source)
        target = rollback.reference.split("/")[0]
        original = m.shutil.rmtree
        injected = False

        def deleting(path, *args, **kwargs):
            nonlocal injected
            if path == target and not injected:
                injected = True
                store.rollback(rollback.reference)
            return original(path, *args, **kwargs)

        with patch.object(m.shutil, "rmtree", side_effect=deleting):
            self.assertEqual(store.clear(), 1)
        self.assertTrue(injected)
        self.assertFalse((store.grant / keep.reference).exists())

    def test_quota_scan_skips_removed_file_and_never_counts_a_moved_copy_twice(self):
        from unittest.mock import patch

        m = self.module()
        for timing in ("before_stat", "after_stat"):
            with self.subTest(timing=timing):
                store = m.SelectionStore("claude-desktop", home=self.root / timing)
                rollback = store.select(self.source)
                keep = store.select(self.source)
                inode = (store.grant / rollback.reference).parent.stat().st_ino
                original = m.os.stat
                injected = False

                def statting(
                    path,
                    *args,
                    inode=inode,
                    timing=timing,
                    store=store,
                    rollback=rollback,
                    original=original,
                    **kwargs,
                ):
                    nonlocal injected
                    fd = kwargs.get("dir_fd")
                    if (
                        fd is not None
                        and path == self.source.name
                        and os.fstat(fd).st_ino == inode
                        and not injected
                    ):
                        injected = True
                        if timing == "after_stat":
                            info = original(path, *args, **kwargs)
                            with patch.object(
                                m.shutil, "rmtree", side_effect=OSError("disk failure")
                            ):
                                with self.assertRaises(m.SelectionError):
                                    store.rollback(rollback.reference)
                            return info
                        store.rollback(rollback.reference)
                    return original(path, *args, **kwargs)

                with patch.object(m.os, "stat", side_effect=statting):
                    self.assertEqual(
                        store.used_bytes(),
                        self.source.stat().st_size * (2 if timing == "after_stat" else 1),
                    )
                self.assertTrue(injected)
                self.assertTrue((store.grant / keep.reference).exists())

    def test_rollback_fails_closed_when_the_entry_directory_is_replaced_by_a_link(self):
        m = self.module()
        store = m.SelectionStore("claude-desktop", home=self.root / "home")
        selected = store.select(self.source)
        entry = (store.grant / selected.reference).parent
        moved = self.root / "original-copy"
        entry.rename(moved)
        entry.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(m.SelectionError, "Cannot revoke"):
            store.rollback(selected.reference)
        for operation in (store.clear, lambda: store.select(self.source)):
            with self.assertRaises(m.SelectionError):
                operation()
        self.assertTrue((moved / self.source.name).exists())

    def test_clear_tolerates_revocation_after_open_before_listing_or_stat(self):
        from unittest.mock import patch

        m = self.module()
        for timing in ("before_list", "after_list"):
            with self.subTest(timing=timing):
                store = m.SelectionStore("claude-desktop", home=self.root / timing)
                rollback = store.select(self.source)
                keep = store.select(self.source)
                inode = (store.grant / rollback.reference).parent.stat().st_ino
                original = m.os.listdir
                injected = False

                def listing(
                    path,
                    *,
                    inode=inode,
                    timing=timing,
                    store=store,
                    rollback=rollback,
                    original=original,
                ):
                    nonlocal injected
                    if isinstance(path, int) and os.fstat(path).st_ino == inode and not injected:
                        injected = True
                        if timing == "after_list":
                            names = original(path)
                            store.rollback(rollback.reference)
                            return names
                        store.rollback(rollback.reference)
                    return original(path)

                with patch.object(m.os, "listdir", side_effect=listing):
                    self.assertEqual(store.clear(), 1)
                self.assertTrue(injected)
                self.assertFalse((store.grant / keep.reference).exists())
