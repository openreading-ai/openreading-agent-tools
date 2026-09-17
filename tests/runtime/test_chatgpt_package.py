"""Plugin packaging preserves executable identity and relocatable chat launch metadata."""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_desktop_package
import test_release

from runtime import package
from runtime.verify import inventory, sha256, verify_release


class ChatGPTPackageTests(unittest.TestCase):
    def fixture(self):
        owner = test_desktop_package.DesktopPackageTests()
        self.addCleanup(owner.doCleanups)
        source = owner.fixture()
        for name in (
            "_internal/runtime/selection.py",
            "_internal/runtime/chat_selection.py",
            "_internal/_tcl_data/init.tcl",
            "_internal/_tk_data/tk.tcl",
        ):
            path = source.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic chooser resource")
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        return source

    def operation(self):
        self.assertTrue(
            hasattr(package, "package_chatgpt_plugin"), "ChatGPT plugin assembler missing"
        )
        return package.package_chatgpt_plugin

    def test_relocated_marketplace_resolves_worker_skill_and_bound_metadata(self):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "built"
            target = self.operation()(source.root, output)
            relative = target.relative_to(output)
            moved = Path(temp) / "installed café space"
            shutil.move(output, moved)
            target = moved / relative
            catalog = json.loads((moved / ".agents/plugins/marketplace.json").read_text())
            entry = catalog["plugins"][0]
            self.assertEqual((moved / entry["source"]["path"]).resolve(), target.resolve())
            manifest = json.loads((target / ".codex-plugin/plugin.json").read_text())
            self.assertEqual(manifest["name"], entry["name"])
            config = json.loads((target / manifest["mcpServers"]).read_text())
            server = config["mcpServers"]["openreading"]
            command = Path(server["command"].replace("${PLUGIN_ROOT}", str(target)))
            self.assertEqual(command, target / "server/openreading-worker")
            self.assertTrue(command.stat().st_mode & 0o111)
            self.assertEqual(server["args"], ["--client", "chatgpt", "--chat-documents"])
            self.assertEqual(set(server), {"command", "args"})
            skill = target / manifest["skills"] / "read-local-document/SKILL.md"
            self.assertEqual(
                skill.read_bytes(),
                (package.REPOSITORY / "skills/read-local-document/SKILL.md").read_bytes(),
            )
            self.assertEqual(verify_release(target / "server"), source.metadata)
            info = json.loads((target / "package-info.json").read_text())
            self.assertEqual(info["distribution"], "development-only")
            self.assertEqual(info["core_commit"], source.metadata["core_commit"])
            self.assertEqual(info["worker_sha256"], sha256(command))
            for name, digest in info["package_files"].items():
                self.assertEqual(sha256(target / name), digest)
            self.assertEqual(
                set(info["package_files"]),
                {
                    ".codex-plugin/plugin.json",
                    ".mcp.json",
                    "README.md",
                    "skills/read-local-document/SKILL.md",
                },
            )

    def test_refuses_existing_destination_and_incompatible_runtime_before_writing(self):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            output.mkdir()
            marker = output / "keep"
            marker.write_text("untouched")
            with self.assertRaisesRegex(ValueError, "new package output"):
                self.operation()(source.root, output)
            self.assertEqual(marker.read_text(), "untouched")
            old = test_release.ReleaseTests()
            old.setUp()
            self.addCleanup(old.doCleanups)
            with self.assertRaisesRegex(ValueError, "Docling runtime"):
                self.operation()(old.root, Path(temp) / "old")
            self.assertFalse((Path(temp) / "old").exists())

    def test_missing_snapshot_contract_refuses_before_copying(self):
        source = self.fixture()
        (source.root / "_internal/runtime/snapshot_selection.py").unlink()
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            with self.assertRaisesRegex(ValueError, "snapshot selection"):
                self.operation()(source.root, output)
            self.assertFalse(output.exists())

    def test_cli_selects_only_chatgpt_plugin(self):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            stdout = io.StringIO()
            with (
                patch(
                    "sys.argv",
                    [
                        "package",
                        "--runtime",
                        str(source.root),
                        "--output",
                        str(output),
                        "--chatgpt-plugin",
                    ],
                ),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(package.main(), 0)
            target = Path(json.loads(stdout.getvalue())["chatgpt"])
            self.assertTrue((target / ".codex-plugin/plugin.json").is_file())
            self.assertFalse((output / "claude-desktop").exists())

    def test_cli_refuses_conflicting_targets(self):
        for flags in (
            ["--chatgpt-plugin", "--docling-desktop"],
            ["--chatgpt-plugin", "--chat-documents"],
        ):
            with (
                self.subTest(flags=flags),
                patch("sys.argv", ["package", "--runtime", ".", "--output", "unused", *flags]),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as result,
            ):
                package.main()
            self.assertEqual(result.exception.code, 2)
