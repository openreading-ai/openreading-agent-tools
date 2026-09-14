"""A frozen Docling smoke cannot pass incorrect OCR, provenance or restart receipts."""

import asyncio
import hashlib
import importlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as Box
from unittest.mock import patch

from mcp import types
from test_proof_scripts import channel


class DoclingSmokeTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("scripts.docling_package_smoke"))
        return importlib.import_module("scripts.docling_package_smoke")

    def test_protocol_smoke_accepts_only_correct_pages_ocr_and_restart(self):
        for fault in (
            None,
            "no_reference",
            "reference_core",
            "reference_missing_true",
            "reference_missing_false",
            "reference_missing_profiles",
            "reference_null",
            "reference_missing_commit",
            "reference_instructions",
            "manifest_missing",
            "reference_only",
            "manifest_only",
            "source",
            "network",
            "telemetry",
            "catalog",
            "receipt",
            "restart",
            "page",
            "text",
            "ocr",
            "phantom_ocr",
            "warm",
            "memory",
            "refusal",
            "error",
            "document_raw",
            "document_ocr",
            "document_digest",
            "document_cursor",
            "document_artifact",
        ):
            with self.subTest(fault=fault):
                self.exercise(fault)

    def exercise(self, fault):
        module = self.module()
        calls = []
        states = []

        def transport(params):
            self.assertEqual(params.command, "/usr/bin/sandbox-exec")
            self.assertIn("(deny network*)", params.args[1])
            self.assertEqual(params.env["PATH"], "/usr/bin:/bin")
            self.assertEqual(params.env.get("ORT_DISABLE_TELEMETRY"), "0")
            if fault == "telemetry":
                target = (
                    Path(params.env["HOME"])
                    / "Library/Application Support/Microsoft/DeveloperTools/.onnxruntime"
                )
                target.mkdir(parents=True, exist_ok=True)
                (target / "deviceid").write_text("synthetic")
            states.append(params.args[-1] == "on")
            return channel()

        class Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def initialize(self):
                return Box(protocolVersion="2025-11-25", instructions="Use returned IDs.")

            async def list_tools(self):
                return Box(
                    tools=[
                        types.Tool(name=name, inputSchema={"type": "object"})
                        for name in (
                            ["bad"]
                            if fault == "catalog"
                            else [
                                "openreading_import",
                                "openreading_search",
                                "openreading_read",
                                "openreading_get_document",
                                "openreading_select_document",
                                "openreading_start_import",
                                "openreading_get_import",
                                "openreading_cancel_import",
                            ]
                        )
                    ]
                )

            async def call_tool(self, name, args, **kwargs):
                if name == "openreading_read":
                    assert set(args) == {"artifact_id", "evidence_ids"}
                calls.append((name, args))
                ocr = states[-1]
                if args.get("path", "").startswith(".."):
                    return Box(isError=fault != "refusal", content=[])
                if name == "openreading_import":
                    if kwargs.get("progress_callback"):
                        await kwargs["progress_callback"](1, None, "preflight")
                    value = {
                        "artifact_id": f"id-{ocr}",
                        "page_count": 0 if fault == "receipt" else 6,
                        "document_sha256": "fixture",
                        "reused": len(states) % 2 == 0
                        or (fault == "warm" and args["path"] == "warm.pdf"),
                    }
                    if fault == "restart" and len(states) % 2 == 0:
                        value["artifact_id"] = "wrong"
                elif name == "openreading_get_document":
                    pages = [
                        {
                            "page_number": number,
                            "text": "30 days"
                            if number == 1
                            else (
                                "45 days" if number == 2 and ocr and fault != "document_ocr" else ""
                            ),
                        }
                        for number in range(1, 7)
                    ]
                    content = {
                        "response": {"document": {"page_count": 6, "pages": pages}},
                        "page_origins": {"1": "native", "2": "ocr" if ocr else "none"},
                        "evidence": [{"evidence_id": "1", "page": 1}],
                        "warnings": [],
                    }
                    if fault == "document_raw":
                        content["response"]["backend_raw"] = {"private": "provider bytes"}
                    encoded = json.dumps(
                        content,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    ).encode()
                    value = {
                        "schema_version": "0.1",
                        "scope": "retained_normalized_response",
                        "artifact_id": "wrong"
                        if fault == "document_artifact"
                        else args["artifact_id"],
                        "content_sha256": "wrong"
                        if fault == "document_digest"
                        else hashlib.sha256(encoded).hexdigest(),
                        "fragment_start": 0,
                        "fragment_count": 1,
                        "fragments": [{"path": "", "value": content}],
                        "next_cursor": "more" if fault == "document_cursor" else None,
                    }
                elif name == "openreading_search":
                    page = 1 if args["query"] == "30 days" else 2
                    value = {
                        "hits": [{"page": 1, "evidence_id": "1"}]
                        + (
                            [{"page": 2, "evidence_id": "2"}]
                            if page == 2 and ((ocr and fault != "ocr") or fault == "phantom_ocr")
                            else []
                        )
                    }
                else:
                    page = int(args["evidence_ids"][0])
                    value = {
                        "passages": [
                            {
                                "page": 99 if fault == "page" else page,
                                "text": "wrong"
                                if fault == "text"
                                else ("30 days" if page == 1 else "45 days"),
                                "text_origin": "native" if page == 1 else "ocr",
                            }
                        ]
                    }
                return Box(isError=fault == "error", content=[Box(text=json.dumps(value))])

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / "fixture.pdf"
            fixture.write_bytes(b"fixture")
            contract = {
                "instructions": "wrong"
                if fault == "reference_instructions"
                else "Use returned IDs.",
                "tools": [
                    {"name": name, "inputSchema": {"type": "object"}}
                    for name in sorted(
                        [
                            "openreading_import",
                            "openreading_read",
                            "openreading_search",
                            "openreading_get_document",
                            "openreading_select_document",
                            "openreading_start_import",
                            "openreading_get_import",
                            "openreading_cancel_import",
                        ]
                    )
                ],
            }
            reference = root / "reference.json"
            reference.write_text(
                json.dumps(
                    {
                        "core_commit": "wrong" if fault == "reference_core" else "pin",
                        "profiles": {"true": contract, "false": contract},
                    }
                )
            )
            if fault in (
                "reference_missing_true",
                "reference_missing_false",
                "reference_missing_profiles",
            ):
                data = json.loads(reference.read_text())
                if fault == "reference_missing_profiles":
                    del data["profiles"]
                else:
                    del data["profiles"][fault.removeprefix("reference_missing_")]
                reference.write_text(json.dumps(data))
            if fault == "reference_null":
                reference.write_text("null")
            if fault == "reference_missing_commit":
                data = json.loads(reference.read_text())
                del data["core_commit"]
                reference.write_text(json.dumps(data))
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "tools": []
                        if fault == "manifest_missing"
                        else [{"name": item["name"]} for item in contract["tools"]]
                    }
                )
            )
            reference_arg = None if fault in ("no_reference", "manifest_only") else reference
            manifest_arg = None if fault in ("no_reference", "reference_only") else manifest
            with (
                patch.object(
                    module,
                    "verify_release",
                    return_value={
                        "format_version": "2",
                        "files": {},
                        "worker_sha256": "hash",
                        "core_commit": "pin",
                    },
                ),
                patch.object(module, "sandbox_observed", return_value=fault != "network"),
                patch.object(
                    module,
                    "sha256",
                    return_value="wrong" if fault == "source" else "fixture",
                ),
                patch.object(
                    module,
                    "recipe",
                    return_value={"expected_hashes": {"functional.pdf": "fixture"}},
                ),
                patch.object(module, "stdio_client", side_effect=transport),
                patch.object(module, "ClientSession", side_effect=lambda *a, **k: Session()),
                patch.object(module, "loaded_libraries", return_value=["native"]),
                patch.object(module, "tree_rss", return_value=0 if fault == "memory" else 100),
            ):
                if fault not in (None, "no_reference"):
                    with self.assertRaises(ValueError):
                        asyncio.run(module.smoke(root, fixture, reference_arg, manifest_arg))
                    if fault.startswith("reference_missing_"):
                        self.assertEqual(
                            states, [], "Reject incomplete references before launching children"
                        )
                else:
                    report = asyncio.run(module.smoke(root, fixture, reference_arg, manifest_arg))
                    self.assertEqual(
                        report["catalog_parity"],
                        "not_checked" if fault == "no_reference" else "passed",
                    )
                    self.assertTrue(report["passed"])
                    self.assertEqual(
                        sum(name == "openreading_get_document" for name, _ in calls), 4
                    )
                    self.assertEqual(len(report["processes"]), 4)
                    self.assertEqual(report["sampled_peak_tree_rss_including_driver"], 100)
                    self.assertTrue(any(row["progress"] for row in report["processes"]))

    def test_native_trace_refuses_external_dependencies_or_missing_observation(self):
        module = self.module()
        root = Path("/synthetic/bundle")
        for lines in [
            "",
            "dyld[1]: <ID> /opt/homebrew/lib/not-bundled.dylib",
            "dyld[1]: <ID> /synthetic/bundle/../../opt/escaped.dylib",
            "dyld[1]: <ID> /usr/lib/../../opt/escaped.dylib",
            "dyld[1]: <ID> /synthetic/bundle/resources/tesseract/bin/tesseract\ndyld[1]: <ID> /usr/lib/libSystem.B.dylib",
        ]:
            with (
                self.subTest(lines=lines),
                patch.object(module.subprocess, "run", return_value=Box(stderr=lines)),
            ):
                if lines.endswith("libSystem.B.dylib"):
                    self.assertEqual(len(module.loaded_libraries(root)), 2)
                else:
                    with self.assertRaises(ValueError):
                        module.loaded_libraries(root)

    def test_network_probe_requires_actual_permission_denial(self):
        module = self.module()
        for status, output, expected in [
            (0, "1\n", True),
            (1, "61\n", False),
            (0, "", False),
        ]:
            with (
                self.subTest(status=status, output=output),
                patch.object(
                    module.subprocess,
                    "run",
                    return_value=Box(returncode=status, stdout=output),
                ) as run,
            ):
                self.assertEqual(module.sandbox_observed("policy"), expected)
                self.assertEqual(
                    run.call_args.args[0][:3], ["/usr/bin/sandbox-exec", "-p", "policy"]
                )
                self.assertEqual(run.call_args.kwargs["timeout"], 5)

    def test_cli_uses_absolute_inputs_and_emits_only_the_report(self):
        import contextlib
        import io

        module = self.module()

        async def smoke(runtime, fixture, reference=None, manifest=None):
            self.assertTrue(runtime.is_absolute())
            self.assertTrue(fixture.is_absolute())
            return {"passed": True}

        with (
            patch.object(module, "smoke", smoke),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            module.main(["--runtime", "bundle", "--fixture", "fixture.pdf"])
        self.assertEqual(json.loads(output.getvalue()), {"passed": True})

    def test_cli_refuses_bad_input_without_traceback_or_secret(self):
        import contextlib
        import io

        module = self.module()
        for failure in (ValueError("planted-secret"), OSError("planted-secret")):

            async def refuse(*args, failure=failure):
                raise failure

            with (
                self.subTest(failure=type(failure).__name__),
                patch.object(module, "smoke", refuse),
                contextlib.redirect_stdout(io.StringIO()) as output,
                contextlib.redirect_stderr(io.StringIO()) as error,
            ):
                self.assertEqual(
                    module.main(["--runtime", "bundle", "--fixture", "fixture.pdf"]), 2
                )
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(error.getvalue(), f"Docling smoke refused: {type(failure).__name__}\n")
