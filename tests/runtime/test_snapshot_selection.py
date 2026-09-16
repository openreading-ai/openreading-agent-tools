"""Folder snapshots copy only selected eligible regular files and revoke failed handoffs."""

import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.selection import SelectionStore


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.folder = self.root / "selected"
        self.folder.mkdir()
        self.store = SelectionStore("claude-desktop", home=self.root / "home")
        self.store.prepare()
        if __import__("sys").platform != "darwin":
            stub = patch("runtime.snapshot_selection.is_package", return_value=False)
            stub.start()
            self.addCleanup(stub.stop)

    def module(self):
        return importlib.import_module("runtime.snapshot_selection")

    def test_recursive_snapshot_skips_links_hidden_packages_and_deduplicates(self):
        (self.folder / "one.pdf").write_bytes(b"%PDF-one")
        nested = self.folder / "nested"
        nested.mkdir()
        (nested / "one.pdf").write_bytes(b"%PDF-two")
        (self.folder / ".hidden.pdf").write_bytes(b"%PDF-hidden")
        (self.folder / "notes.txt").write_text("not a document")
        (self.folder / "link.pdf").symlink_to(nested / "one.pdf")
        package = self.folder / "Test.app"
        package.mkdir()
        (package / "secret.pdf").write_bytes(b"%PDF-package")
        m = self.module()
        with patch.object(m, "is_package", side_effect=lambda p: p.suffix == ".app"):
            result = m.snapshot(self.store, [self.folder, self.folder / "one.pdf"])
        self.assertEqual(len(result["references"]), 2)
        self.assertEqual(
            result["skipped"],
            {"hidden": 1, "unsupported": 1, "symlink": 1, "package": 1, "duplicate": 1},
        )
        contents = {(self.store.grant / r).read_bytes() for r in result["references"]}
        self.assertEqual(contents, {b"%PDF-one", b"%PDF-two"})
        (nested / "one.pdf").write_bytes(b"changed later")
        self.assertEqual(
            {(self.store.grant / r).read_bytes() for r in result["references"]}, contents
        )
        self.assertTrue(all("nested" not in r for r in result["references"]))

    def test_copy_failure_revokes_only_this_snapshot(self):
        for name in ["a.pdf", "b.pdf"]:
            (self.folder / name).write_bytes(b"%PDF-file")
        previous = self.store.select(self.folder / "a.pdf")
        select = self.store.select
        calls = []

        def failing(path, **kwargs):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("private path failure")
            return select(path, **kwargs)

        with patch.object(self.store, "select", failing), self.assertRaises(OSError):
            self.module().snapshot(self.store, [self.folder])
        self.assertEqual(
            [p.name for p in self.store.grant.iterdir()], [previous.reference.split("/")[0]]
        )

    def test_cancelled_walk_publishes_nothing(self):
        (self.folder / "a.pdf").write_bytes(b"%PDF-file")
        with self.assertRaises(ValueError):
            self.module().snapshot(self.store, [self.folder], cancelled=lambda: True)
        self.assertEqual(list(self.store.grant.iterdir()), [])

    def test_special_files_and_replaced_source_are_refused_without_following(self):
        import os

        os.mkfifo(self.folder / "pipe.pdf")
        m = self.module()
        result = m.snapshot(self.store, [self.folder / "pipe.pdf"])
        self.assertEqual(result["skipped"], {"special": 1})
        source = self.folder / "a.pdf"
        source.write_bytes(b"%PDF-before")
        select = self.store.select

        def replacing(path, **kwargs):
            replacement = path.with_name("replacement.pdf")
            replacement.write_bytes(b"%PDF-after")
            replacement.replace(path)
            return select(path, **kwargs)

        with patch.object(self.store, "select", replacing), self.assertRaises(ValueError):
            m.snapshot(self.store, [source])
        self.assertEqual(list(self.store.grant.iterdir()), [])

    def test_changed_enumeration_and_unreadable_folder_do_not_publish(self):
        import os

        m = self.module()
        original = os.listdir

        def changed(fd):
            names = original(fd)
            if isinstance(fd, int) and os.fstat(fd).st_ino == self.folder.stat().st_ino:
                (self.folder / "new.pdf").write_bytes(b"%PDF-new")
            return names

        with (
            patch.object(m, "is_package", return_value=False),
            patch.object(m.os, "listdir", changed),
            self.assertRaises(ValueError),
        ):
            m.snapshot(self.store, [self.folder])
        with (
            patch.object(m, "is_package", side_effect=PermissionError("private path")),
            self.assertRaises(PermissionError),
        ):
            m.snapshot(self.store, [self.folder])
        self.assertEqual(list(self.store.grant.iterdir()), [])

    def test_native_package_property_and_empty_folder(self):
        import sys

        if sys.platform != "darwin":
            self.skipTest("macOS package metadata API")
        m = self.module()
        self.assertFalse(m.is_package(self.folder))
        package = self.folder / "Application.app"
        package.mkdir()
        self.assertTrue(m.is_package(package))
        self.assertEqual(m.snapshot(self.store, [self.folder])["skipped"], {"package": 1})

    def test_snapshot_checks_existing_intake_once(self):
        for i in range(20):
            (self.folder / f"{i}.pdf").write_bytes(b"%PDF-file")
        with patch.object(self.store, "used_bytes", wraps=self.store.used_bytes) as checks:
            result = self.module().snapshot(self.store, [self.folder])
        self.assertEqual(len(result["references"]), 20)
        self.assertEqual(checks.call_count, 1)
