"""Prepare synthetic local MCP host experiments without parsing documents or calling models.

Run with the locked runtime interpreter: python -m scripts.host_probe --log ABSOLUTE_NEW_FILE.
The log records synthetic nonces, timing, process identity, cancellation, and setup arguments.
It never records environment values. Existing log files are refused instead of overwritten.
No host configuration is modified. Native registration and model requests are separate steps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server


def bounded_seconds(value, maximum):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= maximum:
        raise ValueError("Probe delay is outside its finite bounds.")
    return value


class Probe:
    def __init__(self, log: Path, *, startup_delay=0, setup=None):
        self.startup_delay = bounded_seconds(startup_delay, 30)
        if not log.is_absolute():
            raise ValueError("Choose an absolute new probe log path.")
        self.stream = os.fdopen(
            os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600), "w"
        )
        self.server = Server("openreading-host-probe", version="0.1.0")
        try:
            parent = subprocess.check_output(
                ["/bin/ps", "-p", str(os.getppid()), "-o", "comm="], text=True, timeout=5
            ).strip()
        except (OSError, subprocess.SubprocessError):
            parent = None
        self.record(
            "started",
            parent_pid=os.getppid(),
            parent_command=parent,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            cwd=str(Path.cwd()),
            environment_names=sorted(os.environ),
            setup=setup,
        )

        @self.server.list_tools()
        async def list_tools():
            self.record("tools_listed")
            nonce = {"type": "string", "pattern": "^[A-Za-z0-9_-]{1,64}$"}
            return [
                types.Tool(
                    name="probe_echo",
                    description="Echo a synthetic nonce without reading files.",
                    inputSchema={
                        "type": "object",
                        "properties": {"nonce": nonce},
                        "required": ["nonce"],
                        "additionalProperties": False,
                    },
                    annotations=types.ToolAnnotations(readOnlyHint=True),
                ),
                types.Tool(
                    name="probe_delay",
                    description="Wait a bounded interval to measure host timeout and cancellation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "nonce": nonce,
                            "seconds": {"type": "number", "minimum": 0, "maximum": 330},
                            "progress_every": {
                                "anyOf": [
                                    {"const": 0},
                                    {"type": "number", "minimum": 0.01, "maximum": 60},
                                ]
                            },
                        },
                        "required": ["nonce", "seconds"],
                        "additionalProperties": False,
                    },
                    annotations=types.ToolAnnotations(readOnlyHint=False),
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name, arguments):
            context = self.server.request_context
            nonce = arguments["nonce"]
            self.record("called", tool=name, nonce=nonce, request_id=context.request_id)
            try:
                if name == "probe_delay":
                    seconds = bounded_seconds(arguments["seconds"], 330)
                    every = bounded_seconds(arguments.get("progress_every", 0), 60)
                    token = context.meta.progressToken if context.meta else None
                    deadline = time.monotonic() + seconds
                    count = 0
                    while (remaining := deadline - time.monotonic()) > 0:
                        await anyio.sleep(min(remaining, every) if every else remaining)
                        if every and token is not None:
                            count += 1
                            await context.session.send_progress_notification(
                                token, count, message="Synthetic delay is still running."
                            )
                            self.record("progress", nonce=nonce, progress=count)
                self.record("completed", nonce=nonce)
                return [types.TextContent(type="text", text=json.dumps({"nonce": nonce}))]
            except anyio.get_cancelled_exc_class():
                self.record("cancelled", nonce=nonce)
                raise

    def record(self, event, **values):
        self.stream.write(
            json.dumps(
                {
                    "event": event,
                    "pid": os.getpid(),
                    "monotonic_seconds": time.monotonic(),
                    **values,
                },
                allow_nan=False,
            )
            + "\n"
        )
        self.stream.flush()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    async def run_transport(self, reader, writer):
        forward, incoming = anyio.create_memory_object_stream(0)

        async def relay():
            async with forward:
                async for message in reader:
                    if not isinstance(message, Exception):
                        value = message.message.root
                        method = getattr(value, "method", None)
                        if method == "initialize":
                            self.record("initialize_received")
                            await anyio.sleep(self.startup_delay)
                            self.record("initialization_released")
                        elif method == "notifications/cancelled":
                            self.record(
                                "cancel_notification",
                                request_id=(value.params or {}).get("requestId"),
                            )
                    await forward.send(message)

        async with incoming, anyio.create_task_group() as group:
            group.start_soon(relay)
            await self.server.run(incoming, writer, self.server.create_initialization_options())
            group.cancel_scope.cancel()


async def serve(args):
    with Probe(
        args.log,
        startup_delay=args.startup_delay,
        setup={"input_root": args.input_root, "ocr_argument": args.ocr},
    ) as probe:
        async with stdio_server() as (reader, writer):
            await probe.run_transport(reader, writer)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True, help="absolute new private JSONL log")
    parser.add_argument(
        "--startup-delay", type=float, default=0, help="initialization delay, 0 to 30 seconds"
    )
    parser.add_argument(
        "--input-root", help="record a synthetic form argument; never read this directory"
    )
    parser.add_argument("--ocr", help="record the exact form substitution without enabling OCR")
    args = parser.parse_args(argv)
    anyio.run(serve, args)


if __name__ == "__main__":
    main()
