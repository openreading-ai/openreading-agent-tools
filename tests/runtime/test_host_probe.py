"""Synthetic host probes preserve MCP behavior and record no credential values."""

import asyncio
import importlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import anyio
from mcp import ClientSession


class HostProbeTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("scripts.host_probe"), "Host probe is absent")
        return importlib.import_module("scripts.host_probe")

    def test_real_session_discovers_tools_echoes_and_emits_only_requested_progress(self):
        module = self.module()

        async def exercise(log):
            with module.Probe(log, startup_delay=0.01) as probe:
                send, reader = anyio.create_memory_object_stream(0)
                output, receive = anyio.create_memory_object_stream(0)
                async with send, reader, output, receive, anyio.create_task_group() as group:
                    group.start_soon(probe.run_transport, reader, output)
                    async with ClientSession(receive, send) as session:
                        initialized = await session.initialize()
                        self.assertEqual(initialized.serverInfo.name, "openreading-host-probe")
                        tools = (await session.list_tools()).tools
                        self.assertEqual({t.name for t in tools}, {"probe_echo", "probe_delay"})
                        result = await session.call_tool("probe_echo", {"nonce": "literal_nonce"})
                        self.assertEqual(
                            json.loads(result.content[0].text)["nonce"], "literal_nonce"
                        )
                        progress = []

                        async def observe(*args):
                            progress.append(args)

                        result = await session.call_tool(
                            "probe_delay",
                            {"nonce": "delay", "seconds": 0.03, "progress_every": 0.01},
                            progress_callback=observe,
                        )
                        self.assertFalse(result.isError)
                        self.assertGreater(len(progress), 0)
                        result = await session.call_tool(
                            "probe_delay", {"nonce": "no_progress", "seconds": 0.01}
                        )
                        self.assertFalse(result.isError)
                        for args in [
                            {"nonce": "bad", "seconds": -1},
                            {"nonce": "bad", "seconds": 331},
                            {"nonce": "bad", "seconds": 1, "extra": True},
                        ]:
                            self.assertTrue((await session.call_tool("probe_delay", args)).isError)
                    group.cancel_scope.cancel()

        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp).resolve() / "events.jsonl"
            with patch.dict("os.environ", {"PLANTED_API_KEY": "never-log-this-secret"}):
                asyncio.run(exercise(log))
            text = log.read_text()
            self.assertNotIn("never-log-this-secret", text)
            events = [json.loads(line) for line in text.splitlines()]
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)
            self.assertTrue(any(e["event"] == "initialize_received" for e in events))
            self.assertTrue(any(e["event"] == "initialization_released" for e in events))
            self.assertTrue(any(e["event"] == "tools_listed" for e in events))
            self.assertTrue(
                any(e["event"] == "completed" and e.get("nonce") == "delay" for e in events)
            )
            self.assertFalse(
                any(e["event"] == "progress" and e.get("nonce") == "no_progress" for e in events)
            )
            self.assertTrue(all("pid" in e and "monotonic_seconds" in e for e in events))
            from datetime import datetime

            self.assertTrue(
                all(
                    datetime.fromisoformat(e["utc_time"]).utcoffset().total_seconds() == 0
                    for e in events
                )
            )
            received = [e for e in events if e["event"] == "tool_request_received"]
            called = [e for e in events if e["event"] == "called"]
            self.assertTrue(received)
            for call in called:
                observed = next(e for e in received if e["request_id"] == call["request_id"])
                self.assertLessEqual(observed["monotonic_seconds"], call["monotonic_seconds"])
                self.assertNotIn("arguments", observed)

    def test_log_cannot_clobber_an_existing_file_and_invalid_delays_refuse(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp).resolve() / "log"
            path.write_text("retain")
            with self.assertRaises(FileExistsError):
                module.Probe(path)
            self.assertEqual(path.read_text(), "retain")
            for delay in [-1, 31, float("nan"), True]:
                with self.subTest(delay=delay), self.assertRaises(ValueError):
                    module.Probe(path.parent / "new", startup_delay=delay)
            self.assertFalse((path.parent / "new").exists())

    def test_progress_intervals_cannot_flood_the_event_log(self):
        module = self.module()

        async def exercise(log):
            with module.Probe(log) as probe:
                send, reader = anyio.create_memory_object_stream(0)
                output, receive = anyio.create_memory_object_stream(0)
                async with send, reader, output, receive, anyio.create_task_group() as group:
                    group.start_soon(probe.run_transport, reader, output)
                    async with ClientSession(receive, send) as session:
                        await session.initialize()
                        result = await session.call_tool(
                            "probe_delay",
                            {"nonce": "flood", "seconds": 0.001, "progress_every": 0.000001},
                        )
                        self.assertTrue(result.isError)
                    group.cancel_scope.cancel()

        with tempfile.TemporaryDirectory() as temp:
            asyncio.run(exercise(Path(temp).resolve() / "log"))

    def test_cancellation_is_recorded_and_next_call_still_works(self):
        from mcp import types
        from mcp.shared.exceptions import McpError

        module = self.module()

        async def exercise(log):
            with module.Probe(log) as probe:
                send, reader = anyio.create_memory_object_stream(0)
                output, receive = anyio.create_memory_object_stream(0)
                async with send, reader, output, receive, anyio.create_task_group() as group:
                    group.start_soon(probe.run_transport, reader, output)
                    async with ClientSession(receive, send) as session:
                        await session.initialize()
                        call = asyncio.create_task(
                            session.call_tool("probe_delay", {"nonce": "cancel_me", "seconds": 30})
                        )
                        with anyio.fail_after(2):
                            while True:
                                events = [json.loads(line) for line in log.read_text().splitlines()]
                                called = [e for e in events if e["event"] == "called"]
                                if called:
                                    break
                                await anyio.sleep(0.005)
                            await session.send_notification(
                                types.ClientNotification(
                                    types.CancelledNotification(
                                        method="notifications/cancelled",
                                        params=types.CancelledNotificationParams(
                                            requestId=called[-1]["request_id"],
                                            reason="synthetic stop",
                                        ),
                                    )
                                )
                            )
                            while not any(
                                json.loads(line)["event"] == "cancelled"
                                for line in log.read_text().splitlines()
                            ):
                                await anyio.sleep(0.005)
                        with self.assertRaisesRegex(McpError, "Request cancelled"):
                            await call
                        result = await session.call_tool("probe_echo", {"nonce": "after_cancel"})
                        self.assertFalse(result.isError)
                    group.cancel_scope.cancel()

        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp).resolve() / "log"
            asyncio.run(exercise(log))
            events = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertTrue(any(e["event"] == "cancel_notification" for e in events))
            self.assertFalse(
                any(e["event"] == "completed" and e.get("nonce") == "cancel_me" for e in events)
            )

    def test_cli_preserves_synthetic_form_values_and_starts_stdio(self):
        import contextlib
        import runpy
        import sys

        module = self.module()

        async def exercise(args):
            send, reader = anyio.create_memory_object_stream(0)
            output, receive = anyio.create_memory_object_stream(0)

            @contextlib.asynccontextmanager
            async def transport():
                yield reader, output

            with patch.object(module, "stdio_server", transport):
                async with send, reader, output, receive, anyio.create_task_group() as group:
                    group.start_soon(module.serve, args)
                    async with ClientSession(receive, send) as session:
                        await session.initialize()
                        self.assertFalse(
                            (await session.call_tool("probe_echo", {"nonce": "stdio"})).isError
                        )
                    group.cancel_scope.cancel()

        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp).resolve() / "log"
            with (
                patch.object(
                    module.subprocess, "check_output", side_effect=OSError("ps unavailable")
                ),
                patch.object(
                    module.anyio, "run", side_effect=lambda fn, args: asyncio.run(exercise(args))
                ),
            ):
                module.main(
                    ["--log", str(log), "--input-root", "/synthetic only", "--ocr", "false"]
                )
            started = json.loads(log.read_text().splitlines()[0])
            self.assertEqual(
                started["setup"], {"input_root": "/synthetic only", "ocr_argument": "false"}
            )
            self.assertIsNone(started["parent_command"])
            with (
                patch.object(module.anyio, "run") as run,
                patch.object(sys, "argv", ["host_probe.py", "--log", str(log)]),
            ):
                runpy.run_path(str(Path(module.__file__)), run_name="__main__")
            self.assertEqual(run.call_args.args[1].log, log)
        with self.assertRaises(ValueError):
            module.Probe(Path("relative"))
        with self.assertRaises(ValueError):
            module.bounded_seconds(float("inf"), 30)
