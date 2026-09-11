"""Proof commands exercise real orchestration with controlled engine and transport boundaries.

These tests can falsify a passing report without installing native models or starting a host.
The separate real-engine lane remains necessary evidence for extraction and MCP behavior.
"""

import asyncio
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as Box
from unittest.mock import patch

from scripts import package_smoke, retrieval_check, retrieval_restart


@contextlib.asynccontextmanager
async def channel(*args, **kwargs):
    yield (None, None)


class Session:
    def __init__(self, handler):
        self.handler = handler

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def initialize(self):
        pass

    async def list_tools(self):
        return Box(tools=[Box(name=f"openreading_{name}") for name in ("import", "search", "read")])

    async def call_tool(self, name, args):
        data, error = self.handler(name, args)
        return Box(isError=error, content=[Box(text=json.dumps(data))], structuredContent=None)


class RestartTests(unittest.TestCase):
    def test_restart_requires_matching_identity_and_preserves_every_citation(self):
        for fault in (
            None,
            "report",
            "network",
            "environment",
            "reuse",
            "id",
            "quote",
            "page",
            "refusal",
            "mcp",
        ):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                args = Box(output=root, assets=root, lock=root / "lock")
                citation = {
                    "evidence_id": "p0001-b0000-s0000",
                    "page": 1,
                    "text_origin": "native",
                    "quote": "60 days",
                }
                report = {
                    "passed": fault != "report",
                    "environment": {"pin": 1},
                    "documents": {"agreement": {"receipt": {"artifact_id": "id"}}},
                    "tasks": [
                        {"task_id": "answer", "passed": True, "citations": [citation]},
                        {"passed": None},
                    ],
                }
                source = root / "retrieval-report.json"
                source.write_text(json.dumps(report))
                calls = []

                def handler(name, values, fault=fault, calls=calls, citation=citation):
                    calls.append((name, values))
                    if values.get("path", "").startswith(".."):
                        return {}, fault != "refusal"
                    if name == "openreading_import":
                        return {
                            "reused": fault != "reuse",
                            "artifact_id": "wrong" if fault == "id" else "id",
                        }, fault == "mcp"
                    return {
                        "passages": [
                            {
                                **citation,
                                "page": 2 if fault == "page" else 1,
                                "text": "wrong" if fault == "quote" else "60 days",
                            }
                        ]
                    }, False

                with (
                    patch.object(
                        retrieval_restart, "network_denied", return_value=fault != "network"
                    ),
                    patch.object(
                        retrieval_restart,
                        "selected_environment",
                        return_value={"pin": 2 if fault == "environment" else 1},
                    ),
                    patch.object(
                        retrieval_restart,
                        "recipe",
                        return_value={"tasks": [{"id": "answer", "document": "agreement"}]},
                    ),
                    patch.object(retrieval_restart, "stdio_client", channel),
                    patch.object(
                        retrieval_restart,
                        "ClientSession",
                        side_effect=lambda *a, **kw: Session(handler),
                    ),
                ):
                    if fault:
                        with self.assertRaises(ValueError):
                            asyncio.run(retrieval_restart.check(args))
                        self.assertFalse((root / "restart-report.json").exists())
                    else:
                        records = asyncio.run(retrieval_restart.check(args))
                        self.assertEqual([r["exact_reads"] for r in records], [1, 1])
                        self.assertEqual(len(calls), 6)
                        result = json.loads((root / "restart-report.json").read_text())
                        self.assertEqual(
                            result["retrieval_report_sha256"],
                            hashlib.sha256(source.read_bytes()).hexdigest(),
                        )

    def test_restart_cli_passes_resolved_arguments(self):
        async def check(args):
            self.assertTrue(args.output.is_absolute())
            return ["ok"]

        with (
            patch.object(retrieval_restart, "check", check),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            retrieval_restart.main(["--assets", ".", "--output", ".", "--lock", "lock"])
            self.assertEqual(json.loads(output.getvalue()), ["ok"])


class RetrievalCommandTests(unittest.TestCase):
    def test_retrieval_records_only_verified_source_and_complete_functional_checks(self):
        for fault in (
            None,
            "network",
            "existing",
            "generation",
            "source",
            "warning",
            "pages",
            "functional",
            "task",
        ):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "evidence"
                args = Box(
                    output=root,
                    assets=root,
                    lock=root / "lock",
                    tesseract=root / "ocr",
                    tessdata=root,
                )
                if fault == "existing":
                    root.mkdir()
                closed = []
                spec = {
                    "documents": {"agreement": {"pages": 1}},
                    "expected_hashes": {"agreement.pdf": "hash", "functional.pdf": "hash"},
                    "tasks": [{"id": "answer", "document": "agreement"}],
                }

                def generate(output, fault=fault, spec=spec):
                    output.mkdir()
                    return {"files": {} if fault == "generation" else spec["expected_hashes"]}

                class Service:
                    def __init__(self, config, root=root):
                        self.ocr = config.docling.ocr
                        self.store = Box(documents=root, load=self.load)

                    def import_document(self, path, root=root, fault=fault):
                        name = Path(path).stem
                        self.name = name
                        folder = root / name
                        folder.mkdir(exist_ok=True)
                        texts = (
                            ["native answer"]
                            if name == "agreement"
                            else [
                                "30 days",
                                "45 days" if self.ocr else "",
                                "two signatures" if self.ocr else "native",
                                "",
                                "filter inspection and motor inspection",
                                "office renewal",
                            ]
                        )
                        pages = [
                            {"page_number": i + 1, "text": text} for i, text in enumerate(texts)
                        ]
                        if fault == "pages" and name == "agreement":
                            pages.append({"page_number": 2, "text": "extra"})
                        (folder / "response.json").write_text(
                            json.dumps(
                                {
                                    "document": {"pages": pages},
                                    "warnings": [{"code": "ambiguous_page_provenance"}]
                                    if fault == "warning"
                                    else [],
                                }
                            )
                        )
                        return Box(artifact_id=name, wire=lambda: {"artifact_id": name})

                    def load(self, identifier, fault=fault):
                        origins = {
                            "1": "native",
                            "2": "ocr" if self.ocr else "none",
                            "3": "mixed" if self.ocr else "native",
                            "4": "none",
                        }
                        if fault == "functional":
                            origins["4"] = "mixed"
                        return Box(
                            document_sha256="wrong" if fault == "source" else "hash",
                            engine=Box(wire=lambda: {"engine": "fixed"}),
                            page_origins=origins,
                        ), []

                    def search(self, *args):
                        return Box(hits=[Box(page=6)])

                    def close(self, closed=closed):
                        closed.append(self.ocr)

                with (
                    patch.object(
                        retrieval_check, "network_denied", return_value=fault != "network"
                    ),
                    patch.object(
                        retrieval_check, "selected_environment", return_value={"pin": "fixed"}
                    ),
                    patch.object(retrieval_check, "generate", generate),
                    patch.object(retrieval_check, "recipe", return_value=spec),
                    patch.object(
                        retrieval_check, "evaluate", return_value={"passed": fault != "task"}
                    ),
                    patch.dict(
                        "sys.modules",
                        {
                            "openreading.adapters.docling_local.config": Box(
                                LocalDoclingConfig=lambda assets, **kw: Box(**kw)
                            ),
                            "openreading.artifacts.limits": Box(
                                ProfileConfig=Box, DoclingLimits=Box
                            ),
                            "openreading.artifacts.service": Box(ArtifactService=Service),
                        },
                    ),
                ):
                    if fault not in (None, "task", "functional"):
                        with self.assertRaises((ValueError, FileExistsError)):
                            retrieval_check.check(args)
                        self.assertFalse((root / "retrieval-report.json").exists())
                    else:
                        result = retrieval_check.check(args)
                        self.assertEqual(result["passed"], fault is None)
                        self.assertEqual(closed, [False, True])
                        self.assertEqual(set(result["functional"]), {"False", "True"})
                        self.assertEqual(
                            result["documents"]["agreement"]["full_text_sha256"],
                            hashlib.sha256(
                                (root / "agreement-ocr-False.txt").read_bytes()
                            ).hexdigest(),
                        )
                if fault in ("source", "warning", "pages"):
                    self.assertEqual(closed, [False])

    def test_retrieval_cli_propagates_failed_gate(self):
        argv = [
            part
            for name in ("assets", "output", "lock", "tesseract", "tessdata")
            for part in (f"--{name}", ".")
        ]
        for passed in (True, False):
            with (
                patch.object(retrieval_check, "check", return_value={"passed": passed}),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(retrieval_check.main(argv), 0 if passed else 1)


class PackagedSmokeTests(unittest.TestCase):
    def test_packaged_smoke_runs_two_sessions_and_checks_refusal(self):
        imported = []

        def handler(name, args):
            if name == "openreading_import":
                if args["path"].startswith(".."):
                    return {"error": "access_denied"}, True
                reused = bool(imported)
                imported.append(args["path"])
                return {"reused": reused, "page_count": 2, "artifact_id": "stable"}, False
            if name == "openreading_search":
                return {"hits": [{"evidence_id": "passage"}]}, False
            return {"passages": [{"page": 2, "text": "60 days"}]}, False

        with (
            patch.object(
                package_smoke,
                "verify_release",
                return_value={"core_commit": "core", "worker_sha256": "hash"},
            ),
            patch.object(package_smoke, "stdio_client", channel),
            patch.object(package_smoke, "ClientSession", side_effect=lambda *a: Session(handler)),
        ):
            result = asyncio.run(package_smoke.smoke(Path("/runtime")))
            self.assertEqual(result["status"], "passed")
            self.assertEqual(len(imported), 2)
            self.assertEqual(result["clean_host_installation"], "unverified")

        async def smoke(path):
            return result

        with (
            patch.object(package_smoke, "smoke", smoke),
            patch("sys.argv", ["smoke", "--runtime", "."]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(package_smoke.main(), 0)
