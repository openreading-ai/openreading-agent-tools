"""Exercise the frozen worker over real MCP with no Python executable on its PATH.

This development-machine check does not establish a fresh-host installation or model
behavior. Its synthetic input and temporary HOME isolate retained evidence from user data.
Run with --runtime pointing to the verified native directory bundle.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from runtime.verify import verify_release


async def smoke(runtime: Path) -> dict:
    import pymupdf

    metadata = verify_release(runtime)
    with tempfile.TemporaryDirectory(prefix="openreading-host-smoke-") as temporary:
        home = Path(temporary).resolve()
        root = home / "Document grant ü spaces"
        root.mkdir()
        with pymupdf.open() as document:
            document.new_page()
            document.new_page().insert_text(
                (50, 50), "Provide notice at least 60 days before renewal."
            )
            document.save(root / "agreement sample.pdf")
        params = StdioServerParameters(
            command=str(runtime / "openreading-worker"),
            args=["--client", "claude-desktop", "--input-root", str(root)],
            env={"HOME": str(home), "PATH": "/usr/bin:/bin", "TMPDIR": str(home)},
        )
        identifier = None
        for restart in [False, True]:
            async with (
                stdio_client(params) as (reader, writer),
                ClientSession(reader, writer) as client,
            ):
                await client.initialize()
                tools = (await client.list_tools()).tools
                assert {t.name for t in tools} == {
                    "openreading_import",
                    "openreading_search",
                    "openreading_read",
                }
                result = await client.call_tool(
                    "openreading_import", {"path": "agreement sample.pdf"}
                )
                assert not result.isError, result
                assert result.structuredContent is None and len(result.content) == 1
                receipt = json.loads(result.content[0].text)
                assert receipt["reused"] == restart and receipt["page_count"] == 2
                if restart:
                    assert receipt["artifact_id"] == identifier
                identifier = receipt["artifact_id"]
                found = await client.call_tool(
                    "openreading_search",
                    {"artifact_id": identifier, "query": "renewal"},
                )
                hit = json.loads(found.content[0].text)["hits"][0]
                result = await client.call_tool(
                    "openreading_read",
                    {"artifact_id": identifier, "evidence_ids": [hit["evidence_id"]]},
                )
                passage = json.loads(result.content[0].text)["passages"][0]
                assert passage["page"] == 2 and "60 days" in passage["text"]
                denied = await client.call_tool("openreading_import", {"path": "../private.pdf"})
                assert denied.isError and "private.pdf" not in denied.content[0].text
        return {
            "status": "passed",
            "scope": "development-machine frozen stdio smoke",
            "os": platform.mac_ver()[0],
            "arch": platform.machine(),
            "core_commit": metadata["core_commit"],
            "worker_sha256": metadata["worker_sha256"],
            "restart_reuse": True,
            "unicode_paths": True,
            "physical_page_citation": 2,
            "child_path": "/usr/bin:/bin",
            "clean_host_installation": "unverified",
            "model_trials": "not_run",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(smoke(args.runtime.resolve())), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
