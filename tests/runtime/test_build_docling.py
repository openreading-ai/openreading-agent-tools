"""The diagnostic freezer preserves engine pins and required source identity inputs."""

import importlib
import importlib.util
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class DoclingBuildTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime.build_docling"))
        return importlib.import_module("runtime.build_docling")

    def test_p0_preserves_candidate_pins_and_excludes_other_engines(self):
        base = tomllib.loads((ROOT / "runtime/feasibility/uv.lock").read_text())
        p0 = tomllib.loads((ROOT / "runtime/p0/uv.lock").read_text())
        packages = {p["name"]: p for p in p0["package"]}
        for p in base["package"]:
            if "virtual" not in p["source"]:
                self.assertEqual(packages[p["name"]]["version"], p["version"])
                self.assertEqual(packages[p["name"]]["source"], p["source"])
        self.assertEqual(packages["pyinstaller"]["version"], "6.22.2")
        self.assertFalse(
            set(packages)
            & {"torch", "torchvision", "docling-ibm-models", "pymupdf", "onnxruntime-gpu"}
        )

    def test_freezer_retains_sources_metadata_and_never_overwrites(self):
        module = self.module()
        from runtime.verify import verify_release

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model = root / "models/docling-project--docling-layout-heron-onnx/model.onnx"
            model.parent.mkdir(parents=True)
            model.write_bytes(b"synthetic model")
            tess = root / "tessdata"
            (tess / "configs").mkdir(parents=True)
            for name in ["eng.traineddata", "osd.traineddata", "configs/tsv"]:
                (tess / name).write_text(name)
            binary = root / "tesseract"
            binary.write_bytes(b"native")
            binary.chmod(0o755)

            def freeze(command, **kwargs):
                spec = Path(command[-1]).read_text()
                self.assertIn("module_collection_mode", spec)
                self.assertIn("pyz+py", spec)
                self.assertIn("copy_metadata", spec)
                self.assertIn("torch", spec)
                folder = Path(command[command.index("--distpath") + 1]) / "openreading-worker"
                folder.mkdir(parents=True)
                (folder / "openreading-worker").write_bytes(b"worker")
                (folder / "openreading-worker").chmod(0o755)

            def native(source, destination):
                import shutil

                (destination / "bin").mkdir(parents=True)
                shutil.copy2(source, destination / "bin/tesseract")
                return {"tesseract": "synthetic native identity"}

            with (
                patch.object(
                    module,
                    "selected_environment",
                    return_value={"core_commit": "a" * 40, "packages": {"openreading": "0.3.0"}},
                ),
                patch.object(module.platform, "machine", return_value="arm64"),
                patch.object(module.platform, "mac_ver", return_value=("15.1", "", "")),
                patch.object(module.platform, "python_version", return_value="3.11.15"),
                patch.object(module.sys, "platform", "darwin"),
                patch.object(module.subprocess, "run", side_effect=freeze),
                patch.object(module, "bundle_native", side_effect=native),
                patch.object(module, "notices", return_value="fixture notices"),
            ):
                output = module.build_runtime(root / "output", root / "models", binary, tess)
                release = verify_release(output)
                self.assertEqual(release["profile"], "local-document-proof-v2")
                self.assertEqual(release["distribution"], "development-only")
                self.assertEqual(release["core_commit"], "a" * 40)
                with self.assertRaises(ValueError):
                    module.build_runtime(output, root / "models", binary, tess)
                (tess / "configs/tsv").unlink()
                with self.assertRaises(ValueError):
                    module.build_runtime(root / "bad", root / "models", binary, tess)
            with patch.object(module.sys, "platform", "linux"), self.assertRaises(ValueError):
                module.build_runtime(root / "bad", root / "models", binary, tess)

    def test_cli_resolves_input_paths_and_returns_the_built_directory(self):
        import contextlib
        import io

        module = self.module()
        with (
            patch.object(module, "build_runtime", return_value=Path("/synthetic/output")) as build,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(
                module.main(
                    [
                        "--output",
                        "out",
                        "--models",
                        "models",
                        "--tesseract",
                        "ocr",
                        "--tessdata",
                        "data",
                    ]
                ),
                0,
            )
        self.assertTrue(all(path.is_absolute() for path in build.call_args.args))
        self.assertEqual(output.getvalue().strip(), "/synthetic/output")

    def test_spec_includes_docling_plugin_entrypoints(self):
        import sys
        from types import ModuleType, SimpleNamespace

        module = self.module()
        hooks = ModuleType("PyInstaller.utils.hooks")
        hooks.collect_data_files = lambda name: []
        hooks.collect_submodules = lambda name: []
        hooks.copy_metadata = lambda name: []
        hooks.collect_entry_point = lambda name: (
            [("metadata", "destination")],
            ["plugin.discovered_from_metadata"],
        )
        analyses = []

        def analyze(*args, **kwargs):
            analyses.append(kwargs)
            return SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])

        scope = {
            "Analysis": analyze,
            "PYZ": lambda *a: None,
            "EXE": lambda *a, **k: None,
            "COLLECT": lambda *a, **k: None,
        }
        with (
            patch.dict(sys.modules, {"PyInstaller.utils.hooks": hooks}),
            patch("importlib.metadata.distributions", return_value=[]),
        ):
            exec(module.spec_text(), scope)
        self.assertIn("plugin.discovered_from_metadata", analyses[0]["hiddenimports"])
        self.assertIn(("metadata", "destination"), analyses[0]["datas"])
        self.assertEqual(analyses[0]["module_collection_mode"]["openreading"], "pyz+py")
