"""Proxy verified local MCP workers without downloading or installing a runtime.

The installed package supplies its fixed worker manager and reviewed tool catalogs.
Packaged Core instructions reach the host before setup. Live initialization must match
them exactly, so a changed worker cannot silently weaken the advertised safety guidance.
Destination changes block new selection and submission while existing job queries remain available.
Current children report startup failures through fixed exit statuses, never arbitrary stderr.
Historical workers keep their command line and receive no private startup-status flag.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading

DESTINATION_CHANGED = (
    "OpenReading processing settings changed or cannot be read. "
    "Quit and reopen your app, then open the OpenReading file picker before importing documents. "
    "This request did not select or process any documents. Existing jobs keep their original destination."
)

STARTUP_MESSAGES = {
    70: "OpenReading could not start. Quit and reopen your app. If this persists, report the plugin version to the maintainer.",
    71: "OpenReading processing settings are unavailable. Open OpenReading Settings and save your Core server URL before selecting or processing documents.",
    72: "OpenReading storage is unavailable or a move is blocked. Open OpenReading Settings and review Storage. Keep the current data folder; finish existing imports and close other document connections before retrying.",
    73: "OpenReading could not verify the installed runtime. Reinstall the reviewed plugin from its GitHub marketplace; do not bypass integrity checks.",
}


class StartupFailure(ValueError):
    """Carry only a fixed startup category, not paths or child-provided error text."""

    def __init__(self, code=70):
        self.code = code if type(code) is int and code in STARTUP_MESSAGES else 70
        super().__init__(STARTUP_MESSAGES[self.code])


def destination_stamp(home, client="claude-desktop"):
    """Compare saved bytes without importing the runtime or exposing credential references."""
    path = home / (f"Library/Application Support/OpenReading/agent-tools/{client}/destination.json")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as stream:
        data = stream.read(16385)
    if len(data) > 16384:
        raise ValueError("Oversized destination settings.")
    return hashlib.sha256(data).digest()


def start_worker(manager, mode, protocol):
    client = getattr(manager, "client", "claude-desktop")
    stamp = destination_stamp(manager.home, client) if mode == "--chat-documents" else None
    startup_status = getattr(manager, "startup_status", False) is True
    command = [str(manager.root / "openreading-worker"), "--client", client, mode]
    if startup_status:
        command.append("--internal-startup-status")
    child = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=manager.home,
    )
    try:
        for request in [
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": protocol,
                    "capabilities": {},
                    "clientInfo": {"name": "openreading-bootstrap", "version": "0.2"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        ]:
            child.stdin.write(json.dumps(request) + "\n")
            child.stdin.flush()
            if "id" in request:
                line = child.stdout.readline()
                if not line and startup_status:
                    raise StartupFailure(child.wait(timeout=5))
                reply = json.loads(line)
                if (
                    not isinstance(reply, dict)
                    or "error" in reply
                    or reply.get("id") != request["id"]
                ):
                    raise ValueError("Runtime initialization failed.")
                if request["method"] == "initialize" and "instructions" in manager.config:
                    result = reply.get("result")
                    if (
                        not isinstance(result, dict)
                        or result.get("instructions") != manager.config["instructions"][mode]
                    ):
                        raise ValueError("Runtime instructions differ from the installed plugin.")
        allowed = manager.config.get("catalog_variants", {}).get(
            mode, [manager.config["catalogs"][mode]]
        )
        if reply.get("result") not in allowed:
            raise ValueError("Runtime tool catalog differs from the installed plugin.")
        if mode == "--chat-documents" and destination_stamp(manager.home, client) != stamp:
            raise ValueError(DESTINATION_CHANGED)
        child.destination_stamp = stamp
        child.catalog = reply["result"]
        return child
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        if startup_status and isinstance(error, BrokenPipeError):
            try:
                error = StartupFailure(child.wait(timeout=5))
            except subprocess.TimeoutExpired:
                error = StartupFailure()
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        try:
            child.stdin.close()
        except BrokenPipeError:
            pass
        child.stdout.close()
        raise error from None


def serve(manager, mode, incoming, outgoing):
    manager.start()
    child = None
    reader = None
    protocol = "2025-11-25"
    output_lock = threading.Lock()
    pending = set()
    advertised = manager.config["catalogs"][mode]
    catalog_sent = False

    def send(message):
        with output_lock:
            outgoing.write(json.dumps(message) + "\n")
            outgoing.flush()

    def read_worker():
        for line in child.stdout:
            message = json.loads(line)
            pending.discard(message.get("id"))
            send(message)
        for identifier in list(pending):
            send(
                {
                    "jsonrpc": "2.0",
                    "id": identifier,
                    "error": {
                        "code": -32603,
                        "message": "OpenReading worker stopped. Quit and reopen your app to retry.",
                    },
                }
            )
        pending.clear()

    def connect():
        nonlocal child, reader, advertised
        manager.start()
        if child is None and manager.root is not None:
            try:
                child = start_worker(manager, mode, protocol)
                reader = threading.Thread(target=read_worker, daemon=True)
                reader.start()
                changed = advertised != child.catalog
                advertised = child.catalog
                if changed and catalog_sent:
                    send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                manager.status = (
                    str(error) if isinstance(error, StartupFailure) else STARTUP_MESSAGES[70]
                )

    try:
        for line in incoming:
            try:
                request = json.loads(line)
                method = request["method"]
                identifier = request.get("id")
            except (ValueError, KeyError, TypeError):
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Invalid MCP request."},
                    }
                )
                continue
            if method == "initialize":
                protocol = request.get("params", {}).get("protocolVersion", protocol)
                result = {
                    "protocolVersion": protocol,
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": getattr(
                        manager,
                        "server_info",
                        {"name": "openreading-bootstrap", "version": "0.2.0-alpha.12"},
                    ),
                }
                instructions = manager.config.get("instructions", {}).get(mode)
                if instructions is not None:
                    result["instructions"] = instructions
            elif method == "tools/list":
                connect()
                result = advertised
                catalog_sent = True
            elif method == "ping":
                result = {}
            elif method == "tools/call" and child is None:
                connect()
                if child is None:
                    result = {
                        "isError": True,
                        "content": [{"type": "text", "text": manager.status}],
                    }
                    manager.start()
            elif child is None and identifier is None:
                continue
            elif child is None:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": identifier,
                        "error": {"code": -32601, "message": "Method not found."},
                    }
                )
                continue
            if child is not None and method not in ("initialize", "tools/list", "ping"):
                if (
                    mode == "--chat-documents"
                    and method == "tools/call"
                    and request.get("params", {}).get("name")
                    in {
                        "openreading_select_document",
                        "openreading_import",
                        "openreading_start_import",
                    }
                    | {
                        tool["name"]
                        for tool in advertised["tools"]
                        # Only the verified catalog supplies hints, never a tool result.
                        # Missing hints are conservative for future upload-capable tools.
                        if tool.get("annotations", {}).get("openWorldHint", True) is not False
                    }
                ):
                    try:
                        current = (
                            destination_stamp(
                                manager.home, getattr(manager, "client", "claude-desktop")
                            )
                            == child.destination_stamp
                        )
                    except (OSError, ValueError):
                        current = False
                    if not current:
                        send(
                            {
                                "jsonrpc": "2.0",
                                "id": identifier,
                                "result": {
                                    "isError": True,
                                    "content": [{"type": "text", "text": DESTINATION_CHANGED}],
                                },
                            }
                        )
                        continue
                if identifier is not None:
                    pending.add(identifier)
                try:
                    child.stdin.write(line)
                    child.stdin.flush()
                except BrokenPipeError:
                    if identifier is not None:
                        pending.discard(identifier)
                        send(
                            {
                                "jsonrpc": "2.0",
                                "id": identifier,
                                "error": {
                                    "code": -32603,
                                    "message": "OpenReading worker stopped. Quit and reopen your app to retry.",
                                },
                            }
                        )
            elif identifier is not None:
                send({"jsonrpc": "2.0", "id": identifier, "result": result})
    finally:
        if child is not None:
            try:
                child.stdin.close()
            except BrokenPipeError:
                pass
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.terminate()
                child.wait()
            if reader is not None:
                reader.join(timeout=2)
            child.stdout.close()
