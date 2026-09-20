"""The public corpus freezes physical evidence before evaluating retrieval."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


class CorpusTests(unittest.TestCase):
    def test_generator_is_available(self):
        self.assertIsNotNone(importlib.util.find_spec("measurement.corpus"))

    def test_independent_generations_match_frozen_bytes_and_physical_pages(self):
        from pypdf import PdfReader

        from measurement.corpus import generate, recipe

        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, second = generate(Path(a)), generate(Path(b))
            self.assertEqual(first, second)
            self.assertEqual(first["files"], recipe()["expected_hashes"])
            for name, pages in [
                ("agreement", 24),
                ("manual", 48),
                ("report", 80),
                ("functional", 6),
            ]:
                pdf = PdfReader(Path(a) / "documents" / f"{name}.pdf")
                self.assertEqual(len(pdf.pages), pages)
            text = PdfReader(Path(a) / "documents/agreement.pdf").pages[2].extract_text()
            self.assertIn("60 days", text)
            self.assertIn("Printed page 1", text)
            self.assertEqual(len(recipe()["tasks"]), 12)
            self.assertFalse((Path(a) / "documents/ground-truth.json").exists())
            self.assertTrue((Path(a) / "ground-truth.json").is_file())

    def test_generation_refuses_reusing_a_directory(self):
        from measurement.corpus import generate

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            generate(root)
            with self.assertRaises(FileExistsError):
                generate(root)

    def test_generation_does_not_depend_on_platform_rasterization(self):
        from unittest.mock import patch

        from measurement.corpus import generate, recipe

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("PIL.ImageFont.truetype", side_effect=AssertionError("platform rasterizer")),
        ):
            result = generate(Path(temporary))
            self.assertEqual(result["files"], recipe()["expected_hashes"])

    def test_changed_frozen_scan_is_refused(self):
        from unittest.mock import patch

        from measurement.corpus import generate, recipe

        altered = recipe()
        altered["raster_sha256"]["invoices.png"] = "0" * 64
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("measurement.corpus.recipe", return_value=altered),
        ):
            with self.assertRaisesRegex(ValueError, "scan changed"):
                generate(Path(temporary))
