"""Desktop candidates preserve verified Docling resources and explicit setup semantics."""

import contextlib
import io
import json
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
            with self.assertRaises(ValueError):
                self.operation()(source.root, target)

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
