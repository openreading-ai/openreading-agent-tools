"""Synthetic evaluation documents carry frozen page-specific answers and no private data."""

import tempfile
import unittest
from pathlib import Path

from measurement.prepare import generate_dataset


class DatasetTests(unittest.TestCase):
    def test_documents_and_questions_preserve_physical_page_ground_truth(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = generate_dataset(root)
            self.assertEqual(len(dataset["tasks"]), 12)
            self.assertEqual(
                {t["category"] for t in dataset["tasks"]},
                {"agreement", "manual", "report"},
            )
            for name, count in [("agreement", 24), ("manual", 48), ("report", 80)]:
                with pymupdf.open(root / f"documents/{name}.pdf") as doc:
                    self.assertEqual(len(doc), count)
                    self.assertTrue(all(page.get_text().strip() for page in doc))
            with pymupdf.open(root / "documents/agreement.pdf") as doc:
                self.assertIn("60 days", doc[12].get_text())
            text = (root / "extractions/agreement.txt").read_text()
            self.assertIn("[Physical page 13]", text)
            self.assertEqual(text.count("[Physical page "), 24)
