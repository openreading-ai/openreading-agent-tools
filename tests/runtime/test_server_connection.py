"""Connection checks use bounded metadata GETs and never upload or probe providers."""

import unittest

import httpx

from runtime import server_transport


class ConnectionTests(unittest.IsolatedAsyncioTestCase):
    async def check(self, handler):
        self.assertTrue(
            hasattr(server_transport, "check_connection"), "Missing metadata-only connection check"
        )
        return await server_transport.check_connection(
            server_transport.ServerDestination("http://localhost:8787/core", "r"),
            transport=httpx.MockTransport(handler),
        )

    async def test_connection_uses_metadata_only_without_authorization(self):
        seen = []

        def handle(request):
            seen.append(request.url.path)
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.content, b"")
            if request.url.path.endswith("healthz"):
                self.assertNotIn("authorization", request.headers)
                return httpx.Response(200, json={"status": "ok", "version": "0.3.0"})
            self.assertNotIn("authorization", request.headers)
            return httpx.Response(200, json=[{"slug": "pymupdf", "ready": True}])

        result = await self.check(handle)
        self.assertEqual(seen, ["/core/healthz", "/core/v1/backends"])
        self.assertEqual(result, {"version": "0.3.0", "backend_count": 1})

    async def test_anonymous_metadata_check_and_fail_closed_responses(self):
        for stage in ("healthz", "backends"):
            for status, body in (
                (302, b"secret"),
                (401, b"secret"),
                (200, b"{}"),
                (200, b"x" * 1048577),
                (200, b'{"status":"ok","status":"ok"}'),
            ):
                calls = []

                def handle(request, calls=calls, stage=stage, status=status, body=body):
                    calls.append(request)
                    self.assertNotIn("authorization", request.headers)
                    if request.url.path.endswith(stage):
                        return httpx.Response(
                            status, content=body, headers={"location": "https://other.invalid"}
                        )
                    return httpx.Response(200, json={"status": "ok", "version": "0.3.0"})

                with self.subTest(stage=stage, status=status, size=len(body)):
                    with self.assertRaises(server_transport.DestinationError) as caught:
                        await self.check(handle)
                    self.assertNotIn("secret", str(caught.exception))
                    self.assertFalse(caught.exception.submitted)
                    self.assertEqual(len(calls), 1 if stage == "healthz" else 2)

    async def test_network_failures_are_sanitized(self):
        def fail(request):
            raise httpx.ReadTimeout("private connection detail")

        with self.assertRaisesRegex(server_transport.DestinationError, "connection"):
            await self.check(fail)
