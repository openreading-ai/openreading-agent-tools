"""Exercise metadata-only Desktop timing without attributing model or parser work."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from measurement import desktop_timing


def event(seconds, message):
    return f"2026-09-12T12:00:{seconds:06.3f}Z [private connector] [info] {message}\n"


def request(seconds, identifier, method="tools/call"):
    return event(seconds, f'Message from client: method="{method}" id={identifier} params PRIVATE')


def response(seconds, identifier):
    return event(seconds, f"Message from server: id={identifier} PRIVATE")


class DesktopTimingTests(unittest.TestCase):
    def test_transport_outcome_distinguishes_error_result_and_unknown(self):
        report = self.report(
            request(0, 0, "initialize"),
            event(0.5, "Message from server: id=0 result PRIVATE"),
            request(1, 2),
            event(2, "Message from server: id=2 error(code=0) PRIVATE"),
            request(3, 3),
            event(4, "Message from server: id=3 result(1 blocks) PRIVATE"),
            request(5, 4),
            response(6, 4),
        )
        self.assertEqual(
            [r.get("outcome") for r in report["calls"]], ["error", "result", "unknown"]
        )
        self.assertEqual(report["initializations"][0].get("outcome"), "result")
        self.assertEqual(report["pairing"], "observed_pairs_complete")
        self.assertEqual(report["format_version"], "3")
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_outcome_never_comes_from_payload_or_an_ambiguous_response(self):
        for suffix in ("resulting error", "errorish result", 'PRIVATE {"error": "secret"}', ""):
            with self.subTest(suffix=suffix):
                report = self.report(request(1, 2), event(2, f"Message from server: id=2 {suffix}"))
                self.assertEqual(report["calls"][0].get("outcome"), "unknown")
        report = self.report(
            request(0, 2),
            request(1, 0, "initialize"),
            response(2, 0),
            request(3, 2),
            event(4, "Message from server: id=2 result PRIVATE"),
        )
        self.assertIn("outcome", report["calls"][0])
        self.assertIsNone(report["calls"][0]["outcome"])
        self.assertIsNone(report["calls"][1]["outcome"])

    def test_unanswered_initialization_alone_makes_pairing_incomplete(self):
        report = self.report(request(0, 0, "initialize"), request(1, 2), response(2, 2))
        self.assertEqual(report["pairing"], "incomplete")

    def test_clean_restart_resets_gap_without_an_unfinished_call(self):
        report = self.report(
            request(0, 0, "initialize"),
            response(1, 0),
            request(2, 2),
            response(3, 2),
            request(20, 0, "initialize"),
            response(21, 0),
            request(22, 2),
            response(23, 2),
        )
        self.assertIsNone(report["calls"][1]["gap_before_seconds"])

    def test_stray_response_alone_makes_pairing_incomplete(self):
        report = self.report(response(0, 99), request(1, 2), response(2, 2))
        self.assertEqual(report["pairing"], "incomplete")

    def test_unanswered_non_tool_request_is_not_complete(self):
        report = self.report(request(0, 1, "tools/list"), request(1, 2), response(2, 2))
        self.assertEqual(report["pairing"], "incomplete")

    def test_close_and_shutdown_prevent_cross_boundary_pairing_and_gaps(self):
        for boundary in ("Client transport closed", "Shutting down server..."):
            with self.subTest(boundary=boundary):
                report = self.report(
                    request(0, 2), event(1, boundary), response(2, 2), request(3, 3), response(4, 3)
                )
                self.assertIsNone(report["calls"][0]["seconds"])
                self.assertIsNone(report["calls"][1]["gap_before_seconds"])
                self.assertEqual(report["pairing"], "incomplete")

    def test_late_response_after_ambiguous_restart_is_not_a_duration(self):
        report = self.report(
            request(0, 2),
            request(1, 0, "initialize"),
            response(2, 0),
            request(3, 2),
            response(4, 2),
        )
        self.assertEqual(report["pairing"], "incomplete")
        self.assertIsNone(report["calls"][1]["seconds"])

    def test_non_info_tool_call_is_not_silently_skipped(self):
        report = self.report(
            request(0, 2),
            response(1, 2),
            request(2, 3).replace("[info]", "[debug]"),
            response(4, 3),
            request(5, 4),
            response(6, 4),
        )
        self.assertEqual(len(report["calls"]), 3)
        self.assertEqual(report["calls"][2]["gap_before_seconds"], 1)

    def test_server_requests_use_a_separate_id_namespace(self):
        report = self.report(
            request(0, 2),
            event(1, 'Message from server: method="elicitation/create" id=2 params PRIVATE'),
            event(2, "Message from client: id=2 PRIVATE"),
            response(3, 2),
        )
        self.assertEqual(report["calls"][0]["seconds"], 3)
        self.assertNotIn("PRIVATE", json.dumps(report))

    def report(self, *lines):
        return desktop_timing.summarize(io.BytesIO("".join(lines).encode()))

    def test_reports_call_latency_and_idle_gap_without_payloads(self):
        report = self.report(
            request(0, 0, "initialize"),
            response(0.5, 0),
            request(1, 2),
            response(13, 2),
            request(30, 3),
            response(30.025, 3),
        )
        self.assertEqual(report["initializations"][0]["seconds"], 0.5)
        self.assertEqual([r["seconds"] for r in report["calls"]], [12, 0.025])
        self.assertEqual(report["calls"][1]["gap_before_seconds"], 17)
        self.assertEqual(report["pairing"], "observed_pairs_complete")
        self.assertIsNone(report["document"])
        self.assertIsNone(report["parser_seconds"])
        self.assertNotIn("PRIVATE", json.dumps(report))
        self.assertNotIn("private connector", json.dumps(report))

    def test_restart_reuses_ids_without_cross_session_pairing(self):
        report = self.report(
            request(1, 0, "initialize"),
            response(2, 0),
            request(3, 2),
            request(4, 0, "initialize"),
            response(5, 0),
            request(6, 2),
            response(7, 2),
        )
        self.assertEqual([r["segment"] for r in report["calls"]], [1, 2])
        self.assertIsNone(report["calls"][0]["seconds"])
        self.assertIsNone(report["calls"][1]["seconds"])
        self.assertIsNone(report["calls"][1]["gap_before_seconds"])
        self.assertEqual(report["pairing"], "incomplete")

    def test_partial_log_never_invents_a_duration(self):
        report = self.report(response(1, 99), request(2, 2), request(3, 3), response(4, 3))
        self.assertEqual(report["unmatched_responses"], 1)
        self.assertFalse(report["calls"][0]["initialization_observed"])
        self.assertIsNone(report["calls"][0]["seconds"])
        self.assertIsNone(report["calls"][1]["gap_before_seconds"])
        self.assertEqual(report["pairing"], "incomplete")

    def test_concurrent_calls_are_paired_by_id_and_have_no_idle_gap(self):
        report = self.report(request(0, 2), request(1, 3), response(2, 3), response(5, 2))
        self.assertEqual([r["seconds"] for r in report["calls"]], [5, 1])
        self.assertIsNone(report["calls"][1]["gap_before_seconds"])

    def test_skips_known_other_methods_and_non_message_lines(self):
        report = self.report(
            "noise PRIVATE\n",
            request(0, 1, "tools/list"),
            response(1, 1),
            event(
                2, 'Message from client: method="notifications/initialized" { metadata: undefined }'
            ),
            event(2, 'Message from server: method="notifications/progress" params PRIVATE'),
            request(3, 2),
            response(4, 2),
        )
        self.assertEqual(len(report["calls"]), 1)
        self.assertEqual(report["unmatched_responses"], 0)
        self.assertEqual(report["pairing"], "observed_pairs_complete")

    def test_rejects_ambiguous_ids_clock_rollback_and_unknown_format(self):
        for lines in (
            (request(1, 2), request(2, 2)),
            (request(1, 2), response(2, 2), response(3, 2)),
            (request(2, 2), response(1, 2)),
            (request(1, '"secret"'),),
            (event(1, 'Message from client: method="tools/call" params PRIVATE'),),
            (request(1, 2).replace("12:00:01", "12:00:99"),),
        ):
            with self.subTest(lines=lines), self.assertRaises(ValueError):
                self.report(*lines)

    def test_no_recognized_calls_refuses_instead_of_success(self):
        with self.assertRaises(ValueError):
            self.report("unrecognized log format\n")

    def test_binding_covers_ignored_bytes_too(self):
        first = self.report(request(0, 2), response(1, 2))
        second = self.report(request(0, 2), response(1, 2), "ignored PRIVATE\n")
        self.assertNotEqual(first["log_sha256"], second["log_sha256"])
        self.assertEqual(first["calls"], second["calls"])

    def test_cli_reads_only_selected_log_and_sanitizes_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PRIVATE.log"
            path.write_text(request(1, 2) + response(2, 2))
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(desktop_timing.main(["--log", str(path)]), 0)
            self.assertEqual(json.loads(out.getvalue())["calls"][0]["seconds"], 1)
            path.unlink()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(desktop_timing.main(["--log", str(path)]), 2)
            self.assertNotIn("PRIVATE", out.getvalue() + err.getvalue())
            path.write_bytes(b"\xff")
            with contextlib.redirect_stderr(err):
                self.assertEqual(desktop_timing.main(["--log", str(path)]), 2)

    def test_cli_incomplete_pairing_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log"
            path.write_text(request(1, 2))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(desktop_timing.main(["--log", str(path)]), 1)
