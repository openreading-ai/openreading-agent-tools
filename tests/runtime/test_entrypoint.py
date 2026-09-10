"""The launcher checks integrity before dispatch and keeps client grants explicit."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.entrypoint import main
from runtime.verify import ReleaseIntegrityError


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("runtime.entrypoint.sys.platform", "darwin"))
        self.enterContext(patch("platform.machine", return_value="arm64"))
        self.enterContext(patch("runtime.entrypoint.sys.frozen", True, create=True))

    def test_bad_inventory_refuses_even_version_probe(self):
        with (
            patch(
                "runtime.entrypoint.verify_release",
                side_effect=ReleaseIntegrityError("invalid"),
            ),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(["--version"]), 2)

    def test_version_reports_metadata_without_starting_core(self):
        output = io.StringIO()
        with (
            patch(
                "runtime.entrypoint.verify_release",
                return_value={
                    "release_version": "0.1.0",
                    "core_commit": "a" * 40,
                    "worker_sha256": "b" * 64,
                },
            ),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(main(["--version"]), 0)
        self.assertIn('"core_commit": "' + "a" * 40, output.getvalue())

    def test_setup_and_launch_use_persisted_grant(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            grant = root / "documents"
            grant.mkdir()
            with (
                patch("runtime.entrypoint.verify_release", return_value={}),
                patch("pathlib.Path.home", return_value=root),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(main(["--client", "codex"]), 2)
                self.assertEqual(main(["--client", "codex", "--configure"]), 2)
                self.assertEqual(
                    main(["--client", "codex", "--configure", "--input-root", str(grant)]),
                    0,
                )
                with patch("openreading.mcp_server.main.main", return_value=0) as launch:
                    self.assertEqual(main(["--client", "codex"]), 0)
                    self.assertEqual(launch.call_args.args[0][3], str(grant))
                with patch("openreading.artifacts.worker.main", return_value=0) as worker:
                    self.assertEqual(
                        main(["--internal-artifact-worker", "--job-file", "job.json"]),
                        0,
                    )
                    self.assertEqual(worker.call_args.args[0], ["--job-file", "job.json"])

    def test_unsupported_host_refuses_before_inventory_or_document_access(self):
        for operating_system, machine in [("linux", "arm64"), ("darwin", "x86_64")]:
            with (
                self.subTest(os=operating_system, machine=machine),
                patch("runtime.entrypoint.sys.platform", operating_system),
                patch("platform.machine", return_value=machine),
                patch(
                    "runtime.entrypoint.verify_release",
                    return_value={
                        "release_version": "0.1.0",
                        "core_commit": "a" * 40,
                        "worker_sha256": "b" * 64,
                    },
                ) as verify,
                contextlib.redirect_stderr(io.StringIO()) as output,
            ):
                self.assertEqual(main(["--version"]), 2)
                verify.assert_not_called()
                self.assertIn("Apple Silicon", output.getvalue())

    def test_source_launch_reports_packaging_requirement(self):
        with (
            patch("runtime.entrypoint.sys.frozen", False, create=True),
            patch(
                "runtime.entrypoint.verify_release",
                return_value={
                    "release_version": "0.1.0",
                    "core_commit": "a" * 40,
                    "worker_sha256": "b" * 64,
                },
            ) as verify,
            contextlib.redirect_stderr(io.StringIO()) as output,
        ):
            self.assertEqual(main(["--version"]), 2)
            verify.assert_not_called()
            self.assertIn("packaged", output.getvalue())
