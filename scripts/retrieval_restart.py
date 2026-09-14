"""Reopen the C3 evidence through two fresh MCP processes and verify every retained quote.

Run with the same candidate and network-denial wrapper as retrieval_check.py. This checks
stdio process restart, input-root isolation, and exact citation persistence. It does not
exercise a Desktop installation or invoke a language model. Each process must expose exactly
the selected tools with identical schema hashes, negotiated protocol and server identity.
"""

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from measurement.corpus import recipe  # noqa: E402
from scripts.docling_feasibility import network_denied, selected_environment  # noqa: E402


def payload(result):
    if result.isError:
        raise ValueError("MCP refused the registered request.")
    return json.loads(result.content[0].text)


async def check(args):
    retrieval = (args.output / "retrieval-report.json").read_bytes()
    report = json.loads(retrieval)
    if (
        not report["passed"]
        or not network_denied()
        or selected_environment(args.lock) != report["environment"]
    ):
        raise ValueError("A passing matching offline retrieval report is required.")
    config = args.output / "profile.json"
    config.write_text(
        json.dumps(
            {
                "pages": None,
                "source_bytes": None,
                "extraction_bytes": None,
                "store_bytes": None,
                "deadline_seconds": None,
                "worker_memory_bytes": 4 * 1024**3,
                "worker_idle_seconds": 60,
                "docling": {
                    "artifacts_path": str(args.assets),
                    "dependency_lock": str(args.lock),
                    "ocr": False,
                    "threads": 4,
                },
            }
        )
    )
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "openreading.mcp_server.main",
            "--profile",
            "local-document-proof-v2",
            "--profile-config",
            str(config),
            "--input-root",
            str(args.output / "documents"),
            "--artifact-root",
            str(args.output / "store-False"),
        ],
        env={"PATH": os.defpath, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
    )
    records = []
    for generation in range(2):
        count = 0
        async with (
            stdio_client(params) as (reader, writer),
            ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=330)) as session,
        ):
            initialized = await session.initialize()
            tools = (await session.list_tools()).tools
            if len(tools) != 8 or {tool.name for tool in tools} != {
                "openreading_import",
                "openreading_search",
                "openreading_read",
                "openreading_select_document",
                "openreading_get_document",
                "openreading_start_import",
                "openreading_get_import",
                "openreading_cancel_import",
            }:
                raise ValueError("The selected MCP tool catalog is not available.")
            contract = [
                {"name": tool.name, "input": tool.inputSchema, "output": tool.outputSchema}
                for tool in sorted(tools, key=lambda tool: tool.name)
            ]
            schema_digest = hashlib.sha256(
                json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            protocol = {
                "protocol_version": initialized.protocolVersion,
                "server_name": initialized.serverInfo.name,
                "server_version": initialized.serverInfo.version,
                "tool_schema_sha256": schema_digest,
            }
            if records and any(records[0][key] != value for key, value in protocol.items()):
                raise ValueError("Restart changed the negotiated MCP contract.")
            for name, document in report["documents"].items():
                receipt = payload(
                    await session.call_tool("openreading_import", {"path": f"{name}.pdf"})
                )
                if (
                    not receipt["reused"]
                    or receipt["artifact_id"] != document["receipt"]["artifact_id"]
                ):
                    raise ValueError("Restart changed the retained artifact identity.")
            for task in report["tasks"]:
                if task["passed"] is None:
                    continue
                source = next(t for t in recipe()["tasks"] if t["id"] == task["task_id"])
                identifier = report["documents"][source["document"]]["receipt"]["artifact_id"]
                for citation in task["citations"]:
                    result = payload(
                        await session.call_tool(
                            "openreading_read",
                            {"artifact_id": identifier, "evidence_ids": [citation["evidence_id"]]},
                        )
                    )
                    passage = result["passages"][0]
                    if (
                        any(
                            passage[key] != citation[key]
                            for key in ("evidence_id", "page", "text_origin")
                        )
                        or passage["text"] != citation["quote"]
                    ):
                        raise ValueError("Restart changed an exact citation.")
                    count += 1
            refused = await session.call_tool(
                "openreading_import", {"path": "../ground-truth.json"}
            )
            if not refused.isError:
                raise ValueError("The input root allowed ground-truth access.")
        records.append(
            {
                **protocol,
                "process_generation": generation,
                "exact_reads": count,
                "outside_grant_refused": True,
            }
        )
    (args.output / "restart-report.json").write_text(
        json.dumps(
            {
                "passed": True,
                # Binds this restart result to the exact retrieval evidence it reopened.
                "retrieval_report_sha256": hashlib.sha256(retrieval).hexdigest(),
                "processes": records,
            },
            indent=2,
        )
        + "\n"
    )
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("assets", "output", "lock"):
        parser.add_argument(f"--{name}", required=True, type=lambda value: Path(value).resolve())
    print(json.dumps(asyncio.run(check(parser.parse_args(argv)))))


if __name__ == "__main__":
    main()
