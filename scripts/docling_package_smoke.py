"""Check a development-only frozen Docling candidate through real MCP, including OCR.

Run with the frozen corpus's functional.pdf. Each child receives OS network denial and
also cannot read this checkout, Homebrew, or the uv Python directory. Their PATH contains
only system tools, and their working directory is unrelated to the bundle.
The explicit synthetic grant uses codex/v2 artifact storage without reading saved settings
or changing client registration. Retained synthetic artifacts remain there until removed.
Timings are individual observations, not cold-cache measurements or release limits.
Optional --reference and --manifest compare captured same-profile core tools/instructions
and manifest names. The reference is trusted review input, not an authenticated transcript.
Its core commit must match the bundle; both OCR modes require an independently captured
reference. A smoke without these inputs reports catalog_parity=not_checked.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from measurement.corpus import recipe
from runtime.verify import sha256, verify_release
from scripts.docling_feasibility import tree_rss
from scripts.retrieval_restart import payload


def catalog_snapshot(initialized, tools):
    if not initialized.instructions or len({tool.name for tool in tools}) != len(tools):
        raise ValueError("MCP instructions are missing or tool names are duplicated.")
    return {
        "instructions": initialized.instructions,
        "tools": [
            tool.model_dump(mode="json", exclude_none=True)
            for tool in sorted(tools, key=lambda tool: tool.name)
        ],
    }


def check_catalog(expected, actual, manifest):
    names = [tool["name"] for tool in manifest["tools"]]
    if (
        expected != actual
        or len(set(names)) != len(names)
        or sorted(names) != [tool["name"] for tool in actual["tools"]]
    ):
        raise ValueError("The frozen catalog, profile instructions or manifest differs from core.")


def loaded_libraries(runtime):
    result = subprocess.run(
        [str(runtime / "resources/tesseract/bin/tesseract"), "--version"],
        env={"PATH": "/usr/bin:/bin", "DYLD_PRINT_LIBRARIES": "1"},
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    paths = re.findall(r"^dyld\[\d+\]: <[^>]+> (/.+)$", result.stderr, re.MULTILINE)
    allowed = [runtime.resolve(), Path("/usr/lib"), Path("/System/Library")]
    if not paths or any(
        not any(Path(path).resolve().is_relative_to(root) for root in allowed) for path in paths
    ):
        raise ValueError(
            "Native dependency observation is absent or escapes the bundle/system libraries."
        )
    return paths


def sandbox_observed(policy):
    # System Perl supplies a socket errno without loading the denied developer Python.
    script = 'use Socket; use Errno qw(EPERM); my $ok=socket(my $sock,PF_INET,SOCK_STREAM,0); $ok &&=connect($sock,sockaddr_in(9,inet_aton("127.0.0.1"))); my $error=0+$!; print "$error\\n"; exit(!$ok && $error==EPERM ? 0 : 1);'
    result = subprocess.run(
        ["/usr/bin/sandbox-exec", "-p", policy, "/usr/bin/perl", "-e", script],
        capture_output=True,
        text=True,
        timeout=5,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
    )
    return result.returncode == 0 and result.stdout.strip() == "1"


async def smoke(
    runtime: Path,
    fixture: Path,
    reference: Path | None = None,
    manifest: Path | None = None,
) -> dict:
    started = time.monotonic()
    metadata = verify_release(runtime)
    verification_seconds = time.monotonic() - started
    if (reference is None) != (manifest is None):
        raise ValueError("Provide both the core catalog reference and Desktop manifest.")
    expected = json.loads(reference.read_text()) if reference else None
    declared = json.loads(manifest.read_text()) if manifest else None
    if expected is not None and expected["core_commit"] != metadata["core_commit"]:
        raise ValueError("The catalog reference names another core commit.")
    if (
        metadata["format_version"] != "2"
        or sha256(fixture) != recipe()["expected_hashes"]["functional.pdf"]
    ):
        raise ValueError(
            "A verified Docling bundle, network denial and the frozen functional PDF are required."
        )
    libraries = loaded_libraries(runtime)
    blocked = [
        Path(__file__).resolve().parents[1],
        Path("/opt/homebrew"),
        Path("/usr/local"),
        Path.home() / ".local/share/uv",
    ]
    policy = "(version 1)(allow default)(deny network*)" + "".join(
        f"(deny file-read* (subpath {json.dumps(str(path))}))" for path in blocked
    )
    if not sandbox_observed(policy):
        raise ValueError("OS network denial was not observed for the child policy.")
    records = []
    peak = tree_rss(os.getpid())

    async def sample():
        nonlocal peak
        while True:
            peak = max(peak, tree_rss(os.getpid()))
            await asyncio.sleep(0.05)

    sampler = asyncio.create_task(sample())
    try:
        await asyncio.sleep(0)
        with tempfile.TemporaryDirectory(prefix="openreading-p0-smoke-") as temporary:
            work = Path(temporary).resolve()
            grant = work / "Document grant ü spaces"
            grant.mkdir()
            (grant / "functional.pdf").write_bytes(fixture.read_bytes())
            (grant / "warm.pdf").write_bytes(
                fixture.read_bytes() + b"\n% synthetic warm conversion\n"
            )
            for ocr in (False, True):
                identifier = None
                for generation in range(2):
                    params = StdioServerParameters(
                        command="/usr/bin/sandbox-exec",
                        args=[
                            "-p",
                            policy,
                            str(runtime / "openreading-worker"),
                            "--client",
                            "codex",
                            "--input-root",
                            str(grant),
                            "--ocr",
                            "on" if ocr else "off",
                        ],
                        env={
                            "PATH": "/usr/bin:/bin",
                            "HF_HUB_OFFLINE": "1",
                            "TRANSFORMERS_OFFLINE": "1",
                        },
                        cwd=work,
                    )
                    start = time.monotonic()
                    progress = []

                    async def observe(number, total, message, progress=progress, start=start):
                        progress.append(
                            {
                                "stage": message,
                                "seconds_since_launch": time.monotonic() - start,
                            }
                        )

                    async with (
                        stdio_client(params) as (reader, writer),
                        ClientSession(
                            reader, writer, read_timeout_seconds=timedelta(seconds=330)
                        ) as client,
                    ):
                        initialized = await client.initialize()
                        initialization = time.monotonic() - start
                        tools = (await client.list_tools()).tools
                        catalog = catalog_snapshot(initialized, tools)
                        if expected is not None:
                            check_catalog(
                                expected["profiles"][str(ocr).lower()],
                                catalog,
                                declared,
                            )
                        if not {
                            "openreading_import",
                            "openreading_read",
                            "openreading_search",
                        }.issubset(tool.name for tool in tools):
                            raise ValueError("The frozen runtime exposes a different tool catalog.")
                        before = time.monotonic()
                        receipt = payload(
                            await client.call_tool(
                                "openreading_import",
                                {"path": "functional.pdf"},
                                progress_callback=observe,
                            )
                        )
                        import_seconds = time.monotonic() - before
                        if (
                            receipt["page_count"] != 6
                            or receipt["document_sha256"] != sha256(fixture)
                            or receipt["reused"] is not bool(generation)
                            or (identifier is not None and identifier != receipt["artifact_id"])
                        ):
                            raise ValueError(
                                "The import or restart receipt differs from the frozen source."
                            )
                        identifier = receipt["artifact_id"]
                        for page, query in ((1, "30 days"), (2, "45 days")):
                            found = payload(
                                await client.call_tool(
                                    "openreading_search",
                                    {"artifact_id": identifier, "query": query},
                                )
                            )
                            # Lexical search matches individual words, so "45 days" may
                            # also return native "30 days" on another physical page.
                            candidates = [hit for hit in found["hits"] if hit["page"] == page]
                            if page == 2 and not ocr:
                                if candidates:
                                    raise ValueError(
                                        "Raster-only evidence appeared with OCR disabled."
                                    )
                                continue
                            if not candidates:
                                raise ValueError("Expected native or OCR evidence is missing.")
                            hit = candidates[0]
                            passage = payload(
                                await client.call_tool(
                                    "openreading_read",
                                    {
                                        "artifact_id": identifier,
                                        "evidence_ids": [hit["evidence_id"]],
                                    },
                                )
                            )["passages"][0]
                            if (
                                passage["page"] != page
                                or query not in passage["text"]
                                or passage["text_origin"] != ("native" if page == 1 else "ocr")
                            ):
                                raise ValueError(
                                    "The citation text, physical page or origin is wrong."
                                )
                        warm_seconds = None
                        if generation == 0:
                            before = time.monotonic()
                            warm = payload(
                                await client.call_tool("openreading_import", {"path": "warm.pdf"})
                            )
                            warm_seconds = time.monotonic() - before
                            if warm["reused"] or warm["page_count"] != 6:
                                raise ValueError(
                                    "The warm conversion reused an artifact or lost pages."
                                )
                        denied = await client.call_tool(
                            "openreading_import", {"path": "../outside.pdf"}
                        )
                        if not denied.isError:
                            raise ValueError("The document grant allowed an outside path.")
                    records.append(
                        {
                            "ocr": ocr,
                            "generation": generation,
                            "protocol_version": initialized.protocolVersion,
                            "catalog": catalog,
                            "initialization_seconds": initialization,
                            "import_seconds": import_seconds,
                            "warm_conversion_seconds": warm_seconds,
                            "progress": progress,
                            "artifact_id": identifier,
                        }
                    )
    finally:
        sampler.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sampler
    if peak <= 0:
        raise ValueError("No process memory sample was obtained.")
    return {
        "passed": True,
        "catalog_parity": "passed" if expected is not None else "not_checked",
        "catalog_reference_sha256": sha256(reference) if reference else None,
        "manifest_sha256": sha256(manifest) if manifest else None,
        "scope": "development-machine frozen Docling smoke",
        "core_commit": metadata["core_commit"],
        "worker_sha256": metadata["worker_sha256"],
        "verification_seconds": verification_seconds,
        "inventoried_bytes": sum(entry.get("length", 0) for entry in metadata["files"].values()),
        "loaded_libraries": libraries,
        "sampled_peak_tree_rss_including_driver": peak,
        "processes": records,
        "native_host_support": "unverified",
        "model_calls": "not_run",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument(
        "--reference", type=Path, help="captured same-profile pinned-core catalog JSON"
    )
    parser.add_argument("--manifest", type=Path, help="Desktop manifest to compare with core")
    args = parser.parse_args(argv)
    print(
        json.dumps(
            asyncio.run(
                smoke(
                    args.runtime.resolve(),
                    args.fixture.resolve(),
                    args.reference,
                    args.manifest,
                )
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
