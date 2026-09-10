"""Feasibility reports cannot count incomplete or incorrect conversions as success."""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "docling_feasibility.py"


class FeasibilityTests(unittest.TestCase):
    def test_matrix_requires_all_repetitions_and_extraction_checks(self):
        spec = importlib.util.spec_from_file_location("feasibility", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        row = {
            "run": 0,
            "pages": 10,
            "status": "success",
            "native_found": True,
            "origins_match": True,
            "image_found": True,
            "table_found": True,
            "seconds": 1.0,
        }
        observations = [{"stage": "setup", "seconds": 0.1}] + [dict(row, run=i) for i in range(3)]
        self.assertTrue(module.accepts(observations, 10, True))
        self.assertFalse(module.accepts(observations[:-1], 10, True))
        for field, bad in [
            ("pages", 1),
            ("status", "failure"),
            ("table_found", False),
            ("native_found", False),
            ("origins_match", False),
            ("image_found", False),
            ("seconds", float("nan")),
        ]:
            changed = [*observations[:-1], {**observations[-1], field: bad}]
            self.assertFalse(module.accepts(changed, 10, True))
        self.assertFalse(module.accepts(observations, 10, False))
