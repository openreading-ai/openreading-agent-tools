"""Current code-client packages bind local Docling and optional server mode to one runtime."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_desktop_package

from runtime import package
from runtime.verify import inventory, sha256, verify_release


class ServerClientPackageTests(unittest.TestCase):
    """Claude Code and Codex packages never relabel a legacy directory-grant runtime."""

    def fixture(self):
        owner = test_desktop_package.DesktopPackageTests()
        self.addCleanup(owner.doCleanups)
        source = owner.fixture()
        for name in (
            "_internal/runtime/selection.py",
            "_internal/runtime/chat_selection.py",
            "_internal/runtime/native_selection.py",
            "_internal/runtime/snapshot_selection.py",
            "_internal/openreading/mcp_server/selection_pages.py",
            "_internal/openreading/adapters/docling_local/formats.py",
            "_internal/openreading/adapters/docling_local/unpaginated.py",
            "_internal/openreading/schemas/passage.v0.4.json",
            "_internal/_tcl_data/init.tcl",
            "_internal/_tk_data/tk.tcl",
        ):
            path = source.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic resource")
        selection = source.root / "_internal/openreading/schemas/selection-tool.v0.2.json"
        selection.parent.mkdir(parents=True, exist_ok=True)
        selection.write_text(
            json.dumps({"$defs": {"SelectionPage": {}, "Request": {"properties": {"cursor": {}}}}})
        )
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        return source

    def test_current_code_packages_share_verified_docling_runtime(self):
        runtime = self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packages"
            paths = package.package_server_clients(runtime.root, output)
            self.assertEqual(set(paths), {"claude-code", "codex"})
            for client, target in paths.items():
                with self.subTest(client=client):
                    self.assertFalse((target / "historical").exists())
                    self.assertEqual(verify_release(target / "server"), runtime.metadata)
                    info = json.loads((target / "package-info.json").read_text())
                    self.assertEqual(info["core_commit"], runtime.metadata["core_commit"])
                    self.assertEqual(info["worker_sha256"], runtime.metadata["worker_sha256"])
                    self.assertEqual(
                        sha256(
                            target / "OpenReading Settings.app/Contents/MacOS/openreading-settings"
                        ),
                        info["settings_helper_sha256"],
                    )
                    if client == "claude-code":
                        manifest = json.loads((target / ".claude-plugin/plugin.json").read_text())
                        config = json.loads((target / ".mcp.json").read_text())
                    else:
                        manifest = json.loads((target / "plugin.json").read_text())
                        config = json.loads((target / "mcp.json").read_text())
                    self.assertEqual(manifest["name"], "openreading-local-documents")
                    self.assertEqual(
                        config["mcpServers"]["openreading"]["args"],
                        ["--client", client, "--chat-documents"],
                    )

    def test_server_client_packages_refuse_server_only_and_legacy_runtimes(self):
        for format_version, message in (("1", "Docling runtime"), ("3", "Docling runtime")):
            with (
                self.subTest(format_version=format_version),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                with patch(
                    "runtime.package.verify_release",
                    return_value={"format_version": format_version},
                ):
                    with self.assertRaisesRegex(ValueError, message):
                        package.package_server_clients(root / "runtime", root / "output")
                self.assertFalse((root / "output").exists())

    def test_server_client_packages_refuse_an_existing_output(self):
        runtime = self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            output.mkdir()
            with self.assertRaisesRegex(ValueError, "new package output"):
                package.package_server_clients(runtime.root, output)

    def test_cli_selects_current_code_client_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            result = {"claude-code": output / "claude-code", "codex": output / "codex"}
            stdout = io.StringIO()
            with (
                patch("runtime.package.package_server_clients", return_value=result) as operation,
                patch(
                    "sys.argv",
                    [
                        "package",
                        "--runtime",
                        "runtime",
                        "--output",
                        str(output),
                        "--server-clients",
                    ],
                ),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(package.main(), 0)
            operation.assert_called_once_with(Path("runtime").resolve(), output.resolve())
            self.assertEqual(
                json.loads(stdout.getvalue()), {name: str(path) for name, path in result.items()}
            )
