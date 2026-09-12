"""Check annotated answer citations against captured calls and the public MCP read tool.

Capture v1 contains ordered request, response and one final answer event. Host adapters
must preserve complete tool payloads and provenance of that capture outside the grant.
The review binds the capture bytes and supplies Unicode code-point spans into the answer.
Filename and physical-page labels are exact; OCR/mixed evidence needs a visible origin label.
A reviewer must attest citation inventory completeness. This cannot detect an omitted
citation in arbitrary prose or authenticate a fabricated capture. A pass verifies evidence
links, never answer correctness, instruction adherence, host support or token savings.

Use the ordinary runtime environment as a protocol client. The CLI verifies and starts
an explicit frozen v2 runtime, then resolves evidence through openreading_read. It never
imports the historical runtime's core API or reads the artifact store's private files.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from runtime.verify import verify_release


def require(condition, message):
    if not condition:
        raise ValueError(message)


def closed(value, keys):
    require(
        isinstance(value, dict) and set(value) == set(keys.split()),
        "Unsupported citation input fields.",
    )


def span(answer, bounds):
    require(
        isinstance(bounds, list) and len(bounds) == 2 and all(type(v) is int for v in bounds),
        "Invalid answer span.",
    )
    start, end = bounds
    require(0 <= start < end <= len(answer), "Answer span is out of bounds.")
    return answer[start:end]


def label(answer, bounds):
    value = span(answer, bounds)
    start, end = bounds
    suffix = answer[end:]
    # Prefix selections cannot turn another filename or physical page into a match.
    require(start == 0 or not answer[start - 1].isalnum(), "Label starts inside a token.")
    require(
        not suffix
        or not (
            suffix[0].isalnum()
            or suffix[0] in "_/-\\"
            or (suffix.startswith(".") and len(suffix) > 1 and suffix[1].isalnum())
        ),
        "Label continues outside its annotation.",
    )
    return value


def payload(result):
    require(isinstance(result, dict) and result.get("isError", False) is False, "Tool call failed.")
    content = result.get("content", [])
    require(
        len(content) == 1 and content[0].get("type") == "text",
        "Tool payload is incomplete or ambiguous.",
    )
    parsed = json.loads(content[0]["text"])
    require(
        isinstance(parsed, dict)
        and parsed.get("schema_version") == "0.3"
        and "error" not in parsed,
        "Unsupported tool response.",
    )
    structured = result.get("structuredContent")
    require(structured is None or structured == parsed, "Tool response encodings disagree.")
    return parsed


def captured(capture):
    closed(capture, "format_version host complete tools events")
    require(
        type(capture["format_version"]) is int
        and capture["format_version"] == 1
        and capture["complete"] is True,
        "Complete capture v1 is required.",
    )
    closed(capture["host"], "application version mode")
    require(
        all(isinstance(v, str) and v.strip() for v in capture["host"].values()),
        "Host identity is incomplete.",
    )
    closed(capture["tools"], "import search read")
    names = capture["tools"]
    require(
        all(isinstance(v, str) and v for v in names.values()) and len(set(names.values())) == 3,
        "Tool names are ambiguous.",
    )
    events = capture["events"]
    require(
        isinstance(events, list) and events and events[-1].get("kind") == "answer",
        "A final captured answer is required.",
    )
    closed(events[-1], "kind text")
    require(isinstance(events[-1]["text"], str) and events[-1]["text"], "Answer text is missing.")
    requests, responses = {}, {}
    for index, event in enumerate(events[:-1]):
        kind = event.get("kind")
        require(kind in ("request", "response"), "Unexpected capture event or answer ordering.")
        identifier = event.get("id")
        require(
            isinstance(identifier, str) and identifier, "Capture call IDs must be nonempty strings."
        )
        if kind == "request":
            closed(event, "kind id name arguments")
            require(
                identifier not in requests and isinstance(event["arguments"], dict),
                "Duplicate call ID or invalid arguments.",
            )
            requests[identifier] = (index, event)
        else:
            closed(event, "kind id result")
            require(
                identifier in requests and identifier not in responses,
                "Missing request or duplicate response.",
            )
            responses[identifier] = (index, event["result"])
    require(requests.keys() == responses.keys(), "Capture has unfinished calls.")
    return events[-1]["text"], names, requests, responses


def passage(result, artifact, evidence):
    require(result.get("artifact_id") == artifact, "Read returned another artifact.")
    matches = [p for p in result.get("passages", []) if p.get("evidence_id") == evidence]
    require(len(matches) == 1, "Read evidence is missing or ambiguous.")
    return matches[0]


async def check(capture, review, resolve):
    """Resolve each citation using an async callable returning a public ReadResult dict."""
    closed(review, "format_version capture_sha256 citations_complete citations")
    require(
        type(review["format_version"]) is int
        and review["format_version"] == 1
        and review["citations_complete"] is True,
        "A complete human citation inventory is required.",
    )
    answer, names, requests, responses = captured(capture)
    citations = review["citations"]
    require(isinstance(citations, list) and citations, "No reviewed citations were supplied.")
    seen = set()
    for citation in citations:
        closed(
            citation,
            "artifact_id evidence_id page text_origin import_call search_call read_call quote_span filename_span page_span origin_span",
        )
        artifact, evidence = citation["artifact_id"], citation["evidence_id"]
        require(
            isinstance(artifact, str)
            and isinstance(evidence, str)
            and type(citation["page"]) is int
            and citation["page"] > 0,
            "Invalid citation identity.",
        )
        require(
            citation["text_origin"] in ("native", "ocr", "mixed", "unknown", None),
            "Invalid text origin.",
        )
        results = {}
        previous = -1
        for verb in ("import", "search", "read"):
            identifier = citation[f"{verb}_call"]
            require(
                isinstance(identifier, str) and identifier in requests,
                "Citation references an uncaptured call.",
            )
            started, request = requests[identifier]
            finished, response = responses[identifier]
            require(
                request["name"] == names[verb] and previous < started < finished,
                "Citation call order or tool differs.",
            )
            previous = finished
            result = payload(response)
            require(result.get("artifact_id") == artifact, "Captured call names another artifact.")
            arguments = request["arguments"]
            if verb != "import":
                require(arguments.get("artifact_id") == artifact, "Requested artifact differs.")
            if verb == "read":
                require(
                    evidence in arguments.get("evidence_ids", []), "Evidence was not requested."
                )
            results[verb] = result
        hit = [h for h in results["search"].get("hits", []) if h.get("evidence_id") == evidence]
        require(len(hit) == 1, "Search did not return this evidence uniquely.")
        saved = passage(results["read"], artifact, evidence)
        retained = await resolve(artifact, evidence)
        actual = passage(retained, artifact, evidence)
        require(actual == saved, "Captured passage differs from verified retained evidence.")
        require(
            all(
                item.get("page") == citation["page"]
                and item.get("text_origin") == citation["text_origin"]
                for item in (saved, hit[0])
            ),
            "Page or origin differs from citation.",
        )
        excerpt = hit[0]
        bounds = [excerpt.get("excerpt_start"), excerpt.get("excerpt_end")]
        require(
            span(saved["text"], bounds) == excerpt.get("excerpt"),
            "Search excerpt differs from retained text.",
        )
        quote = span(answer, citation["quote_span"])
        require(quote in actual["text"], "Answer quote is not verbatim evidence.")
        filename = label(answer, citation["filename_span"])
        require(
            all(
                result.get("display_name") == filename
                for result in (results["import"], results["read"], retained)
            ),
            "Answer filename differs from source.",
        )
        require(
            label(answer, citation["page_span"]) == f"physical PDF page {citation['page']}",
            "Visible physical-page label differs.",
        )
        origin = citation["text_origin"]
        if origin in ("ocr", "mixed") or citation["origin_span"] is not None:
            require(
                label(answer, citation["origin_span"]).casefold() == origin,
                "Visible origin label is missing or differs.",
            )
        key = tuple(citation["quote_span"])
        require(key not in seen, "A quote span has ambiguous citation annotations.")
        seen.add(key)
    return dict(
        format_version=1,
        verified_citations=len(citations),
        citation_evidence="passed",
        answer_quality="requires_human_review",
        native_host_support="unverified",
        host=capture["host"],
    )


async def check_files(capture_path, review_path, resolve):
    raw = capture_path.read_bytes()
    review_raw = review_path.read_bytes()
    review = json.loads(review_raw)
    require(
        review.get("capture_sha256") == hashlib.sha256(raw).hexdigest(),
        "Capture changed after citation review.",
    )
    result = await check(json.loads(raw), review, resolve)
    result["capture_sha256"] = hashlib.sha256(raw).hexdigest()
    result["review_sha256"] = hashlib.sha256(review_raw).hexdigest()
    return result


async def run(args):
    runtime = args.runtime.resolve()
    metadata = verify_release(runtime)
    require(metadata["format_version"] == "2", "Citation verification needs a frozen v2 runtime.")
    params = StdioServerParameters(
        command=str(runtime / "openreading-worker"),
        args=[
            "--client",
            args.client,
            "--input-root",
            str(args.input_root.resolve()),
            "--ocr",
            args.ocr,
        ],
        env={"PATH": "/usr/bin:/bin", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
    )
    async with (
        stdio_client(params) as (reader, writer),
        ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=60)) as session,
    ):
        await session.initialize()

        async def resolve(artifact, evidence):
            result = await session.call_tool(
                "openreading_read", {"artifact_id": artifact, "evidence_ids": [evidence]}
            )
            return payload(result.model_dump(mode="json", exclude_none=True))

        report = await check_files(args.capture, args.review, resolve)
    report.update(core_commit=metadata["core_commit"], worker_sha256=metadata["worker_sha256"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "review", "runtime", "input-root"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument(
        "--client", required=True, choices=["claude-desktop", "claude-code", "codex", "chatgpt"]
    )
    parser.add_argument("--ocr", default="off", choices=["on", "off"])
    args = parser.parse_args(argv)
    try:
        report = asyncio.run(run(args))
    except Exception as exc:
        print(json.dumps({"citation_evidence": "refused", "reason": type(exc).__name__}))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
