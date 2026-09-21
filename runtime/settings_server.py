"""Expose a separate no-argument settings opener without altering Core's tool catalog.

Only the native window supplies configuration values. Opening acknowledges process launch,
not visibility or saved changes. The child has no MCP stdout and survives chat disconnects.
A live child is reused; closing it allows the next request to start a fresh window.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from runtime.configuration import CLIENTS


class WindowOpener:
    def __init__(self, client):
        if client not in CLIENTS:
            raise ValueError("Unknown client.")
        self.client, self.child = client, None

    def open(self, arguments):
        if arguments:
            raise ValueError("OpenReading Settings accepts no configuration arguments.")
        if self.child is None or self.child.poll() is not None:
            command = [sys.executable]
            if not getattr(sys, "frozen", False):
                command += ["-m", "runtime.settings_server"]
            command += ["--client", self.client, "--destination-settings"]
            self.child = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        return {
            "status": "window_requested",
            "message": "Use the OpenReading Settings window to review and save changes.",
        }


def create_server(client):
    server = Server("openreading-settings")
    opener = WindowOpener(client)

    @server.list_tools()
    async def list_tools():
        return [
            types.Tool(
                name="openreading_open_settings",
                description="Open the native OpenReading Settings window for storage, processing destination, credentials and delivery preferences. The user reviews and saves values locally.",
                inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
                annotations=types.ToolAnnotations(
                    readOnlyHint=False, destructiveHint=False, openWorldHint=False
                ),
            )
        ]

    @server.call_tool()
    async def call_tool(name, arguments):
        if name != "openreading_open_settings":
            raise ValueError("Unknown settings tool.")
        try:
            result = opener.open(arguments)
        except OSError:
            raise ValueError(
                "Cannot open OpenReading Settings. Reconnect the plugin and retry."
            ) from None
        return [types.TextContent(type="text", text=json.dumps(result))]

    return server


async def serve(client):
    server = create_server(client)
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True, choices=sorted(CLIENTS))
    parser.add_argument("--destination-settings", action="store_true")
    args = parser.parse_args()
    if args.destination_settings:
        from runtime.destination_ui import run

        return run(args.client)
    asyncio.run(serve(args.client))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
