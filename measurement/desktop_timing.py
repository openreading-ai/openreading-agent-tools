"""Read Claude Desktop's compact MCP log without exporting document payloads.

This diagnostic pairs numeric request IDs within log-boundary segments.
It recognizes the compact 'Message from client: method="..." id=N params' format.
Payloads, connector names and file paths are discarded. Input bytes bind the report
by SHA-256; this is not authentication of a log supplied by a reviewer.

Durations measure host-log request/response intervals, including transport, server work and possibly host approval waiting. They do not isolate parsing, identify a document, prove success, measure model
thinking, or measure the complete question-to-answer interval. Missing endpoints stay
unknown. Inter-call gaps are shown only after all preceding calls have completed.
Clock rollback, repeated IDs and incompatible message formats refuse rather than
producing plausible timings. Initialization, transport close and shutdown start new segments; do not concatenate
logs from separate connectors or concurrent server processes.

Run python -m measurement.desktop_timing --log PATH. No server or model is invoked.
The CLI emits JSON to stdout: exit 0 for paired calls, 1 for incomplete pairing, or
2 for invalid input. Format 3 records result/error transport markers without payloads.
Unknown response markers stay unknown; missing or ambiguous responses stay null.
A result can contain a tool-level failure, so this is not application success. Segment numbers are not process or conversation identities.
Server requests use a separate ID namespace. Interrupted requests taint their IDs
for the rest of the log, so late responses cannot supply plausible new durations. Exception messages and the selected input path are never printed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HEADER = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z) \[[^\n]*?\] \[[A-Za-z]+\] (.*)$")
REQUEST = re.compile(
    r'^Message from (client|server): method="([a-zA-Z/_]+)"(?: id=(0|[1-9][0-9]*))? params\b'
)
RESPONSE = re.compile(r"^Message from (client|server): id=(0|[1-9][0-9]*)(?:\s|$)")


def summarize(stream):
    digest = hashlib.sha256()
    pending, seen, responded = {}, set(), set()
    calls, initializations = [], []
    segment, unmatched, abandoned, ambiguous = 0, 0, 0, 0
    initialized = False
    tainted = set()
    last_stamp = None
    for raw in stream:
        digest.update(raw)
        line = raw.decode("utf-8").rstrip("\r\n")
        header = HEADER.match(line)
        if not header:
            continue
        timestamp, message = header.groups()
        boundary = message.startswith(("Client transport closed", "Shutting down server"))
        if not boundary and not message.startswith(
            ("Message from client:", "Message from server:")
        ):
            continue
        stamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if last_stamp is not None and stamp < last_stamp:
            raise ValueError("The log clock moved backwards.")
        last_stamp = stamp
        incoming, outgoing = REQUEST.match(message), RESPONSE.match(message)
        initialization = incoming is not None and incoming.groups()[:2] == ("client", "initialize")
        if boundary or initialization:
            abandoned += len(pending)
            tainted.update(pending)
            segment += 1
            initialized = initialization
            pending, seen, responded = {}, set(), set()
        if boundary:
            continue
        if incoming:
            direction, method, identifier = incoming.groups()
            if identifier is None:
                if not method.startswith("notifications/"):
                    raise ValueError("An observed request has no supported numeric ID.")
                continue
            key = (direction, identifier)
            if key in seen:
                raise ValueError("Request IDs repeat without initialization.")
            seen.add(key)
            row = None
            if direction == "client" and method in ("tools/call", "initialize"):
                row = {
                    "segment": segment,
                    "request_id": int(identifier),
                    "started_at": timestamp,
                    "seconds": None,
                    "outcome": None,
                }
                if method == "tools/call":
                    row.update(initialization_observed=initialized, gap_before_seconds=None)
                    calls.append(row)
                else:
                    initializations.append(row)
            pending[key] = (stamp, row)
        elif outgoing:
            direction, identifier = outgoing.groups()
            key = ("client" if direction == "server" else "server", identifier)
            if key in responded:
                raise ValueError("A response is duplicated.")
            responded.add(key)
            if key not in pending:
                unmatched += 1
                continue
            start, row = pending.pop(key)
            if key in tainted:
                ambiguous += 1
                continue
            if row is not None:
                row["seconds"] = (stamp - start).total_seconds()
                row["responded_at"] = timestamp
                marker = re.match(r"(result|error)(?=[\s(]|$)", message[outgoing.end() :].lstrip())
                row["outcome"] = marker[1] if marker else "unknown"
        elif re.match(
            r'^Message from (?:client|server): method="notifications/[a-zA-Z/_]+"(?:\s|$)', message
        ):
            continue
        else:
            raise ValueError("The compact message format is unsupported.")
    if not calls:
        raise ValueError("No recognizable tool calls were found.")
    # A concurrent or unfinished call makes the previous idle interval unknowable.
    previous_segment, latest_end, unfinished = None, None, False
    for row in calls:
        if row["segment"] != previous_segment:
            previous_segment, latest_end, unfinished = row["segment"], None, False
        start = datetime.fromisoformat(row["started_at"])
        if not unfinished and latest_end is not None and latest_end <= start:
            row["gap_before_seconds"] = (start - latest_end).total_seconds()
        if row["seconds"] is None:
            unfinished = True
        else:
            end = datetime.fromisoformat(row["responded_at"])
            latest_end = max(latest_end, end) if latest_end is not None else end
    complete = (
        unmatched == 0
        and abandoned == 0
        and ambiguous == 0
        and not pending
        and all(row["seconds"] is not None for row in calls + initializations)
    )
    return {
        "format_version": "3",
        "scope": "Claude Desktop compact MCP log intervals; no document or model attribution",
        "log_sha256": digest.hexdigest(),
        "pairing": "observed_pairs_complete" if complete else "incomplete",
        "segment_identity": "log boundaries only; process and conversation identity unverified",
        "unanswered_requests": abandoned + len(pending),
        "ambiguous_responses": ambiguous,
        "unmatched_responses": unmatched,
        "document": None,
        "parser_seconds": None,
        "answer_seconds": None,
        "token_savings": "unmeasured",
        "initializations": initializations,
        "calls": calls,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True, help="one compact Desktop MCP log")
    args = parser.parse_args(argv)
    try:
        with args.log.open("rb") as stream:
            report = summarize(stream)
    except (ValueError, OSError) as error:
        print(f"Timing diagnostic refused: {type(error).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["pairing"] == "observed_pairs_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
