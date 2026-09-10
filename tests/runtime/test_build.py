"""The build pins engine metadata and validates the assembled output before returning it."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.build import build_runtime, locked_identity, notices
from runtime.verify import verify_release


class BuildTests(unittest.TestCase):
    def test_freezer_output_is_inventoried_and_never_overwritten(self):
        def freezer(command, **kwargs):
            destination = Path(command[command.index("--distpath") + 1]) / "openreading-worker"
            destination.mkdir(parents=True)
            (destination / "openreading-worker").write_bytes(b"synthetic executable")
            (destination / "openreading-worker").chmod(0o755)

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "runtime"
            with (
                patch("runtime.build.sys.platform", "darwin"),
                patch("runtime.build.platform.machine", return_value="arm64"),
                patch("runtime.build.platform.mac_ver", return_value=("15.1", "", "")),
                patch("runtime.build.platform.python_version", return_value="3.11.15"),
                patch("runtime.build.subprocess.run", side_effect=freezer),
            ):
                result = build_runtime(output)
                metadata = verify_release(result)
                self.assertEqual(metadata["core_commit"], locked_identity()["core_commit"])
                self.assertIn("pymupdf", (output / "THIRD_PARTY_NOTICES.txt").read_text().lower())
                with self.assertRaises(ValueError):
                    build_runtime(output)

    def test_wrong_platform_is_refused_before_build(self):
        with (
            patch("runtime.build.sys.platform", "linux"),
            self.assertRaises(ValueError),
        ):
            build_runtime(Path("/nonexistent/output"))

    def test_notices_identify_the_native_backend(self):
        self.assertIn("pymupdf", notices().lower())

    def test_installed_engine_revision_must_match_the_lock(self):
        with patch("runtime.build.importlib.metadata.distribution") as distribution:
            distribution.return_value.read_text.return_value = '{"vcs_info":{"commit_id":"wrong"}}'
            with self.assertRaises(ValueError):
                locked_identity()
