"""Historical probe schedules and disabled compatibility commands stay explicit."""

import contextlib
import io
import json
import unittest
from pathlib import Path

from measurement.probe import MODEL_ID, main, schedule


class ProbeTests(unittest.TestCase):
    def test_historical_schedule_preserves_every_arm_and_question(self):
        rows = schedule()
        self.assertEqual(len(rows), 9)
        self.assertEqual(
            {(r["task_id"], r["arm"]) for r in rows},
            {(n + "-single_fact", a) for n in ("agreement", "manual", "report") for a in "ABC"},
        )
        self.assertEqual(rows, schedule())

    def test_historical_model_identifiers_match_the_schema(self):
        schema = json.loads(Path("measurement/probe-manifest.schema.json").read_text())
        self.assertEqual(schema["properties"]["model_id"]["pattern"], f"^{MODEL_ID.pattern}$")
        self.assertTrue(MODEL_ID.fullmatch("claude-sonnet-4-6"))
        self.assertFalse(MODEL_ID.fullmatch("claude-latest"))

    def test_old_cli_commands_refuse_without_preparing_a_study(self):
        for args in (
            [
                "prepare",
                *[
                    v
                    for name in ("output", "evidence", "python", "client", "assets", "lock")
                    for v in ("--" + name, "/missing")
                ],
            ],
            [
                "finalize",
                "/missing",
                "--model",
                "model",
                "--account",
                "account",
                "--pricing",
                "/missing",
            ],
        ):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaisesRegex(ValueError, "Provider API trials are disabled"):
                    main(args)
            self.assertEqual(output.getvalue(), "")
