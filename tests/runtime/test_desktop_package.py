"""Desktop candidates preserve verified Docling resources and explicit setup semantics."""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_release

from runtime import package
from runtime.verify import ReleaseIntegrityError, inventory, sha256, verify_release


class DesktopPackageTests(unittest.TestCase):
    def fixture(self):
        release = test_release.ReleaseTests()
        release.setUp()
        self.addCleanup(release.doCleanups)
        for name in [
            "_internal/openreading/mcp_server/selection.py",
            "_internal/openreading/mcp_server/selection_pages.py",
            "_internal/openreading/adapters/docling_local/formats.py",
            "_internal/openreading/adapters/docling_local/unpaginated.py",
            "_internal/openreading/schemas/passage.v0.4.json",
            "_internal/runtime/server_profile.py",
            "_internal/runtime/server_imports.py",
            "_internal/runtime/server_selection.py",
            "_internal/runtime/server_transport.py",
            "_internal/runtime/server_keychain.py",
            "_internal/runtime/destination_settings.py",
            "_internal/runtime/destination_ui.py",
            "_internal/openreading/artifacts/retention.py",
            "_internal/openreading/schemas/local-document.v0.5.json",
            "_internal/openreading/schemas/agent-document-tool.v0.5.json",
            "_internal/openreading/schemas/import-job.v0.4.json",
            "_internal/runtime/native_selection.py",
            "_internal/runtime/snapshot_selection.py",
            "_internal/openreading/artifacts/document.py",
            "_internal/openreading/artifacts/delivery.py",
            "_internal/openreading/mcp_server/delivery.py",
            "_internal/openreading/artifacts/jobs.py",
            "resources/docling-runtime.uv.lock",
            "resources/models/docling-project--docling-layout-heron-onnx/model.onnx",
            "resources/tessdata/eng.traineddata",
            "resources/tessdata/osd.traineddata",
            "resources/tessdata/configs/tsv",
            "resources/tesseract/bin/tesseract",
        ]:
            path = release.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic identity input")
        (release.root / name).chmod(0o755)
        schema = release.root / "_internal/openreading/schemas/import-job.v0.3.json"
        schema.parent.mkdir(parents=True, exist_ok=True)
        schema.write_text(json.dumps({"$defs": {"ListRequest": {}, "PageProgress": {}}}))
        (schema.parent / "document-tool.v0.4.json").write_text(
            json.dumps(
                {
                    "$defs": {
                        "TextOriginCounts": {},
                        "DeliveryRequest": {
                            "properties": {"delivery": {"enum": ["fragments", "auto", "file"]}}
                        },
                    }
                }
            )
        )
        (schema.parent / "selection-tool.v0.2.json").write_text(
            json.dumps(
                {
                    "$defs": {
                        "SelectionPage": {},
                        "Request": {"properties": {"cursor": {}}},
                    }
                }
            )
        )
        release.metadata.update(
            format_version="2",
            profile="local-document-proof-v2",
            distribution="development-only",
            dependency_lock_sha256=sha256(release.root / "resources/docling-runtime.uv.lock"),
            files=inventory(release.root),
        )
        release.write_metadata()
        return release

    def operation(self):
        self.assertTrue(hasattr(package, "package_docling_desktop"))
        return package.package_docling_desktop

    def test_candidate_preserves_runtime_and_limits_configuration_to_grant_and_ocr(
        self,
    ):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "candidate"
            target = self.operation()(source.root, destination)
            self.assertEqual(target, destination)
            self.assertEqual(verify_release(target / "server"), source.metadata)
            manifest = json.loads((target / "manifest.json").read_text())
            self.assertNotEqual(manifest["name"], "openreading-local-proof")
            self.assertEqual(set(manifest["user_config"]), {"input_root", "ocr"})
            self.assertTrue(manifest["user_config"]["input_root"]["required"])
            self.assertEqual(manifest["user_config"]["ocr"]["type"], "boolean")
            self.assertIs(manifest["user_config"]["ocr"]["default"], False)
            self.assertNotIn("default", manifest["user_config"]["input_root"])
            self.assertEqual(
                manifest["server"]["mcp_config"]["args"],
                [
                    "--client",
                    "claude-desktop",
                    "--input-root",
                    "${user_config.input_root}",
                    "--ocr",
                    "${user_config.ocr}",
                ],
            )
            record = json.loads((target / "package-info.json").read_text())
            self.assertEqual(record["core_commit"], source.metadata["core_commit"])
            self.assertEqual(record["worker_sha256"], sha256(target / "server/openreading-worker"))
            self.assertEqual(record["manifest_sha256"], sha256(target / "manifest.json"))
            self.assertEqual(record["workflow_sha256"], sha256(target / "WORKFLOW.md"))
            self.assertEqual(record["distribution"], "development-only")
            self.assertIn("openreading_get_document", [tool["name"] for tool in manifest["tools"]])
            self.assertIn("openreading_list_imports", [tool["name"] for tool in manifest["tools"]])
            self.assertIn("openreading_get_document", (target / "WORKFLOW.md").read_text())
            with self.assertRaises(ValueError):
                self.operation()(source.root, target)

    def test_full_document_manifest_refuses_an_older_runtime(self):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "candidate"
            (source.root / "_internal/openreading/artifacts/document.py").unlink()
            source.metadata["files"] = inventory(source.root)
            source.write_metadata()
            with self.assertRaisesRegex(ValueError, "full normalized"):
                self.operation()(source.root, target)
            self.assertFalse(target.exists())

    def test_background_manifest_refuses_runtime_without_job_dispatch(self):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "candidate"
            (source.root / "_internal/openreading/artifacts/jobs.py").unlink()
            source.metadata["files"] = inventory(source.root)
            source.write_metadata()
            with self.assertRaisesRegex(ValueError, "background import"):
                self.operation()(source.root, target)
            self.assertFalse(target.exists())

    def test_job_listing_manifest_refuses_older_or_invalid_contract(self):
        for contents in (None, b"{}", b"[]", b"invalid", b'{"$defs":[]}'):
            with self.subTest(contents=contents):
                source = self.fixture()
                schema = source.root / "_internal/openreading/schemas/import-job.v0.3.json"
                if contents is None:
                    schema.unlink()
                else:
                    schema.write_bytes(contents)
                source.metadata["files"] = inventory(source.root)
                source.write_metadata()
                with tempfile.TemporaryDirectory() as temp:
                    target = Path(temp) / "candidate"
                    with self.assertRaisesRegex(ValueError, "job discovery"):
                        self.operation()(source.root, target)
                    self.assertFalse(target.exists())

    def test_historical_invalid_and_tampered_candidates_create_no_output(self):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "candidate"
            source.metadata.pop("profile")
            source.metadata.pop("distribution")
            source.metadata["format_version"] = "1"
            source.write_metadata()
            with self.assertRaisesRegex(ValueError, "Docling"):
                self.operation()(source.root, destination)
            self.assertFalse(destination.exists())
            (source.root / "openreading-worker").write_bytes(b"changed")
            with self.assertRaises(ReleaseIntegrityError):
                self.operation()(source.root, destination)
            self.assertFalse(destination.exists())

    def test_cli_selects_docling_candidate_explicitly(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch(
                "sys.argv",
                [
                    "package",
                    "--runtime",
                    str(self.fixture().root),
                    "--output",
                    temp + "/candidate",
                    "--docling-desktop",
                ],
            ),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(package.main(), 0)
            paths = json.loads(output.getvalue())
            self.assertEqual(set(paths), {"claude-desktop"})
            self.assertTrue((Path(paths["claude-desktop"]) / "manifest.json").is_file())

    def test_selection_package_requires_picker_runtime_and_has_no_directory_setting(
        self,
    ):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "selection"
            with self.assertRaises(ValueError):
                package.package_docling_desktop(source.root, target, selection=True)
            self.assertFalse(target.exists())
            for name in (
                "_internal/runtime/selection.py",
                "_internal/_tcl_data/init.tcl",
                "_internal/_tk_data/tk.tcl",
            ):
                path = source.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic picker resource")
            source.metadata["files"] = inventory(source.root)
            source.write_metadata()
            package.package_docling_desktop(source.root, target, selection=True)
            manifest = json.loads((target / "manifest.json").read_text())
            self.assertEqual(set(manifest["user_config"]), {"ocr"})
            self.assertEqual(
                manifest["server"]["mcp_config"]["args"],
                [
                    "--client",
                    "claude-desktop",
                    "--selected-documents",
                    "--ocr",
                    "${user_config.ocr}",
                ],
            )
            self.assertEqual(manifest["name"], "openreading-file-selection-preview")
            resolved = subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "-e",
                    """
import {getMcpConfigForManifest} from '@anthropic-ai/mcpb';
let text=''; for await (const chunk of process.stdin) text+=chunk;
const manifest=JSON.parse(text), results=[];
for (const ocr of [false,true]) results.push(await getMcpConfigForManifest({
 manifest, extensionPath:"/installed/Unicode 界 space ' $(echo forbidden) ; *",
 systemDirs:{}, userConfig:{ocr}, pathSeparator:"/"}));
console.log(JSON.stringify(results));
""",
                ],
                input=json.dumps(manifest),
                text=True,
                capture_output=True,
                check=True,
                cwd=package.REPOSITORY,
            )
            for enabled, config in zip((False, True), json.loads(resolved.stdout), strict=True):
                self.assertEqual(
                    config["args"],
                    [
                        "--client",
                        "claude-desktop",
                        "--selected-documents",
                        "--ocr",
                        str(enabled).lower(),
                    ],
                )
                self.assertEqual(
                    config["command"],
                    "/installed/Unicode 界 space ' $(echo forbidden) ; */server/openreading-worker",
                )

            self.assertIn("Choose", (target / "README.md").read_text())
            helper = target / "OpenReading Choose Document.app/Contents/MacOS/openreading-select"
            self.assertTrue(helper.stat().st_mode & 0o111)
            self.assertIn("--select-document", helper.read_text())
            info = json.loads((target / "package-info.json").read_text())
            self.assertEqual(info["helper_sha256"], sha256(helper))

    def test_selection_cli_requires_explicit_docling_package_mode(self):
        with (
            patch(
                "sys.argv",
                ["package", "--runtime", "r", "--output", "o", "--selected-documents"],
            ),
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as error,
        ):
            package.main()
        self.assertEqual(error.exception.code, 2)

    def test_chat_package_requires_provider_and_only_optional_delivery_setting(self):
        source = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "chat"
            with self.assertRaises(ValueError):
                package.package_docling_desktop(source.root, target, chat=True)
            self.assertFalse(target.exists())
            for name in (
                "_internal/runtime/selection.py",
                "_internal/runtime/chat_selection.py",
                "_internal/openreading/mcp_server/selection.py",
                "_internal/_tcl_data/init.tcl",
                "_internal/_tk_data/tk.tcl",
            ):
                path = source.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic provider resource")
            source.metadata["files"] = inventory(source.root)
            source.write_metadata()
            package.package_docling_desktop(source.root, target, chat=True)
            manifest = json.loads((target / "manifest.json").read_text())
            self.assertEqual(set(manifest["user_config"]), {"document_response_bytes"})
            self.assertEqual(manifest["user_config"]["document_response_bytes"]["default"], 1000000)
            self.assertFalse(manifest["user_config"]["document_response_bytes"]["required"])
            self.assertEqual(manifest["user_config"]["document_response_bytes"]["min"], 4096)
            self.assertEqual(
                manifest["server"]["mcp_config"]["args"],
                [
                    "--client",
                    "claude-desktop",
                    "--chat-documents",
                    "--document-response-bytes",
                    "${user_config.document_response_bytes}",
                ],
            )
            self.assertEqual(manifest["name"], "openreading-chat-selection-preview")
            self.assertIn("configured adapter", manifest["long_description"])
            self.assertNotIn("choose a local PDF", manifest["long_description"])
            self.assertIn(
                "openreading_select_document",
                [tool["name"] for tool in manifest["tools"]],
            )
            self.assertEqual(verify_release(target / "server"), source.metadata)
            self.assertFalse((target / "OpenReading Choose Document.app").exists())
            self.assertIn("Cancel", (target / "README.md").read_text())
            self.assertNotIn("Copy reference", (target / "README.md").read_text())
            with self.assertRaises(ValueError):
                package.package_docling_desktop(
                    source.root, Path(temp) / "both", chat=True, selection=True
                )

    def test_chat_cli_requires_docling_and_cannot_combine_selection_modes(self):
        for options in (
            ["--chat-documents"],
            ["--chat-documents", "--selected-documents", "--docling-desktop"],
        ):
            with (
                patch("sys.argv", ["package", "--runtime", "r", "--output", "o", *options]),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                package.main()

    def test_current_manifest_cannot_package_an_older_three_tool_runtime(self):
        source = self.fixture()
        path = source.root / "_internal/openreading/mcp_server/selection.py"
        path.unlink(missing_ok=True)
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "old-core"
            with self.assertRaisesRegex(ValueError, "selection contract"):
                package.package_docling_desktop(source.root, target)
            self.assertFalse(target.exists())

    def test_candidate_refuses_missing_complete_delivery_contract_before_output(self):
        source = self.fixture()
        (source.root / "_internal/openreading/schemas/document-tool.v0.4.json").unlink()
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            with self.assertRaisesRegex(ValueError, "complete delivery"):
                package.package_docling_desktop(source.root, output)
            self.assertFalse(output.exists())

    def test_candidate_refuses_each_missing_delivery_module(self):
        for module in ("artifacts", "mcp_server"):
            with self.subTest(module=module):
                source = self.fixture()
                (source.root / f"_internal/openreading/{module}/delivery.py").unlink()
                source.metadata["files"] = inventory(source.root)
                source.write_metadata()
                with tempfile.TemporaryDirectory() as temp:
                    output = Path(temp) / "candidate"
                    with self.assertRaisesRegex(ValueError, "complete delivery"):
                        package.package_docling_desktop(source.root, output)
                    self.assertFalse(output.exists())

    def test_candidate_refuses_wrong_delivery_enum(self):
        source = self.fixture()
        path = source.root / "_internal/openreading/schemas/document-tool.v0.4.json"
        schema = json.loads(path.read_text())
        schema["$defs"]["DeliveryRequest"]["properties"]["delivery"]["enum"] = ["fragments"]
        path.write_text(json.dumps(schema))
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            with self.assertRaisesRegex(ValueError, "complete delivery"):
                package.package_docling_desktop(source.root, output)
            self.assertFalse(output.exists())

    def test_candidate_refuses_delivery_without_origin_metadata(self):
        source = self.fixture()
        for name in ("document-tool.v0.2.json", "document-tool.v0.4.json"):
            path = source.root / "_internal/openreading/schemas" / name
            if path.exists():
                schema = json.loads(path.read_text())
                schema["$defs"].pop("TextOriginCounts", None)
                path.write_text(json.dumps(schema))
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            with self.assertRaisesRegex(ValueError, "complete delivery"):
                package.package_docling_desktop(source.root, output)
            self.assertFalse(output.exists())

    def test_candidate_refuses_jobs_without_page_progress(self):
        source = self.fixture()
        for name in ("import-job.v0.1.json", "import-job.v0.3.json"):
            path = source.root / "_internal/openreading/schemas" / name
            if path.exists():
                schema = json.loads(path.read_text())
                schema["$defs"].pop("PageProgress", None)
                path.write_text(json.dumps(schema))
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            with self.assertRaisesRegex(ValueError, "job discovery"):
                package.package_docling_desktop(source.root, output)
            self.assertFalse(output.exists())

    def test_chat_candidate_refuses_missing_snapshot_schema(self):
        source = self.fixture()
        path = source.root / "_internal/openreading/schemas/selection-tool.v0.2.json"
        path.write_text(json.dumps({"$defs": {"Request": {"properties": {"cursor": {}}}}}))
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "candidate"
            with self.assertRaisesRegex(ValueError, "snapshot selection"):
                self.operation()(source.root, destination, chat=True)
            self.assertFalse(destination.exists())

    def test_chat_candidate_refuses_missing_format_runtime(self):
        for name in (
            "adapters/docling_local/formats.py",
            "adapters/docling_local/unpaginated.py",
            "schemas/passage.v0.4.json",
        ):
            source = self.fixture()
            (source.root / "_internal/openreading" / name).unlink()
            source.metadata["files"] = inventory(source.root)
            source.write_metadata()
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "candidate"
                with self.assertRaisesRegex(ValueError, "snapshot selection"):
                    self.operation()(source.root, output, chat=True)
                self.assertFalse(output.exists())

    def test_chat_settings_helper_remains_bound_to_claude_after_relocation(self):
        import plistlib
        import shutil

        from test_chatgpt_package import ChatGPTPackageTests

        fixtures = ChatGPTPackageTests()
        self.addCleanup(fixtures.doCleanups)
        source = fixtures.fixture()
        worker = source.root / "openreading-worker"
        worker.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
        source.metadata["files"] = inventory(source.root)
        source.metadata["worker_sha256"] = sha256(worker)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temporary:
            built = Path(temporary) / "built"
            package.package_docling_desktop(source.root, built, chat=True)
            moved = Path(temporary) / "installed café space"
            shutil.move(built, moved)
            contents = moved / "OpenReading Settings.app/Contents"
            self.assertTrue(contents.is_dir(), "Claude server settings app is missing")
            info = plistlib.loads((contents / "Info.plist").read_bytes())
            helper = contents / "MacOS" / info["CFBundleExecutable"]
            process = subprocess.run([str(helper)], capture_output=True, text=True, check=True)
            self.assertEqual(
                process.stdout.splitlines(),
                ["--client", "claude-desktop", "--destination-settings"],
            )
            metadata = json.loads((moved / "package-info.json").read_text())
            self.assertEqual(metadata["helper_sha256"], sha256(helper))
            self.assertEqual(metadata["helper_info_sha256"], sha256(contents / "Info.plist"))

    def test_chat_settings_refuses_runtime_without_server_support(self):
        from test_chatgpt_package import ChatGPTPackageTests

        fixtures = ChatGPTPackageTests()
        self.addCleanup(fixtures.doCleanups)
        source = fixtures.fixture()
        (source.root / "_internal/runtime/server_profile.py").unlink()
        source.metadata["files"] = inventory(source.root)
        source.write_metadata()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "candidate"
            with self.assertRaisesRegex(ValueError, "server destination"):
                package.package_docling_desktop(source.root, target, chat=True)
            self.assertFalse(target.exists())
