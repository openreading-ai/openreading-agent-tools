"""Transfers serialize, consume native approval once, and reuse completed downloads."""

import importlib.util
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
from openreading.artifacts.limits import ArtifactError, ProfileConfig
from openreading.artifacts.models import EngineIdentity

from runtime.destination_settings import save_destination
from runtime.server_selection import ServerSelectionProvider, ServerSelectionStore


class ServerImportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.server_imports"),
            "Missing approved server import service",
        )
        import asyncio

        from runtime.server_imports import ServerArtifactService

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.settings = save_destination(
            "chatgpt", "server", base_url="http://localhost:8787", home=self.home
        )
        self.selection = ServerSelectionStore("chatgpt", home=self.home)
        files = [self.home / "one.custom", self.home / "two.custom"]
        for file in files:
            file.write_bytes(b"synthetic bytes")

        async def choose():
            with (
                patch("runtime.server_selection.choose", AsyncMock(return_value=files)),
                patch("runtime.server_selection.confirm", AsyncMock(return_value=True)),
            ):
                async with ServerSelectionProvider(
                    self.selection, self.settings
                ).select() as selected:
                    return selected["references"]

        self.references = asyncio.run(choose())
        self.config = ProfileConfig(self.selection.grant, self.home / "artifacts")
        self.identity = EngineIdentity(
            core_commit="a" * 40,
            core_version="0.3.0",
            backend_id="external-response",
            backend_version="1",
            extraction_settings={},
        )
        self.requests = []

        self.response = {
            "schema_version": "0.3",
            "status": {"state": "succeeded"},
            "backend": {"id": "synthetic", "type": "oss_library"},
            "document": {"page_count": 1, "text": "preserved"},
        }

        def handle(request):
            self.requests.append(request)
            return httpx.Response(200, json=self.response)

        self.transport = httpx.MockTransport(handle)
        self.service = ServerArtifactService(
            self.config,
            settings=self.settings,
            selection=self.selection,
            identity=self.identity,
            transport=self.transport,
        )
        self.addCleanup(self.service.close)
        self.receipt = object()
        self.retainer = self.enterContext(
            patch.object(self.service, "_retain", return_value=self.receipt)
        )

    def test_approved_upload_and_download_reuse_never_submit_twice(self):
        phases = []
        result = self.service.import_document(self.references[0], progress=phases.append)
        self.assertIs(result, self.receipt)
        self.assertEqual(phases, ["uploading", "waiting", "receiving", "retaining"])
        self.assertEqual(len(self.requests), 1)
        received = self.retainer.call_args.args[1]
        self.assertEqual(received.response, self.response)
        self.assertIs(self.service.import_document(self.references[0]), self.receipt)
        self.assertEqual(len(self.requests), 1)

    def test_retention_failure_can_recover_saved_response_after_restart(self):
        from runtime.server_imports import ServerArtifactService

        self.retainer.side_effect = ArtifactError("storage_limit")
        with self.assertRaises(ArtifactError):
            self.service.import_document(self.references[0])
        self.service.close()
        save_destination("chatgpt", "local", home=self.home)
        restarted = ServerArtifactService(
            self.config,
            settings=self.settings,
            selection=self.selection,
            identity=self.identity,
            transport=self.transport,
        )
        self.addCleanup(restarted.close)
        with patch.object(restarted, "_retain", return_value=self.receipt):
            self.assertIs(restarted.import_document(self.references[0]), self.receipt)
        self.assertEqual(len(self.requests), 1)

    def test_interrupted_submission_is_not_repeated_and_stops_batch(self):
        def fail(request):
            self.requests.append(request)
            raise httpx.ReadTimeout("sensitive error")

        self.service.transport = httpx.MockTransport(fail)
        for reference in (self.references[0], self.references[0], self.references[1]):
            with self.assertRaises(ArtifactError):
                self.service.import_document(reference)
        self.assertEqual(len(self.requests), 1)
        self.retainer.assert_not_called()

    def test_document_rejection_does_not_stop_other_selected_files(self):
        def reject(request):
            self.requests.append(request)
            return httpx.Response(422 if len(self.requests) == 1 else 200, json=self.response)

        self.service.transport = httpx.MockTransport(reject)
        with self.assertRaises(ArtifactError):
            self.service.import_document(self.references[0])
        self.assertIs(self.service.import_document(self.references[1]), self.receipt)
        self.assertEqual(len(self.requests), 2)

    def test_missing_copy_after_approval_does_not_consume_batch_or_submit(self):
        from runtime import server_imports

        original = server_imports.read_approval

        def remove_after_check(*args, **kwargs):
            approval = original(*args, **kwargs)
            (self.selection.grant / self.references[0]).unlink()
            return approval

        with patch.object(server_imports, "read_approval", side_effect=remove_after_check):
            with self.assertRaises(ArtifactError):
                self.service.import_document(self.references[0])
        self.assertEqual(self.requests, [])
        self.assertEqual(list(self.service.transfers.glob("*.active")), [])
        self.assertEqual(list(self.service.transfers.glob("*.attempt")), [])
        self.assertIs(self.service.import_document(self.references[1]), self.receipt)
        self.assertEqual(len(self.requests), 1)

    def test_http_auth_failure_keeps_its_diagnostic_without_claiming_processing(self):
        self.service.transport = httpx.MockTransport(lambda request: httpx.Response(401, json={}))
        with self.assertRaises(ArtifactError) as caught:
            self.service.import_document(self.references[0])
        message = caught.exception.envelope().error.message.lower()
        self.assertIn("http 401", message)
        self.assertNotIn("may have started", message)

    def run_detached_job(self):
        import json

        from openreading.artifacts import jobs
        from openreading.artifacts.jobs import ImportExecution, ImportJobs

        # Only process creation is replaced; the persisted job runner and service remain real.
        process = Mock(pid=999999999)
        with patch.object(jobs.subprocess, "Popen", return_value=process):
            manager = ImportJobs(self.service, execution=ImportExecution(("trusted-worker",), {}))
            initial = manager.start(self.references[0])
        root = manager.root / initial.job_id
        jobs.main([str(root)], service_factory=lambda request: self.service)
        return json.loads((root / "status.json").read_bytes())

    def test_detached_auth_failure_keeps_confirmed_http_diagnostic(self):
        self.service.transport = httpx.MockTransport(lambda request: httpx.Response(401, json={}))
        status = self.run_detached_job()
        self.assertEqual(status["state"], "failed")
        message = status["error"]["message"].lower()
        self.assertIn("http 401", message)
        self.assertNotIn("may continue", message)

    def test_detached_duplicate_is_busy_without_upload_or_extra_job(self):
        from openreading.artifacts import jobs
        from openreading.artifacts.jobs import ImportExecution, ImportJobs

        manager = ImportJobs(self.service, execution=ImportExecution(("trusted-worker",), {}))
        with patch.object(jobs.subprocess, "Popen", return_value=Mock(pid=os.getpid())):
            initial = manager.start(self.references[0])
            with self.assertRaises(ArtifactError) as caught:
                manager.start(self.references[0])
        self.assertEqual(caught.exception.code, "busy")
        self.assertTrue(caught.exception.envelope().error.retryable)
        self.assertEqual([path.name for path in manager.root.iterdir()], [initial.job_id])
        self.assertEqual(self.requests, [])

    def test_detached_retention_busy_recovers_cached_response_without_second_post(self):
        from runtime.server_imports import ServerArtifactService

        def retain(*args, **kwargs):
            if self.retainer.call_count == 1:
                raise ArtifactError("busy")
            return ServerArtifactService._retain(self.service, *args, **kwargs)

        self.retainer.side_effect = retain
        status = self.run_detached_job()
        self.assertEqual(status["state"], "succeeded", status)
        self.assertEqual(self.retainer.call_count, 2)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(len(list(self.service.store.documents.iterdir())), 1)

    def test_detached_admission_caps_waiting_supervisors_before_any_upload(self):
        from openreading.artifacts import jobs
        from openreading.artifacts.jobs import ImportExecution, ImportJobs

        # The runner is not started. Real intake and admission validate five local sources.
        references = []
        for index in range(5):
            path = self.selection.grant / self.references[0]
            path = path.with_name(f"queued-{index}.custom")
            path.write_bytes(b"synthetic bytes")
            references.append(path.relative_to(self.selection.grant).as_posix())
        manager = ImportJobs(self.service, execution=ImportExecution(("trusted-worker",), {}))
        with patch.object(jobs.subprocess, "Popen", return_value=Mock(pid=os.getpid())):
            admitted = [manager.start(path).job_id for path in references[:4]]
            with self.assertRaises(ArtifactError) as caught:
                manager.start(references[4])
        self.assertEqual(caught.exception.code, "busy")
        self.assertTrue(caught.exception.envelope().error.retryable)
        self.assertEqual({path.name for path in manager.root.iterdir()}, set(admitted))
        self.assertEqual(self.requests, [])

    def test_duplicate_physical_pages_are_rejected_before_caching_or_retention(self):
        from runtime.server_selection import approval_name

        self.response["document"] = {
            "page_count": 2,
            "pages": [
                {"page_number": 1, "text": "Payment approved."},
                {"page_number": 1, "text": "Payment rejected."},
            ],
        }
        with self.assertRaises(ArtifactError):
            self.service.import_document(self.references[0])
        self.assertEqual(len(self.requests), 1)
        self.retainer.assert_not_called()
        path = self.service.transfers / (approval_name(self.references[0]) + ".response")
        self.assertFalse(path.exists())

    def test_rejected_result_releases_siblings_without_reupload_after_restart(self):
        from runtime.server_imports import ResponseRejected, ServerArtifactService

        def handle(request):
            self.requests.append(request)
            response = self.response
            if len(self.requests) == 1:
                response = {
                    **response,
                    "document": {
                        "pages": [
                            {"page_number": 1, "text": "Payment approved."},
                            {"page_number": 1, "text": "Payment rejected."},
                        ]
                    },
                }
            return httpx.Response(200, json=response)

        transport = httpx.MockTransport(handle)
        self.service.transport = transport
        with self.assertRaises(ResponseRejected):
            self.service.import_document(self.references[0])
        self.service.close()
        restarted = ServerArtifactService(
            self.config,
            settings=self.settings,
            selection=self.selection,
            identity=self.identity,
            transport=transport,
        )
        self.addCleanup(restarted.close)
        with self.assertRaises(ArtifactError):
            restarted.import_document(self.references[0])
        self.assertEqual(len(self.requests), 1)
        receipt = restarted.import_document(self.references[1])
        self.assertEqual(receipt.extraction_state, "succeeded")
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(len(list(restarted.store.documents.iterdir())), 1)

    def test_cancel_unapproved_and_changed_settings_never_submit(self):
        event = threading.Event()
        event.set()
        with self.assertRaises(ArtifactError) as caught:
            self.service.import_document(self.references[0], cancelled=event)
        self.assertEqual(caught.exception.code, "cancelled")
        with self.assertRaises(ArtifactError):
            self.service.import_document("a" * 32 + "/unapproved.pdf")
        save_destination("chatgpt", "local", home=self.home)
        with self.assertRaises(ArtifactError):
            self.service.import_document(self.references[0])
        self.assertEqual(self.requests, [])

    def test_corrupt_destination_settings_require_new_selection_without_upload(self):
        destination = self.selection.root.parents[1] / "destination.json"
        destination.write_text("corrupt")
        with self.assertRaises(ArtifactError) as caught:
            self.service.import_document(self.references[0])
        self.assertEqual(caught.exception.code, "access_denied")
        self.assertEqual(self.requests, [])

    def test_real_retention_and_mcp_delivery_preserve_server_values(self):
        import asyncio
        import json

        from mcp.shared.memory import create_connected_server_and_client_session
        from openreading.artifacts.jobs import ImportExecution
        from openreading.mcp_server.tools import create_server

        from runtime.server_imports import ServerArtifactService

        response = {
            "schema_version": "0.3",
            "status": {"state": "partial"},
            "backend": {"id": "synthetic", "type": "oss_library"},
            "document": {
                "page_count": 1,
                "text": "SERVER ALPHA 界",
                "pages": [{"page_number": 1, "text": "SERVER ALPHA 界"}],
            },
            "future": {"explicit_null": None, "flag": False, "number": 0},
        }
        self.service.transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json=response)
        )
        retained = ServerArtifactService._retain.__get__(self.service)
        self.assertFalse(hasattr(self.service, "_worker"))
        with patch.object(self.service, "_retain", retained):
            receipt = self.service.import_document(self.references[0])
        self.assertEqual(receipt.schema_version, "0.5")
        self.assertEqual(receipt.extraction_state, "partial")
        self.assertEqual(self.service.store.load_document(receipt.artifact_id)[2], response)

        async def retrieve():
            server = create_server(
                self.service,
                execution=ImportExecution(("trusted-child",), {"test": True}),
            )
            async with create_connected_server_and_client_session(server) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual(len(tools), 9)
                imported = next(tool for tool in tools if tool.name == "openreading_import")
                self.assertTrue(imported.annotations.openWorldHint)
                document = await client.call_tool(
                    "openreading_get_document",
                    {"artifact_id": receipt.artifact_id, "delivery": "auto"},
                )
                self.assertFalse(document.isError)
                self.assertEqual(
                    json.loads(document.content[0].text)["content"]["response"],
                    response,
                )
                found = await client.call_tool(
                    "openreading_search",
                    {"artifact_id": receipt.artifact_id, "query": "ALPHA"},
                )
                evidence = json.loads(found.content[0].text)["hits"][0]["evidence_id"]
                read = await client.call_tool(
                    "openreading_read",
                    {"artifact_id": receipt.artifact_id, "evidence_ids": [evidence]},
                )
                passage = json.loads(read.content[0].text)["passages"][0]
                self.assertEqual(passage["page"], 1)
                self.assertIn("SERVER ALPHA 界", passage["text"])

        asyncio.run(retrieve())

    def test_active_transfer_blocks_other_jobs_and_invalid_cache_never_uploads(self):
        from runtime.server_selection import approval_name

        with self.service._serial():
            with self.assertRaises(ArtifactError) as caught:
                self.service.import_document(self.references[0])
            self.assertEqual(caught.exception.code, "busy")
        path = self.service.transfers / (approval_name(self.references[0]) + ".response")
        path.write_text("{}")
        with self.assertRaises(ArtifactError) as caught:
            self.service.import_document(self.references[0])
        self.assertEqual(caught.exception.code, "artifact_corrupt")
        self.assertEqual(self.requests, [])

    def test_unusable_200_response_is_not_cached_as_a_retainable_result(self):
        from runtime.server_selection import approval_name

        self.service.transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "schema_version": "0.3",
                    "status": {"state": "failed"},
                    "backend": {"id": "synthetic", "type": "oss_library"},
                    "document": {"page_count": 1},
                },
            )
        )
        with self.assertRaises(ArtifactError) as caught:
            self.service.import_document(self.references[0])
        self.assertEqual(caught.exception.code, "access_denied")
        self.assertIn("select", caught.exception.envelope().error.message.lower())
        response = self.service.transfers / (approval_name(self.references[0]) + ".response")
        self.assertFalse(os.path.lexists(response))
        self.retainer.assert_not_called()

    def test_deep_valid_response_remains_recoverable_from_local_cache(self):
        nested = "value"
        for _ in range(60):
            nested = {"next": nested}
        response = {**self.response, "future": nested}
        self.service.transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json=response)
        )
        self.assertIs(self.service.import_document(self.references[0]), self.receipt)
        self.assertIs(self.service.import_document(self.references[0]), self.receipt)

    def test_synchronous_mcp_server_import_with_progress_preserves_the_batch(self):
        import asyncio
        import json

        from mcp.shared.memory import create_connected_server_and_client_session
        from openreading.artifacts.jobs import ImportExecution
        from openreading.mcp_server.tools import create_server

        from runtime.server_imports import ServerArtifactService

        response = {
            "schema_version": "0.3",
            "status": {"state": "succeeded"},
            "backend": {"id": "synthetic", "type": "oss_library"},
            "document": {
                "page_count": 1,
                "text": "SERVER ALPHA",
                "pages": [{"page_number": 1, "text": "SERVER ALPHA"}],
            },
        }

        async def handle(request):
            self.requests.append(request)
            await asyncio.sleep(0.05)
            return httpx.Response(200, json=response)

        self.service.transport = httpx.MockTransport(handle)
        seen = []

        async def observed(progress, total, message):
            seen.append(message)

        async def run():
            server = create_server(self.service, execution=ImportExecution(("trusted",), {}))
            async with create_connected_server_and_client_session(server) as client:
                for reference in self.references:
                    result = await client.call_tool(
                        "openreading_import",
                        {"path": reference},
                        progress_callback=observed,
                    )
                    self.assertFalse(result.isError, result)
                    self.assertEqual(
                        json.loads(result.content[0].text)["extraction_state"],
                        "succeeded",
                    )

        with patch.object(
            self.service, "_retain", ServerArtifactService._retain.__get__(self.service)
        ):
            asyncio.run(run())
        self.assertEqual(len(self.requests), 2)
        self.assertIn("uploading", seen)

    def test_nonobject_cached_response_fails_before_retention_without_upload(self):
        import json

        from runtime.server_selection import approval_name

        self.service.import_document(self.references[0])
        path = self.service.transfers / (approval_name(self.references[0]) + ".response")
        value = json.loads(path.read_bytes())
        self.retainer.reset_mock()
        for response in (None, [], "invalid", 1):
            value["response"] = response
            path.write_text(json.dumps(value))
            with self.assertRaises(ArtifactError) as caught:
                self.service.import_document(self.references[0])
            self.assertEqual(caught.exception.code, "artifact_corrupt")
        self.retainer.assert_not_called()
        self.assertEqual(len(self.requests), 1)

    def test_stopped_selection_explains_recovery_without_repeating_upload(self):
        def fail(request):
            self.requests.append(request)
            raise httpx.ReadTimeout("private failure")

        self.service.transport = httpx.MockTransport(fail)
        with self.assertRaises(ArtifactError):
            self.service.import_document(self.references[0])
        for reference in self.references:
            with self.assertRaises(ArtifactError) as caught:
                self.service.import_document(reference)
            message = caught.exception.envelope().error.message.lower()
            self.assertIn("selection", message)
            self.assertIn("select", message)
            self.assertIn("confirm", message)
        self.assertEqual(len(self.requests), 1)

    def test_unicode_cache_avoids_ascii_expansion_and_reads_legacy_cache(self):
        import json

        from runtime.server_selection import approval_name

        self.service.transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={**self.response, "document": {"text": "界" * 1000}}
            )
        )
        self.service.import_document(self.references[0])
        path = self.service.transfers / (approval_name(self.references[0]) + ".response")
        self.assertLess(len(path.read_bytes()), 4000)
        value = json.loads(path.read_bytes())
        path.write_text(json.dumps(value, ensure_ascii=True))
        self.assertIs(self.service.import_document(self.references[0]), self.receipt)

    def test_legacy_settings_import_without_reading_or_sending_credentials(self):
        import json

        from runtime.destination_settings import read_destination

        path = next(self.home.rglob("destination.json"))
        value = json.loads(path.read_text())
        value.update(schema_version=1, credential_ref="c" * 32)
        path.write_text(json.dumps(value))
        self.service.settings = read_destination("chatgpt", home=self.home)
        with patch("ctypes.CDLL", side_effect=AssertionError("No Keychain access")):
            self.assertIs(self.service.import_document(self.references[0]), self.receipt)
        self.assertEqual(len(self.requests), 1)
        self.assertNotIn("authorization", self.requests[0].headers)
        self.assertNotIn("credential_ref", self.service.settings.wire())

    def test_server_failure_reports_safe_reason_without_claiming_local_processing(self):
        self.service.transport = httpx.MockTransport(lambda request: httpx.Response(403))
        with self.assertRaises(ArtifactError) as raised:
            self.service.import_document(self.references[0])
        error = raised.exception.envelope().error
        self.assertEqual(error.code, "parse_failed")
        self.assertIn("403", error.message)
        self.assertFalse(error.retryable)
