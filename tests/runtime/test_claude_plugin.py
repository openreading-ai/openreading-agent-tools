"""Claude plugin archives preserve the reviewed extension without installing it."""

import contextlib
import importlib
import io
import json
import shutil
import stat
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import test_chatgpt_package

from runtime import package
from runtime.verify import sha256, verify_release


class ClaudePluginTests(unittest.TestCase):
    def fixture(self):
        owner = test_chatgpt_package.ChatGPTPackageTests()
        self.addCleanup(owner.doCleanups)
        runtime = owner.fixture()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        extension = package.package_docling_desktop(runtime.root, root / "extension", chat=True)
        helper = extension / "OpenReading Settings.app/Contents/MacOS/openreading-settings"
        helper.parent.mkdir(parents=True)
        helper.write_text("#!/bin/sh\nexit 0\n")
        helper.chmod(0o755)
        plist = helper.parent.parent / "Info.plist"
        plist.write_text("synthetic settings plist")
        info_path = extension / "package-info.json"
        info = json.loads(info_path.read_text())
        info.update(helper_sha256=sha256(helper), helper_info_sha256=sha256(plist))
        info_path.write_text(json.dumps(info))
        return extension, root / "output"

    def module(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.claude_plugin"),
            "Cowork plugin archive builder is missing",
        )
        return importlib.import_module("runtime.claude_plugin")

    def test_archive_preserves_runtime_and_launches_without_developer_paths(self):
        extension, output = self.fixture()
        archive = self.module().build(extension, output)
        target = output / "plugin"
        manifest = json.loads((target / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "openreading-local-documents")
        config = json.loads((target / manifest["mcpServers"]).read_text())
        server = config["mcpServers"]["openreading"]
        self.assertEqual(server["command"], "${CLAUDE_PLUGIN_ROOT}/server/openreading-worker")
        self.assertEqual(server["args"], ["--client", "claude-desktop", "--chat-documents"])
        skill = target / manifest["skills"] / "read-local-document/SKILL.md"
        self.assertEqual(
            skill.read_bytes(),
            (package.REPOSITORY / "skills/read-local-document/SKILL.md").read_bytes(),
        )
        self.assertEqual(verify_release(target / "server"), verify_release(extension / "server"))
        with zipfile.ZipFile(archive) as packed:
            self.assertIsNone(packed.testzip())
            self.assertIn(".claude-plugin/plugin.json", packed.namelist())
            self.assertNotIn("manifest.json", packed.namelist())
            for name in packed.namelist():
                self.assertFalse(name.startswith("/"))
                self.assertNotIn("..", Path(name).parts)
                self.assertEqual(packed.read(name), (target / name).read_bytes())
            for name in [
                "server/openreading-worker",
                "OpenReading Settings.app/Contents/MacOS/openreading-settings",
            ]:
                mode = packed.getinfo(name).external_attr >> 16
                self.assertTrue(stat.S_ISREG(mode))
                self.assertEqual(mode & 0o777, 0o755)
        receipt = json.loads((output / "candidate.json").read_text())
        self.assertEqual(receipt["archive_sha256"], sha256(archive))
        self.assertEqual(receipt["worker_sha256"], sha256(target / "server/openreading-worker"))
        moved = output.parent / "relocated café"
        shutil.move(target, moved)
        resolved = server["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(moved))
        self.assertTrue(Path(resolved).is_file())
        self.assertEqual(verify_release(moved / "server"), verify_release(extension / "server"))

    def test_stale_extension_workflow_does_not_replace_current_shared_skill(self):
        extension, output = self.fixture()
        workflow = extension / "WORKFLOW.md"
        workflow.write_text("Historical workflow from the frozen extension.\n")
        info_path = extension / "package-info.json"
        info = json.loads(info_path.read_text())
        info["workflow_sha256"] = sha256(workflow)
        info_path.write_text(json.dumps(info))
        source_version = json.loads((extension / "manifest.json").read_text())["version"]
        archive = self.module().build(extension, output)
        current = package.REPOSITORY / "skills/read-local-document/SKILL.md"
        name = "skills/read-local-document/SKILL.md"
        with zipfile.ZipFile(archive) as packed:
            self.assertEqual(packed.read(name), current.read_bytes())
            manifest = json.loads(packed.read(".claude-plugin/plugin.json"))
            self.assertNotEqual(manifest["version"], source_version)
        receipt = json.loads((output / "candidate.json").read_text())
        self.assertEqual(receipt["package_files"][name], sha256(current))
        self.assertEqual(receipt["source_package_info_sha256"], sha256(info_path))
        self.assertEqual(workflow.read_text(), "Historical workflow from the frozen extension.\n")

    def test_changed_inputs_and_existing_output_refuse_without_overwrite(self):
        module = self.module()
        for name in [
            "manifest.json",
            "WORKFLOW.md",
            "server/openreading-worker",
            "OpenReading Settings.app/Contents/MacOS/openreading-settings",
            "OpenReading Settings.app/Contents/Info.plist",
        ]:
            with self.subTest(name=name):
                extension, output = self.fixture()
                path = extension / name
                path.write_bytes(path.read_bytes() + b"changed")
                with self.assertRaises(ValueError):
                    module.build(extension, output)
                self.assertFalse(output.exists())
        extension, output = self.fixture()
        output.mkdir()
        marker = output / "keep"
        marker.write_text("preserve")
        with self.assertRaisesRegex(ValueError, "new output"):
            module.build(extension, output)
        self.assertEqual(marker.read_text(), "preserve")

    def test_refuses_symlinks_non_chat_manifest_and_nonexecutable_helper(self):
        module = self.module()
        for fault in ("symlink", "manifest", "helper"):
            with self.subTest(fault=fault):
                extension, output = self.fixture()
                if fault == "symlink":
                    (extension / "link").symlink_to("WORKFLOW.md")
                elif fault == "manifest":
                    manifest_path = extension / "manifest.json"
                    manifest = json.loads(manifest_path.read_text())
                    manifest["server"]["mcp_config"]["args"] = []
                    manifest_path.write_text(json.dumps(manifest))
                    info_path = extension / "package-info.json"
                    info = json.loads(info_path.read_text())
                    info["manifest_sha256"] = sha256(manifest_path)
                    info_path.write_text(json.dumps(info))
                else:
                    (
                        extension / "OpenReading Settings.app/Contents/MacOS/openreading-settings"
                    ).chmod(0o644)
                with self.assertRaises(ValueError):
                    module.build(extension, output)
                self.assertFalse(output.exists())

    def test_size_limit_refuses_archive_instead_of_delivering_uninstallable_file(self):
        module = self.module()
        extension, output = self.fixture()
        with patch.object(module, "MAX_ARCHIVE_BYTES", 1, create=True):
            with self.assertRaisesRegex(ValueError, "200 MB"):
                module.build(extension, output)
        self.assertFalse((output / "openreading-claude-cowork.zip").exists())

    def test_expanded_limit_refuses_archive_even_when_compressed_size_fits(self):
        module = self.module()
        extension, output = self.fixture()
        with patch.object(module, "MAX_EXPANDED_BYTES", 1, create=True):
            with self.assertRaisesRegex(ValueError, "uncompressed"):
                module.build(extension, output)
        self.assertFalse((output / "openreading-claude-cowork.zip").exists())

    def test_download_package_is_small_and_preserves_both_destinations_runtime(self):
        module = self.module()
        extension, output = self.fixture()
        archive = module.build(extension, output, runtime_base_url="https://example.invalid/v1")
        target = output / "plugin"
        config = json.loads((target / ".mcp.json").read_text())
        server = config["mcpServers"]["openreading"]
        self.assertEqual(
            server,
            {"command": "/bin/sh", "args": ["${CLAUDE_PLUGIN_ROOT}/launch.sh", "--chat-documents"]},
        )
        with zipfile.ZipFile(archive) as zipped:
            self.assertFalse(any(name.startswith("server/") for name in zipped.namelist()))
            self.assertFalse(any(name.endswith(".tar.gz") for name in zipped.namelist()))
            self.assertLess(sum(item.file_size for item in zipped.infolist()), 100_000)
            self.assertIn("launch.sh", zipped.namelist())
        self.assertIn("--destination-settings", (target / module.HELPER).read_text())
        receipt = json.loads((output / "candidate.json").read_text())
        download = receipt["runtime_download"]
        payload = output / "runtime" / download["url"].rsplit("/", 1)[1]
        self.assertEqual(download["sha256"], sha256(payload))
        self.assertEqual(download["length"], payload.stat().st_size)
        self.assertFalse((target / "server").exists())
        restored = output.parent / "restored"
        with tarfile.open(payload) as packed:
            packed.extractall(restored, filter="data")
        self.assertEqual(verify_release(restored), verify_release(extension / "server"))
        # Neither settings nor destination selection is rewritten by packaging.
        self.assertEqual(receipt["core_commit"], verify_release(restored)["core_commit"])
        self.assertIn("Optional Core server", (target / ".claude-plugin/plugin.json").read_text())
        again = output.parent / "again"
        module.build(extension, again, runtime_base_url="https://example.invalid/v1")
        second = json.loads((again / "candidate.json").read_text())["runtime_download"]
        self.assertEqual(download, second)

    def test_download_url_refuses_credentials_http_and_ambiguous_paths(self):
        module = self.module()
        for url in (
            "http://example.com",
            "https://user:secret@example.com",
            "https://example.com?a=1",
            "https://example.com/#x",
            "https:///missing",
            "https://example.com/../x",
            "https://example.com/line\n",
        ):
            with self.subTest(url=url):
                extension, output = self.fixture()
                with self.assertRaisesRegex(ValueError, "HTTPS"):
                    module.build(extension, output, runtime_base_url=url)
                self.assertFalse(output.exists())

    def test_cli_and_incompatible_identity(self):
        module = self.module()
        extension, output = self.fixture()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(
                module.main(
                    [
                        "--extension",
                        str(extension),
                        "--output",
                        str(output),
                        "--runtime-base-url",
                        "https://example.invalid/assets",
                    ]
                ),
                0,
            )
        self.assertTrue(Path(stdout.getvalue().strip()).is_file())
        extension, output = self.fixture()
        p = extension / "package-info.json"
        info = json.loads(p.read_text())
        info["core_commit"] = "0" * 40
        p.write_text(json.dumps(info))
        with self.assertRaisesRegex(ValueError, "identity"):
            module.build(extension, output)
        with patch.object(module, "verify_release", return_value={"format_version": "1"}):
            with self.assertRaisesRegex(ValueError, "Docling"):
                module.build(extension, output)
