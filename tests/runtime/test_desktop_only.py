"""Retired study entry points refuse before credentials, processes, or writes."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class DesktopOnlyTests(unittest.TestCase):
    def test_finalization_refuses_before_reading_a_draft_or_writing_outputs(self):
        from measurement.probe import finalize

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "synthetic-not-a-key"}):
                with self.assertRaisesRegex(ValueError, "Provider API trials are disabled"):
                    finalize(root, "claude-sonnet-4-6", "account", root / "pricing.json")
            self.assertEqual(list(root.iterdir()), [])

    def test_preparation_cannot_create_new_api_studies(self):
        from measurement.prepare import prepare as legacy
        from measurement.probe import prepare as probe

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for call in (
                lambda: legacy(root / "study", root, root, "model", "account", "primary"),
                lambda: probe(root / "probe", root, root, root, root, root),
            ):
                with self.assertRaisesRegex(ValueError, "Provider API trials are disabled"):
                    call()
            self.assertEqual(list(root.iterdir()), [])
