"""Feasibility reports cannot count incomplete or incorrect conversions as success."""

import importlib.util
import json
import re
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "docling_feasibility.py"
CANDIDATE = ROOT / "runtime" / "feasibility"
SPEC = importlib.util.spec_from_file_location("feasibility", SCRIPT)
feasibility = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(feasibility)


def page_text(number, ocr):
    lines = [
        feasibility.NATIVE_TEXT[0],
        f"Physical source page {number}. {feasibility.NATIVE_TEXT[1]}",
        *([feasibility.RASTER_TEXT] if ocr else []),
        *feasibility.TABLE_TEXT,
    ]
    return "\n".join(lines)


def projection(pages, ocr, warnings=("table_text_unavailable",)):
    schema = {
        "document": {
            "pages": [
                {"page_number": number, "text": page_text(number, ocr)}
                for number in range(1, pages + 1)
            ]
        },
        "warnings": [{"code": code} for code in warnings],
    }
    origins = {number: "mixed" if ocr else "native" for number in range(1, pages + 1)}
    return schema, origins


def observations(pages, ocr):
    schema, origins = projection(pages, ocr)
    row = {
        "status": "success",
        "seconds": 1.0,
        **feasibility.inspect_pages(pages, ocr, schema, origins),
    }
    setup = {"stage": "setup", "seconds": 0.1, "network_denied": True}
    return [setup, *[dict(row, run=index) for index in range(3)]]


class AcceptanceTests(unittest.TestCase):
    def test_matrix_requires_all_repetitions_and_extraction_checks(self):
        rows = observations(10, True)
        self.assertTrue(feasibility.accepts(rows, 10, True))
        self.assertFalse(feasibility.accepts(rows[:-1], 10, True))
        self.assertFalse(feasibility.accepts([*rows, dict(rows[-1], run=3)], 10, True))
        for field, bad in [
            ("pages", 1),
            ("status", "failure"),
            ("table_found", False),
            ("native_found", False),
            ("origins_match", False),
            ("image_found", False),
            ("page_numbers_match", False),
            ("page_markers_match", False),
            ("warnings", ["unreadable_pages"]),
            ("warnings", None),
            ("seconds", float("nan")),
            ("seconds", 0),
        ]:
            changed = [*rows[:-1], {**rows[-1], field: bad}]
            self.assertFalse(feasibility.accepts(changed, 10, True), field)
        self.assertFalse(feasibility.accepts(rows, 10, False))

    def test_matrix_requires_observed_network_denial(self):
        rows = observations(1, False)
        self.assertTrue(feasibility.accepts(rows, 1, False))
        for setup in [
            {**rows[0], "network_denied": False},
            {"stage": "setup", "seconds": 0.1},
        ]:
            self.assertFalse(feasibility.accepts([setup, *rows[1:]], 1, False))
        self.assertFalse(feasibility.accepts(rows[1:], 1, False))
        self.assertFalse(feasibility.accepts([rows[0], *rows], 1, False))

    def test_corrupted_observation_lines_fail_closed(self):
        rows = observations(1, False)
        lines = [json.dumps(row) for row in rows]
        lines[2] = lines[2][:20]
        log = mock.Mock()
        log.read_text.return_value = "\n".join(["native diagnostic", *lines, '{"broken'])
        parsed = feasibility.read_observations(log)
        self.assertEqual(len(parsed), 3)
        self.assertFalse(feasibility.accepts(parsed, 1, False))


class PageInspectionTests(unittest.TestCase):
    def check(self, schema, origins, pages=3, ocr=True):
        return feasibility.inspect_pages(pages, ocr, schema, origins)

    def test_complete_projection_passes_every_page_check(self):
        for ocr in [False, True]:
            result = self.check(*projection(3, ocr), ocr=ocr)
            self.assertEqual(result["warnings"], ["table_text_unavailable"])
            self.assertIs(result["image_found"], ocr)
            for field in [
                "page_numbers_match",
                "page_markers_match",
                "native_found",
                "table_found",
                "origins_match",
            ]:
                self.assertIs(result[field], True, field)

    def test_shifted_or_duplicated_page_text_fails(self):
        schema, origins = projection(3, True)
        first = schema["document"]["pages"][0]["text"]
        for pages in [
            [{"page_number": n, "text": first} for n in [1, 2, 3]],
            [{"page_number": n, "text": page_text(n + 1, True)} for n in [1, 2, 3]],
            [{"page_number": n, "text": page_text(n, True) + "\n" + first} for n in [1, 2, 3]],
        ]:
            schema["document"]["pages"] = pages
            self.assertFalse(self.check(schema, origins)["page_markers_match"])

    def test_missing_or_misnumbered_pages_fail(self):
        schema, origins = projection(3, True)
        schema["document"]["pages"] = schema["document"]["pages"][:2]
        self.assertFalse(self.check(schema, origins)["page_numbers_match"])
        schema, origins = projection(3, True)
        schema["document"]["pages"][2]["page_number"] = 4
        self.assertFalse(self.check(schema, origins)["page_numbers_match"])

    def test_each_expected_value_is_required_on_every_page(self):
        for value, field in [
            *[(text, "native_found") for text in feasibility.NATIVE_TEXT],
            *[(text, "table_found") for text in feasibility.TABLE_TEXT],
            (feasibility.RASTER_TEXT, "image_found"),
        ]:
            schema, origins = projection(3, True)
            page = schema["document"]["pages"][1]
            page["text"] = "\n".join(line for line in page["text"].split("\n") if line != value)
            if value == feasibility.NATIVE_TEXT[1]:
                page["text"] = page["text"].replace(value, "")
            self.assertFalse(self.check(schema, origins)[field], value)

    def test_raster_text_without_ocr_is_detected(self):
        schema, origins = projection(3, False)
        schema["document"]["pages"][2]["text"] += "\n" + feasibility.RASTER_TEXT
        self.assertTrue(self.check(schema, origins, ocr=False)["image_found"])

    def test_origins_must_cover_every_page_with_the_measured_kind(self):
        schema, origins = projection(3, True)
        for changed in [
            {**origins, 2: "native"},
            {**origins, 3: "ocr"},
            {1: "mixed", 2: "mixed"},
            {**origins, 4: "mixed"},
        ]:
            self.assertFalse(self.check(schema, changed)["origins_match"])

    def test_unexpected_warnings_are_reported(self):
        schema, origins = projection(3, True, ("table_text_unavailable", "partial_conversion"))
        result = self.check(schema, origins)
        self.assertEqual(result["warnings"], ["partial_conversion", "table_text_unavailable"])


class EnvironmentTests(unittest.TestCase):
    COMMIT = "f" * 40

    def fixture(self, directory):
        lock = directory / "uv.lock"
        lock.write_text(
            "\n".join(
                [
                    "[[package]]",
                    'name = "openreading-docling-feasibility"',
                    'source = { virtual = "." }',
                    'dependencies = [{ name = "openreading" }, { name = "docling-slim" }]',
                    "[[package]]",
                    'name = "openreading"',
                    'version = "0.3.0"',
                    f'source = {{ git = "https://example.test/core.git?rev={self.COMMIT}#{self.COMMIT}" }}',
                    "[[package]]",
                    'name = "docling-slim"',
                    'version = "2.126.0"',
                ]
            )
        )
        module = directory / "site" / "openreading" / "__init__.py"
        module.parent.mkdir(parents=True)
        module.write_text("")
        return lock, module

    def run_check(self, lock, module, distributions, commit=None, origin=None):
        commit = commit or self.COMMIT
        core = SimpleNamespace(
            read_text=lambda name: json.dumps({"vcs_info": {"commit_id": commit}}),
            locate_file=lambda name: module.parents[1] / name,
        )
        dists = [
            SimpleNamespace(metadata={"Name": name}, version=version)
            for name, version in distributions
        ]
        spec = SimpleNamespace(origin=str(origin or module))
        with (
            mock.patch.object(feasibility.metadata, "distributions", return_value=dists),
            mock.patch.object(feasibility.metadata, "distribution", return_value=core),
            mock.patch.object(
                feasibility.importlib.util,
                "find_spec",
                side_effect=lambda name: spec if name == "openreading" else None,
            ),
        ):
            return feasibility.selected_environment(lock)

    def test_locked_environment_reports_its_core_identity(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            lock, module = self.fixture(directory)
            identity = self.run_check(
                lock, module, [("openreading", "0.3.0"), ("docling_slim", "2.126.0")]
            )
            self.assertEqual(identity["core_commit"], self.COMMIT)
            self.assertEqual(
                identity["packages"],
                {"docling-slim": "2.126.0", "openreading": "0.3.0"},
            )

    def test_unlocked_or_changed_packages_are_refused(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            lock, module = self.fixture(directory)
            for distributions in [
                [("openreading", "0.3.0"), ("torch", "2.9.0")],
                [("openreading", "0.3.0"), ("docling-slim", "2.125.0")],
            ]:
                with self.assertRaises(RuntimeError):
                    self.run_check(lock, module, distributions)

    def test_missing_locked_dependency_is_refused(self):
        with tempfile.TemporaryDirectory() as name:
            lock, module = self.fixture(Path(name))
            with self.assertRaisesRegex(RuntimeError, "missing"):
                self.run_check(lock, module, [("openreading", "0.3.0")])

    def test_sibling_checkout_or_other_commit_is_refused(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            lock, module = self.fixture(directory)
            sibling = directory / "openreading-core" / "src" / "openreading" / "__init__.py"
            sibling.parent.mkdir(parents=True)
            sibling.write_text("")
            for options in [{"origin": sibling}, {"commit": "0" * 40}]:
                with self.assertRaises(RuntimeError):
                    self.run_check(lock, module, [("openreading", "0.3.0")], **options)

    def test_prohibited_modules_are_refused_even_outside_package_metadata(self):
        with (
            mock.patch.object(
                feasibility.importlib.util,
                "find_spec",
                side_effect=lambda name: object() if name == "fitz" else None,
            ),
            self.assertRaisesRegex(RuntimeError, "fitz"),
        ):
            feasibility.selected_environment(Path("unused.lock"))


class CandidateLockTests(unittest.TestCase):
    def test_lock_pins_the_declared_core_without_prohibited_packages(self):
        lock = tomllib.loads((CANDIDATE / "uv.lock").read_text())
        packages = {package["name"]: package for package in lock["package"]}
        declared = tomllib.loads((CANDIDATE / "pyproject.toml").read_text())
        core = next(
            dep for dep in declared["project"]["dependencies"] if dep.startswith("openreading")
        )
        commit = re.fullmatch(r".*@([0-9a-f]{40})", core).group(1)
        self.assertEqual(packages["openreading"]["source"]["git"].rpartition("#")[2], commit)
        self.assertEqual(
            sorted(
                {
                    "torch",
                    "torchvision",
                    "docling-ibm-models",
                    "pymupdf",
                    "onnxruntime-gpu",
                }
                & set(packages)
            ),
            [],
        )
        readme = (CANDIDATE / "README.md").read_text()
        self.assertIn(commit, readme)
        for name, label in [
            ("docling-slim", "Docling slim"),
            ("transformers", "Transformers"),
            ("onnxruntime", "CPU ONNX Runtime"),
        ]:
            self.assertIn(f"{label} {packages[name]['version']}", readme)


class MemoryTests(unittest.TestCase):
    def psutil(self):
        class Error(Exception):
            pass

        class AccessDenied(Error):
            pass

        class NoSuchProcess(Error):
            pass

        return SimpleNamespace(
            Error=Error,
            AccessDenied=AccessDenied,
            NoSuchProcess=NoSuchProcess,
            Process=mock.Mock(),
        )

    def test_inaccessible_process_invalidates_the_sample(self):
        psutil = self.psutil()

        parent = mock.Mock()
        parent.children.return_value = [mock.Mock()]
        parent.memory_info.return_value = SimpleNamespace(rss=100)
        parent.children.return_value[0].memory_info.side_effect = psutil.AccessDenied(2)
        with (
            mock.patch.dict(sys.modules, {"psutil": psutil}),
            mock.patch.object(psutil, "Process", return_value=parent),
        ):
            self.assertIsNone(feasibility.tree_rss(1))

    def test_exited_child_preserves_the_rest_of_the_sample(self):
        psutil = self.psutil()

        parent, child = mock.Mock(), mock.Mock()
        parent.children.return_value = [child]
        parent.memory_info.return_value = SimpleNamespace(rss=100)
        child.memory_info.side_effect = psutil.NoSuchProcess(2)
        with (
            mock.patch.dict(sys.modules, {"psutil": psutil}),
            mock.patch.object(psutil, "Process", return_value=parent),
        ):
            self.assertEqual(feasibility.tree_rss(1), 100)

    def test_parent_exit_is_distinct_from_inaccessible_memory(self):
        psutil = self.psutil()
        psutil.Process.side_effect = psutil.NoSuchProcess(1)
        with mock.patch.dict(sys.modules, {"psutil": psutil}):
            self.assertEqual(feasibility.tree_rss(1), 0)
