"""Native relocation copies the dependency closure and refuses ambiguous libraries."""

import importlib
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class NativeBundleTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime.native_bundle"))
        return importlib.import_module("runtime.native_bundle")

    def test_dependencies_relocate_and_system_libraries_stay_external(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            binary = root / "tesseract"
            library = root / "libsample.dylib"
            binary.write_text("executable")
            binary.chmod(0o755)
            library.write_text("library")
            commands = []

            def output(command, **kwargs):
                commands.append(command)
                if command[0] == "/usr/bin/otool":
                    target = Path(command[-1])
                    return f"{target}:\n\t{library if target.name == 'tesseract' else '/usr/lib/libSystem.B.dylib'} (compatibility version 1.0.0, current version 1.0.0)\n"
                return "tesseract fixture"

            with (
                patch.object(module.subprocess, "check_output", side_effect=output),
                patch.object(module.subprocess, "run") as run,
            ):
                result = module.bundle_native(binary, root / "bundle")
            self.assertEqual((root / "bundle/lib/libsample.dylib").read_text(), "library")
            self.assertEqual((root / "bundle/bin/tesseract").read_text(), "executable")
            changes = [args.args[0] for args in run.call_args_list if "-change" in args.args[0]]
            self.assertEqual(len(changes), 1)
            self.assertIn("@loader_path/../lib/libsample.dylib", changes[0])
            self.assertEqual(result["tesseract"], "tesseract fixture")
            self.assertEqual(result["libraries"], ["libsample.dylib"])
            self.assertEqual(
                sum(args.args[0][0] == "/usr/bin/codesign" for args in run.call_args_list), 2
            )

    def test_unresolved_or_colliding_install_names_refuse(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            binary = root / "tesseract"
            binary.write_text("x")
            left = root / "a/libsame.dylib"
            left.parent.mkdir()
            left.write_text("a")
            right = root / "b/libsame.dylib"
            right.parent.mkdir()
            right.write_text("b")
            for paths in [["@rpath/missing.dylib"], [str(left), str(right)]]:
                destination = root / str(len(paths))
                with (
                    self.subTest(paths=paths),
                    patch.object(module, "dependencies", return_value=paths),
                    patch.object(module.subprocess, "check_output", return_value=""),
                    self.assertRaises(ValueError),
                ):
                    module.bundle_native(binary, destination)

    def test_otool_failure_is_not_a_partial_success(self):
        module = self.module()
        with (
            patch.object(
                module.subprocess,
                "check_output",
                side_effect=subprocess.CalledProcessError(1, "otool"),
            ),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            module.dependencies(Path("/missing"))

    def test_loader_relative_rpath_resolves_without_homebrew_search(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            library = root / "lib/libsample.dylib"
            library.parent.mkdir()
            library.write_text("library")
            source = root / "lib/libcaller.dylib"
            source.write_text("caller")
            listing = "cmd LC_RPATH\ncmdsize 32\npath @loader_path/../lib (offset 12)\n"
            with patch.object(module.subprocess, "check_output", return_value=listing):
                self.assertEqual(
                    module.resolve_dependency("@rpath/libsample.dylib", source), library.resolve()
                )
                self.assertEqual(
                    module.resolve_dependency("@loader_path/libsample.dylib", source),
                    library.resolve(),
                )
                with self.assertRaises(ValueError):
                    module.resolve_dependency("@executable_path/missing", source)

    def test_shared_and_self_references_copy_once_and_ambiguous_rpaths_refuse(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            binary = root / "tesseract"
            binary.write_text("binary")
            library = root / "libsame.dylib"
            library.write_text("library")
            graph = {binary: [str(library), str(library)], library: [str(library)]}
            with (
                patch.object(module, "dependencies", side_effect=lambda path: graph[path]),
                patch.object(module.subprocess, "run"),
                patch.object(module.subprocess, "check_output", return_value="tesseract fixture"),
            ):
                result = module.bundle_native(binary, root / "bundle")
            self.assertEqual(result["libraries"], ["libsame.dylib"])
            second = root / "other/libsame.dylib"
            second.parent.mkdir()
            second.write_text("other")
            missing = root / "missing"
            listing = f"cmd LC_RPATH\npath {root} (offset 12)\ncmd LC_RPATH\npath {second.parent} (offset 12)\ncmd LC_RPATH\npath {missing} (offset 12)\ncmd LC_RPATH\npath @unknown/location (offset 12)\n"
            with (
                patch.object(module.subprocess, "check_output", return_value=listing),
                self.assertRaisesRegex(ValueError, "ambiguous"),
            ):
                module.resolve_dependency("@rpath/libsame.dylib", binary)
