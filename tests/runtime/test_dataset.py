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

    def test_preparation_freezes_inputs_without_authorizing_a_live_run(self):
        import json
        from unittest.mock import patch

        from measurement.prepare import prepare
        from runtime.verify import sha256

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            plugin = root / "plugin"
            (plugin / "server").mkdir(parents=True)
            (plugin / "server/release.json").write_text("{}")
            (plugin / "skills/read-local-document").mkdir(parents=True)
            (plugin / "skills/read-local-document/SKILL.md").write_text("Read source evidence.")
            client = root / "claude-test"
            client.write_text('#!/bin/sh\necho "2.1.266 (Claude Code)"\n')
            client.chmod(0o755)
            with (
                patch(
                    "measurement.prepare.verify_release",
                    return_value={"core_commit": "a" * 40},
                ),
                patch.dict("os.environ", {"ANTHROPIC_API_KEY": "synthetic-key"}),
            ):
                path = prepare(
                    root / "evidence",
                    plugin,
                    client,
                    "claude-sonnet-4-6",
                    "synthetic-account",
                    "calibration",
                )
                manifest = json.loads(path.read_text())
                self.assertEqual(manifest["max_trials"], 12)
                self.assertEqual(manifest["dataset_sha256"], sha256(path.parent / "dataset.json"))
                self.assertNotIn("synthetic-key", path.read_text())
                self.assertNotIn("approved", manifest)
                with self.assertRaises(ValueError):
                    prepare(
                        root / "evidence",
                        plugin,
                        client,
                        "claude-sonnet-4-6",
                        "synthetic-account",
                        "calibration",
                    )
            (root / ".git").mkdir()
            with self.assertRaises(ValueError):
                prepare(
                    root / "other",
                    plugin,
                    client,
                    "claude-sonnet-4-6",
                    "synthetic-account",
                    "primary",
                )
