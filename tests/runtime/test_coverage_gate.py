"""Line coverage cannot conceal insufficient branch coverage in the Python gate."""

import contextlib
import io
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class CoverageGateTests(unittest.TestCase):
    def test_each_metric_must_independently_reach_95_percent(self):
        from runtime.coverage_gate import check_report

        totals = {
            "covered_lines": 95,
            "num_statements": 100,
            "covered_branches": 95,
            "num_branches": 100,
        }
        check_report({"totals": totals})
        for key, value in [("covered_lines", 94), ("covered_branches", 94), ("num_branches", 0)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_report({"totals": {**totals, key: value}})

    def test_command_reads_the_report_and_fails_for_low_branch_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "coverage.json"
            report.write_text(
                json.dumps(
                    {
                        "totals": {
                            "covered_lines": 100,
                            "num_statements": 100,
                            "covered_branches": 95,
                            "num_branches": 100,
                        }
                    }
                )
            )
            with (
                patch.object(sys, "argv", ["coverage_gate", str(report)]),
                contextlib.redirect_stdout(io.StringIO()) as output,
            ):
                with self.assertRaises(SystemExit) as result:
                    runpy.run_module("runtime.coverage_gate", run_name="__main__")
                self.assertEqual(result.exception.code, 0)
                self.assertIn("95.00%", output.getvalue())
