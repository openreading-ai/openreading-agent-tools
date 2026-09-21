"""Download a pinned runtime while Claude can discover its document and settings tools.

The native plugin contains this frozen stdlib-only launcher and verified local/server catalogs.
Both connectors share an exclusive download lock and an immutable Application Support cache.
HTTPS archive and worker digests bind the payload before extraction and execution.
Runtime installation preserves all user settings, documents and Keychain entries.
No document reaches the download endpoint. Warm launches require no network.
An early tool call reports setup progress; retrying after setup forwards to the real worker.
The proxy preserves asynchronous worker replies and cancellation notifications after setup.
Before startup, discovery uses conservative combined descriptions and upload annotations.
Once verified, discovery exposes the active profile verbatim and notifies previous callers.
Document sessions bind the saved destination at startup. A later save blocks new selections
and imports until reconnect, including local sessions that otherwise retain bundled Docling.
Already admitted jobs, cancellation and retained-result retrieval remain available.
The temporary ngrok origin is a development route, not a released download service.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import ssl
import subprocess
import sys
import tarfile
import tempfile
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from runtime.verify import verify_release


class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https":
            raise ValueError("Runtime download redirects must use HTTPS.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_download(url):
    if urlsplit(url).scheme != "https" or not urlsplit(url).hostname:
        raise ValueError("Runtime download requires HTTPS.")
    # macOS supplies the trust bundle, so the installer needs no Python certificate package.
    context = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    opener = urllib.request.build_opener(
        HTTPSRedirect(), urllib.request.HTTPSHandler(context=context)
    )
    return opener.open(
        urllib.request.Request(
            url,
            headers={"User-Agent": "OpenReading-bootstrap/0.2", "ngrok-skip-browser-warning": "1"},
        ),
        timeout=30,
    )


def install(config, home, progress=lambda message: None):
    home = home.resolve()
    expected = config["worker_sha256"]
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("Invalid runtime digest.")
    base = home / "Library/Application Support/OpenReading/agent-tools/runtime-cache"
    for parent in [*reversed(base.parents), base]:
        if parent.is_symlink():
            raise ValueError("Runtime cache cannot use symbolic-link directories.")
    base.mkdir(parents=True, exist_ok=True)
    target = base / expected
    lockpath = base / (expected + ".lock")
    fd = os.open(lockpath, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        progress("Preparing OpenReading. Another connector may be downloading the runtime.")
        fcntl.flock(lock, fcntl.LOCK_EX)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or verify_release(target)["worker_sha256"] != expected:
                raise ValueError("Cached runtime verification failed.")
            return target
        with tempfile.TemporaryDirectory(prefix=".download-", dir=base) as temp:
            stage = Path(temp)
            archive = stage / "runtime.tar.gz"
            digest = hashlib.sha256()
            size = 0
            with open_download(config["url"]) as response, archive.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > config["archive_bytes"]:
                        raise ValueError("Runtime download exceeds its pinned size.")
                    output.write(chunk)
                    digest.update(chunk)
                    progress(
                        f"Downloading OpenReading runtime: {size * 100 // config['archive_bytes']}%. Retry this tool when setup finishes."
                    )
            if size != config["archive_bytes"] or digest.hexdigest() != config["archive_sha256"]:
                raise ValueError("Runtime download checksum failed.")
            progress("Verifying and unpacking OpenReading. Retry this tool when setup finishes.")
            with tarfile.open(archive, "r:gz") as payload:
                payload.extractall(stage / "unpacked", filter="data")
            unpacked = stage / "unpacked/runtime"
            if verify_release(unpacked)["worker_sha256"] != expected:
                raise ValueError("Downloaded worker verification failed.")
            unpacked.rename(target)
    return target


class Manager:
    def __init__(self, config, home):
        self.config, self.home = config, home
        self.root = None
        self.status = "Downloading OpenReading runtime. Retry this tool when setup finishes."
        self.thread = None

    def start(self):
        if self.root is None and (self.thread is None or not self.thread.is_alive()):
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def run(self):
        try:
            self.root = install(self.config, self.home, self.progress)
            self.status = "OpenReading is ready."
        except (OSError, ValueError, tarfile.TarError) as error:
            self.status = f"OpenReading setup failed: {error}. Retry the tool to retry setup."

    def progress(self, message):
        self.status = message


DESTINATION_CHANGED = (
    "OpenReading processing settings changed or cannot be read. "
    "Reconnect the OpenReading document connector before selecting or importing documents. "
    "This request did not select or process any documents. Existing jobs keep their original destination."
)


def destination_stamp(home):
    """Compare saved bytes without importing the runtime or exposing credential references."""
    path = home / (
        "Library/Application Support/OpenReading/agent-tools/claude-desktop/destination.json"
    )
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
    stamp = destination_stamp(manager.home) if mode == "--chat-documents" else None
    child = subprocess.Popen(
        [str(manager.root / "openreading-worker"), "--client", "claude-desktop", mode],
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
                reply = json.loads(child.stdout.readline())
                if "error" in reply or reply.get("id") != request["id"]:
                    raise ValueError("Runtime initialization failed.")
        allowed = manager.config.get("catalog_variants", {}).get(
            mode, [manager.config["catalogs"][mode]]
        )
        if reply.get("result") not in allowed:
            raise ValueError("Runtime tool catalog differs from the installed plugin.")
        if mode == "--chat-documents" and destination_stamp(manager.home) != stamp:
            raise ValueError(DESTINATION_CHANGED)
        child.destination_stamp = stamp
        child.catalog = reply["result"]
        return child
    except (OSError, ValueError):
        child.terminate()
        child.wait()
        child.stdin.close()
        child.stdout.close()
        raise


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
                        "message": "OpenReading worker stopped. Reconnect its connector.",
                    },
                }
            )
        pending.clear()

    def connect():
        nonlocal child, reader, advertised
        if child is None and manager.root is not None:
            try:
                child = start_worker(manager, mode, protocol)
                reader = threading.Thread(target=read_worker, daemon=True)
                reader.start()
                changed = advertised != child.catalog
                advertised = child.catalog
                if changed and catalog_sent:
                    send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            except (OSError, ValueError) as error:
                manager.status = f"OpenReading could not start: {error}. Retry this tool."

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
                    "serverInfo": {"name": "openreading-bootstrap", "version": "0.2.0-alpha.12"},
                }
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
                ):
                    try:
                        current = destination_stamp(manager.home) == child.destination_stamp
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
                                    "message": "OpenReading worker stopped. Reconnect its connector.",
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


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise ValueError("This plugin requires macOS on Apple Silicon.")
    config = json.loads(Path(argv[0]).read_text())
    if argv[1] not in config["catalogs"]:
        raise ValueError("Unknown OpenReading connector.")
    serve(Manager(config, Path.home()), argv[1], sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
