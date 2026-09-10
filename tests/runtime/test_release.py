"""A release refuses changed, missing, escaping, and unlisted runtime files."""

import json
import tempfile
import unittest
from pathlib import Path

from runtime.verify import ReleaseIntegrityError, inventory, verify_release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "openreading-worker").write_bytes(b"test executable")
        (self.root / "openreading-worker").chmod(0o755)
        (self.root / "library.dylib").write_bytes(b"native library")
        self.metadata = {
            "format_version": "1",
            "release_version": "0.1.0-alpha.1",
            "os": "darwin",
            "arch": "arm64",
            "minimum_os_version": "15.1",
            "core_commit": "a" * 40,
            "core_version": "0.3.0",
            "python_version": "3.11.15",
            "dependency_lock_sha256": "b" * 64,
            "files": inventory(self.root),
            "licenses": ["THIRD_PARTY_NOTICES.txt"],
        }
        (self.root / "THIRD_PARTY_NOTICES.txt").write_text("Synthetic test notice")
        self.metadata["files"] = inventory(self.root)
        self.metadata["worker_sha256"] = self.metadata["files"]["openreading-worker"]["sha256"]
        self.write_metadata()

    def write_metadata(self):
        (self.root / "release.json").write_text(json.dumps(self.metadata))

    def test_intact_release_passes(self):
        self.assertEqual(verify_release(self.root)["core_commit"], "a" * 40)

    def test_changed_worker_fails(self):
        (self.root / "openreading-worker").write_bytes(b"changed")
        with self.assertRaises(ReleaseIntegrityError):
            verify_release(self.root)

    def test_unlisted_library_and_missing_notice_fail(self):
        extra = self.root / "injected.dylib"
        extra.write_bytes(b"not inventoried")
        with self.assertRaises(ReleaseIntegrityError):
            verify_release(self.root)
        extra.unlink()
        (self.root / "THIRD_PARTY_NOTICES.txt").unlink()
        with self.assertRaises(ReleaseIntegrityError):
            verify_release(self.root)

    def test_escaping_inventory_and_inconsistent_worker_hash_fail(self):
        self.metadata["files"]["../secret"] = self.metadata["files"]["library.dylib"]
        self.write_metadata()
        with self.assertRaises(ReleaseIntegrityError):
            verify_release(self.root)
        del self.metadata["files"]["../secret"]
        self.metadata["worker_sha256"] = "0" * 64
        self.write_metadata()
        with self.assertRaises(ReleaseIntegrityError):
            verify_release(self.root)

    def test_external_symlink_is_refused(self):
        (self.root / "escape").symlink_to(self.root.parent)
        with self.assertRaises(ReleaseIntegrityError):
            inventory(self.root)

    def test_packaging_materializes_internal_library_links_before_hashing(self):
        from runtime.build import materialize_links

        (self.root / "alias.dylib").symlink_to("library.dylib")
        materialize_links(self.root)
        self.assertFalse((self.root / "alias.dylib").is_symlink())
        self.assertEqual((self.root / "alias.dylib").read_bytes(), b"native library")
        self.assertEqual(inventory(self.root)["alias.dylib"], inventory(self.root)["library.dylib"])
