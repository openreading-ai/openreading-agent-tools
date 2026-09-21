"""Upload one selected snapshot to an operator-run Core server without parse retries.

The trusted launcher supplies destination settings and an optional existing bearer token.
Tools cannot choose URLs, request metadata, headers, credentials, or redirect destinations.
Only loopback permits HTTP. Other destinations require verified HTTPS; upload redirects fail.
The request uses Core's configured default backend or strategy through backend.id=null.

Cancellation stops local transfer and waiting. Submitted server processing may continue.
No failed parse is retried automatically, including gateway failures and read timeouts.
Decoded responses are bounded before JSON parsing. Duplicate keys, nonfinite values, and
excessive nesting fail explicitly. Core retention performs normalized-schema validation.
No provider key, ambient proxy setting, or local Core routing configuration is read here.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

import anyio
import httpx

REQUEST = '{"backend":{"id":null}}'
UPLOAD_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class ServerDestination:
    base_url: str
    revision: str
    response_bytes: int = 256 * 1024 * 1024

    def __post_init__(self):
        url = urlsplit(self.base_url)
        host = url.hostname
        decoded = unquote(url.path)
        if (
            not host
            or url.scheme not in {"http", "https"}
            or url.username is not None
            or url.password is not None
            or url.query
            or url.fragment
            or "?" in self.base_url
            or "#" in self.base_url
            or "\\" in self.base_url
            or any(ord(c) < 33 or ord(c) == 127 for c in self.base_url)
            or any(part in {".", ".."} for part in decoded.split("/"))
            or not self.revision
            or type(self.response_bytes) is not int
            or self.response_bytes <= 0
        ):
            raise ValueError("Configure a server URL without credentials, query, or fragment.")
        if url.port is not None and not 1 <= url.port <= 65535:
            raise ValueError("Configure a valid server port.")
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host.lower() == "localhost"
        if url.scheme == "http" and not loopback:
            raise ValueError("Non-loopback servers require HTTPS.")
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    @property
    def identity(self):
        return hashlib.sha256(self.base_url.encode()).hexdigest()


class DestinationError(ValueError):
    """Expose a fixed diagnostic without copying response bodies or exception strings."""

    def __init__(self, message, *, submitted=False, http_status=None, shared_failure=True):
        super().__init__(message)
        self.submitted = submitted
        self.http_status = http_status
        self.shared_failure = shared_failure


@dataclass(frozen=True)
class ServerResult:
    response: dict
    source_sha256: str
    destination_sha256: str
    request_sha256: str


def notify_progress(callback, stage):
    """Keep an advisory observer failure from changing upload or retention state."""
    if callback is not None:
        try:
            callback(stage)
        except Exception:
            pass


def _decode(payload: bytes, *, max_depth: int = 64) -> dict:
    text = payload.decode("utf-8")
    depth, quoted, escaped = 0, False, False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                raise ValueError("Excessive JSON depth")
        elif character in "]}":
            depth -= 1

    def pairs(entries):
        value = {}
        for key, item in entries:
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value

    def constant(value):
        raise ValueError("Nonfinite JSON number")

    result = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    if not isinstance(result, dict):
        raise ValueError("Response must be an object")
    # Exponents such as 1e999 can overflow without using a JSON nonfinite token.
    json.dumps(result, allow_nan=False)
    return result


async def parse_document(
    destination: ServerDestination,
    source: Path,
    *,
    token: str | None = None,
    cancelled=None,
    progress=None,
    transport=None,
    source_fd: int | None = None,
) -> ServerResult:
    """Send one snapshot once; return decoded values and the actual uploaded-byte digest."""
    submitted = False
    cancelled_here = False
    response = None
    digest = hashlib.sha256()
    count = 0

    def cancellation():
        return cancelled is not None and cancelled.is_set()

    def stage(value):
        notify_progress(progress, value)

    if cancellation():
        raise DestinationError("Cancelled before submission.")
    if token is not None and not re.fullmatch(r"[\x21-\x7e]+", token):
        raise DestinationError("The configured server credential is invalid.")
    headers = {"Authorization": "Bearer " + token} if token else {}
    timeout = httpx.Timeout(connect=10, write=30, read=None, pool=10)
    fd = (
        os.dup(source_fd)
        if source_fd is not None
        else os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    )
    with os.fdopen(fd, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > UPLOAD_BYTES:
            raise DestinationError(
                "The selected file exceeds the server upload limit or is not regular.",
                shared_failure=False,
            )

        class Upload:
            def __getattr__(self, name):
                return getattr(stream, name)

            def read(self, size):
                nonlocal count
                data = stream.read(size)
                count += len(data)
                if count > UPLOAD_BYTES:
                    raise DestinationError(
                        "The selected file exceeds the server upload limit.",
                        submitted=submitted,
                        shared_failure=False,
                    )
                digest.update(data)
                if not data:
                    stage("waiting")
                return data

        try:
            async with (
                httpx.AsyncClient(
                    timeout=timeout,
                    trust_env=False,
                    follow_redirects=False,
                    transport=transport,
                ) as client,
                anyio.create_task_group() as group,
            ):

                async def watch():
                    nonlocal cancelled_here
                    while True:
                        if cancellation():
                            cancelled_here = True
                            group.cancel_scope.cancel()
                            return
                        await anyio.sleep(0.05)

                group.start_soon(watch)
                try:
                    stage("uploading")
                    submitted = True
                    async with client.stream(
                        "POST",
                        destination.base_url + "/v1/parse",
                        headers=headers,
                        data={"request": REQUEST},
                        files={"file": (source.name, Upload(), "application/octet-stream")},
                    ) as received:
                        if received.status_code != 200:
                            raise DestinationError(
                                f"Core server returned HTTP {received.status_code}. Processing may have started; no retry was sent.",
                                submitted=True,
                                http_status=received.status_code,
                                shared_failure=received.status_code not in {413, 422},
                            )
                        stage("receiving")
                        payload = bytearray()
                        async for chunk in received.aiter_bytes(chunk_size=65536):
                            if len(payload) + len(chunk) > destination.response_bytes:
                                raise DestinationError(
                                    "The Core result exceeds the configured response limit.",
                                    submitted=True,
                                )
                            payload.extend(chunk)
                        try:
                            response = _decode(bytes(payload))
                        except (ValueError, UnicodeError, RecursionError):
                            raise DestinationError(
                                "The Core result is not valid normalized JSON.", submitted=True
                            ) from None
                except httpx.HTTPError:
                    raise DestinationError(
                        "The server connection failed. Submitted processing may continue; no retry was sent.",
                        submitted=submitted,
                    ) from None
                finally:
                    group.cancel_scope.cancel()
        except BaseExceptionGroup as errors:
            # TaskGroup wraps the request failure even when its watcher has no error.
            error = errors.exceptions[0]
            if isinstance(error, DestinationError):
                raise error from None
            raise
    if cancelled_here:
        raise DestinationError(
            "Local request cancelled. Server processing may continue.", submitted=submitted
        )
    assert response is not None
    return ServerResult(
        response,
        digest.hexdigest(),
        destination.identity,
        hashlib.sha256(REQUEST.encode()).hexdigest(),
    )


async def check_connection(destination: ServerDestination, *, token=None, transport=None) -> dict:
    """Check HTTP health and authorized metadata without uploading or calling providers.

    Both GETs have a ten-second overall deadline and a one-MiB decoded body limit.
    A passing check proves these endpoints answer, never that document parsing will succeed.
    """
    if token is not None and not re.fullmatch(r"[\x21-\x7e]+", token):
        raise DestinationError("The configured server credential is invalid.")
    headers = {"Authorization": "Bearer " + token} if token else {}
    values = []
    try:
        with anyio.fail_after(10):
            async with httpx.AsyncClient(
                timeout=10, trust_env=False, follow_redirects=False, transport=transport
            ) as client:
                for path in ("/healthz", "/v1/backends"):
                    async with client.stream(
                        "GET",
                        destination.base_url + path,
                        headers=headers if path == "/v1/backends" else {},
                    ) as received:
                        if received.status_code != 200:
                            raise DestinationError(
                                f"Server connection check returned HTTP {received.status_code}.",
                                http_status=received.status_code,
                            )
                        payload = bytearray()
                        async for chunk in received.aiter_bytes(chunk_size=65536):
                            if len(payload) + len(chunk) > 1024 * 1024:
                                raise DestinationError("Server connection metadata is too large.")
                            payload.extend(chunk)
                        try:
                            value = _decode(b'{"value":' + bytes(payload) + b"}")["value"]
                        except (ValueError, UnicodeError, RecursionError):
                            raise DestinationError(
                                "Server connection metadata is invalid."
                            ) from None
                        if path == "/healthz" and (
                            not isinstance(value, dict)
                            or value.get("status") != "ok"
                            or not isinstance(value.get("version"), str)
                            or not value["version"]
                            or len(value["version"]) > 128
                        ):
                            raise DestinationError("Server connection metadata is invalid.")
                        values.append(value)
    except (httpx.HTTPError, TimeoutError):
        raise DestinationError(
            "The server connection check failed. No document was sent."
        ) from None
    health, backends = values
    if not isinstance(backends, list) or any(
        not isinstance(row, dict) or not isinstance(row.get("slug"), str) for row in backends
    ):
        raise DestinationError("Server connection metadata is invalid.")
    return {"version": health["version"], "backend_count": len(backends)}
