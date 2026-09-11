"""Developer commands preserve explicit arguments and propagate their operation results."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class CommandTests(unittest.TestCase):
    def test_build_and_package_commands_resolve_paths_and_report_outputs(self):
        from runtime import build, package

        output = io.StringIO()
        with (
            patch("sys.argv", ["build", "--output", "new-runtime"]),
            patch.object(build, "build_runtime", return_value=Path("/candidate")) as operation,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(build.main(), 0)
            operation.assert_called_once_with(Path("new-runtime").resolve())
            self.assertEqual(output.getvalue().strip(), "/candidate")
        output = io.StringIO()
        with (
            patch("sys.argv", ["package", "--runtime", "runtime", "--output", "packages"]),
            patch.object(
                package, "package_clients", return_value={"codex": Path("/candidate/codex")}
            ) as operation,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(package.main(), 0)
            operation.assert_called_once_with(Path("runtime").resolve(), Path("packages").resolve())
            self.assertEqual(json.loads(output.getvalue()), {"codex": "/candidate/codex"})

    def test_prepare_command_passes_explicit_study_and_account(self):
        from measurement import prepare

        args = [
            "prepare",
            "--output",
            "evidence",
            "--plugin",
            "plugin",
            "--client",
            "client",
            "--model",
            "frozen-model",
            "--account-label",
            "review-account",
            "--study",
            "primary",
        ]
        with (
            patch("sys.argv", args),
            patch.object(prepare, "prepare", return_value=Path("manifest.json")) as operation,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(prepare.main(), 0)
            operation.assert_called_once_with(
                Path("evidence"),
                Path("plugin"),
                Path("client"),
                "frozen-model",
                "review-account",
                "primary",
            )
            self.assertEqual(output.getvalue().strip(), "manifest.json")

    def test_primary_preparation_records_absent_baseline_without_an_account(self):
        from measurement.prepare import prepare

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            plugin = root / "plugin"
            (plugin / "server").mkdir(parents=True)
            (plugin / "server/release.json").write_text("{}")
            (plugin / "skills/read-local-document").mkdir(parents=True)
            (plugin / "skills/read-local-document/SKILL.md").write_text("Read evidence.")
            client = root / "client"
            client.write_text("#!/bin/sh\necho '2.1.266 test'\n")
            client.chmod(0o755)
            with (
                patch("measurement.prepare.verify_release", return_value={"core_commit": "a" * 40}),
                patch("measurement.prepare.shutil.which", return_value=None),
                patch.dict("os.environ", {}, clear=True),
            ):
                manifest = prepare(root / "evidence", plugin, client, "model", "account", "primary")
            data = json.loads(manifest.read_text())
            self.assertEqual((data["max_trials"], len(data["task_ids"])), (108, 12))
            self.assertEqual(data["allowed_bash_commands"], [])
            environment = json.loads((manifest.parent / "environment.json").read_text())
            self.assertIsNone(environment["baseline"])
            self.assertIsNone(environment["account_key_sha256"])
