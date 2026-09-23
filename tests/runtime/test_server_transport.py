"""Server destination transport uses only explicit synthetic offline HTTP exchanges."""

import asyncio
import hashlib
import tempfile
import threading
import unittest
from pathlib import Path

import httpx

from runtime.server_transport import DestinationError, ServerDestination, parse_document


class ServerTransportTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name) / "report.md"
        self.source.write_bytes("synthetic 界".encode())
        self.response = {
            "status": {"state": "succeeded"},
            "document": {"text": "synthetic"},
        }
        self.destination = ServerDestination("http://127.0.0.1:8787/prefix", "revision-1")

    async def test_multipart_preserves_bytes_prefix_and_null_backend(self):
        seen = []

        async def handle(request):
            seen.append(request)
            payload = await request.aread()
            self.assertIn(self.source.read_bytes(), payload)
            self.assertIn(b'name="request"\r\n\r\n{"backend":{"id":null}}', payload)
            self.assertIn(b'filename="report.md"', payload)
            self.assertNotIn(str(self.source.parent).encode(), payload)
            self.assertEqual(request.url.path, "/prefix/v1/parse")
            self.assertNotIn("authorization", request.headers)
            return httpx.Response(200, json=self.response)

        result = await parse_document(
            self.destination,
            self.source,
            transport=httpx.MockTransport(handle),
        )
        self.assertEqual(result.response, self.response)
        self.assertEqual(result.source_sha256, hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(len(seen), 1)

    async def test_redirect_auth_and_gateway_errors_never_retry(self):
        for status in (301, 307, 401, 403, 404, 413, 422, 429, 500, 502, 503):
            with self.subTest(status=status):
                requests = []

                def handle(request, requests=requests, status=status):
                    requests.append(request)
                    return httpx.Response(
                        status,
                        text="private proxy diagnostics",
                        headers={"location": "https://elsewhere.invalid"},
                    )

                with self.assertRaises(DestinationError) as caught:
                    await parse_document(
                        self.destination,
                        self.source,
                        transport=httpx.MockTransport(handle),
                    )
                self.assertEqual(caught.exception.http_status, status)
                self.assertNotIn("private", str(caught.exception))
                self.assertEqual(len(requests), 1)
                self.assertTrue(caught.exception.submitted)
                self.assertEqual(caught.exception.shared_failure, status not in (413, 422))

    async def test_invalid_json_is_explicit(self):
        for body in (
            b'{"a":1,"a":2}',
            b'{"a":NaN}',
            b'{"a":Infinity}',
            b'{"a":1e999}',
            b"[]",
            b"not json",
            b'{"a":"\xff"}',
            b"[" * 70 + b"0" + b"]" * 70,
        ):
            with self.subTest(body=body):
                with self.assertRaisesRegex(DestinationError, "valid normalized JSON"):
                    await parse_document(
                        self.destination,
                        self.source,
                        transport=httpx.MockTransport(
                            lambda _, body=body: httpx.Response(200, content=body)
                        ),
                    )

    async def test_nested_strings_and_explicit_null_survive(self):
        value = {"future": {"brackets": '[ { \\"', "empty": None}}
        result = await parse_document(
            self.destination,
            self.source,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=value)),
        )
        self.assertEqual(result.response, value)

    async def test_response_limit_is_not_truncation(self):
        destination = ServerDestination(self.destination.base_url, "r", response_bytes=16)
        with self.assertRaisesRegex(DestinationError, "response limit"):
            await parse_document(
                destination,
                self.source,
                transport=httpx.MockTransport(
                    lambda _: httpx.Response(200, content=b'{"large":"' + b"x" * 50 + b'"}')
                ),
            )

    async def test_connect_failure_and_cancel_before_submit(self):
        calls = []

        def fail(request):
            calls.append(request)
            raise httpx.ConnectError("secret transport message")

        with self.assertRaisesRegex(DestinationError, "connection failed"):
            await parse_document(self.destination, self.source, transport=httpx.MockTransport(fail))
        self.assertEqual(len(calls), 1)
        cancelled = threading.Event()
        cancelled.set()
        with self.assertRaises(DestinationError) as caught:
            await parse_document(
                self.destination,
                self.source,
                cancelled=cancelled,
                transport=httpx.MockTransport(fail),
            )
        self.assertFalse(caught.exception.submitted)
        self.assertEqual(len(calls), 1)

    async def test_cancel_while_waiting_stops_local_request(self):
        entered = asyncio.Event()
        cancelled = threading.Event()

        async def wait(request):
            entered.set()
            await asyncio.sleep(30)
            return httpx.Response(200, json={})

        task = asyncio.create_task(
            parse_document(
                self.destination,
                self.source,
                cancelled=cancelled,
                transport=httpx.MockTransport(wait),
            )
        )
        await entered.wait()
        cancelled.set()
        with self.assertRaises(DestinationError) as caught:
            await asyncio.wait_for(task, 2)
        self.assertTrue(caught.exception.submitted)
        self.assertIn("may continue", str(caught.exception))

    async def test_progress_and_preflight_limits(self):
        from unittest.mock import patch

        stages = []
        result = await parse_document(
            self.destination,
            self.source,
            progress=stages.append,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=self.response)),
        )
        self.assertEqual(stages, ["uploading", "waiting", "receiving"])
        self.assertEqual(len(result.request_sha256), 64)
        with patch("runtime.server_transport.UPLOAD_BYTES", 1):
            with self.assertRaises(DestinationError) as caught:
                await parse_document(self.destination, self.source)
            self.assertFalse(caught.exception.submitted)
            self.assertFalse(caught.exception.shared_failure)

    async def test_file_growth_cannot_exceed_upload_limit(self):
        from unittest.mock import patch

        self.source.write_bytes(b"x")

        def progress(stage):
            if stage == "uploading":
                self.source.write_bytes(b"xxxx")

        with patch("runtime.server_transport.UPLOAD_BYTES", 2):
            with self.assertRaises(DestinationError) as caught:
                await parse_document(
                    self.destination,
                    self.source,
                    progress=progress,
                    transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
                )
        self.assertTrue(caught.exception.submitted)
        self.assertFalse(caught.exception.shared_failure)

    async def test_write_timeout_does_not_retry(self):
        calls = []

        def fail(request):
            calls.append(request)
            raise httpx.WriteTimeout("private diagnostics")

        with self.assertRaisesRegex(DestinationError, "no retry"):
            await parse_document(self.destination, self.source, transport=httpx.MockTransport(fail))
        self.assertEqual(len(calls), 1)

    async def test_unexpected_failure_does_not_become_success(self):
        async def fail(request):
            raise RuntimeError("synthetic unexpected failure")

        with self.assertRaises(ExceptionGroup):
            await parse_document(self.destination, self.source, transport=httpx.MockTransport(fail))

    def test_settings_validate_limits_and_port(self):
        for kwargs in (
            {"response_bytes": 0},
            {"response_bytes": True},
            {"revision": ""},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ServerDestination("https://example.invalid", **({"revision": "r"} | kwargs))
        for url in (
            "https://example.invalid:0",
            "https://example.invalid:65536",
            "https://example.invalid?",
            "https://example.invalid#",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                ServerDestination(url, "r")
        self.assertEqual(
            ServerDestination("https://example.invalid/core/", "r").base_url,
            "https://example.invalid/core",
        )

    def test_settings_reject_unsafe_or_ambiguous_urls(self):
        for url in (
            "http://remote.invalid",
            "ftp://localhost",
            "https://user:pass@host",
            "https://host?key=secret",
            "https://host/#part",
            "https://host/../other",
            "http://localhost.evil",
            "http://127.0.0.1\\@evil",
            "https://host/%2e%2e/private",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                ServerDestination(url, "r")
        for url in (
            "http://localhost:8787",
            "http://[::1]:8787",
            "https://example.invalid/core",
        ):
            self.assertEqual(ServerDestination(url, "r").base_url, url)


if __name__ == "__main__":
    unittest.main()


class GrantedDescriptorTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_uses_already_granted_descriptor_not_replaced_path(self):
        import inspect

        self.assertIn("source_fd", inspect.signature(parse_document).parameters)
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "selected.pdf"
            source.write_bytes(b"approved bytes")
            with source.open("rb") as granted:
                source.unlink()
                source.write_bytes(b"unapproved replacement")

                async def handle(request):
                    body = await request.aread()
                    self.assertIn(b"approved bytes", body)
                    self.assertNotIn(b"unapproved replacement", body)
                    return httpx.Response(200, json={})

                result = await parse_document(
                    ServerDestination("http://localhost", "r"),
                    source,
                    source_fd=granted.fileno(),
                    transport=httpx.MockTransport(handle),
                )
                self.assertEqual(
                    result.source_sha256, hashlib.sha256(b"approved bytes").hexdigest()
                )
                self.assertFalse(granted.closed)

    async def test_progress_observer_failure_cannot_abort_a_transfer(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "synthetic.pdf"
            source.write_bytes(b"synthetic")

            def broken(stage):
                raise RuntimeError("observer unavailable")

            result = await parse_document(
                ServerDestination("http://localhost", "r"),
                source,
                progress=broken,
                transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"ok": True})),
            )
            self.assertEqual(result.response, {"ok": True})
