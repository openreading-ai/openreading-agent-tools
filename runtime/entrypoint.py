"""Launch the verified core worker without an end-user Python installation.

Unsupported hosts and unfrozen source execution return status 2 before inventory access.
The client name selects only its retained-store location. It cannot change the core
profile or backend. Explicit directory arguments are never interpreted by a shell.
The internal child dispatch uses the same frozen executable and verified inventory.
Format 2 supports --select-document for the GUI and --selected-documents for MCP.
The separate --chat-documents candidate installs a trusted local chooser and automatic OCR.
It ignores saved settings and refuses directory or OCR overrides.
The older selection modes reject directory configuration. MCP supplies private completed intake
copies and ignores saved grants; developer OCR remains an explicit argument, default off.

Environment variables this module reads
--------------------------------------
Format 2 sets ORT_DISABLE_TELEMETRY=1 before importing any core worker or parser module.
This process-wide startup opt-out overrides absent or inherited values and reaches children.
It suppresses ONNX Runtime's uploader and persistent device identifier at initialization.
The flag remains set for this dedicated executable's lifetime; it does not erase older data.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

from runtime.configuration import client_root, configure, read_grant
from runtime.verify import ReleaseIntegrityError, verify_release


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if sys.platform != "darwin" or platform.machine() != "arm64":
        print("This runtime requires macOS on Apple Silicon.", file=sys.stderr)
        return 2
    if not getattr(sys, "frozen", False):
        print(
            "Run the packaged worker. This entry point cannot verify a source installation.",
            file=sys.stderr,
        )
        return 2
    root = Path(sys.executable).parent
    try:
        metadata = verify_release(root)
    except ReleaseIntegrityError as error:
        print(str(error), file=sys.stderr)
        return 2
    if metadata.get("format_version") == "2":
        # The API opt-out is too late: ORT initializes telemetry while its native module loads.
        os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    if argv == ["--version"]:
        print(
            json.dumps(
                {key: metadata[key] for key in ["release_version", "core_commit", "worker_sha256"]}
            )
        )
        return 0
    if metadata.get("format_version") == "2" and argv[:1] == ["--internal-artifact-job"]:
        from openreading.artifacts.jobs import main as job_main

        return job_main(argv[1:])
    if argv[:1] == ["--internal-artifact-worker"]:
        from openreading.artifacts.worker import main as worker_main

        return worker_main(argv[1:])
    if metadata.get("format_version") == "2" and argv == ["--internal-select-file"]:
        from runtime.chat_selection import main as chooser_main

        return chooser_main()
    parser = argparse.ArgumentParser(
        description="Run the verified local OpenReading document tools."
    )
    docling = metadata.get("format_version") == "2"
    clients = ["claude-desktop", "claude-code", "codex"] + (["chatgpt"] if docling else [])
    parser.add_argument("--client", required=True, choices=clients)
    if docling:
        parser.add_argument(
            "--document-response-bytes",
            type=int,
            default=1_000_000,
            help="advanced complete-result delivery budget in serialized MCP bytes; default 1000000",
        )
        parser.add_argument("--ocr", help="setup-only OCR: on/true or off/false; default off")
        selection = parser.add_mutually_exclusive_group()
        selection.add_argument(
            "--chat-documents",
            action="store_true",
            help="select documents through chat with automatic local OCR",
        )
        selection.add_argument(
            "--selected-documents",
            action="store_true",
            help="serve only copies explicitly selected through the local picker",
        )
        selection.add_argument(
            "--select-document",
            action="store_true",
            help="open the local file picker; no source path argument",
        )
    parser.add_argument(
        "--configure", action="store_true", help="save an explicit input grant for this client"
    )
    parser.add_argument(
        "--input-root", type=Path, help="explicit document directory; no default grant"
    )
    args = parser.parse_args(argv)
    try:
        if docling:
            if args.document_response_bytes < 4096:
                raise ValueError("Document response bytes must be at least 4096.")
            from runtime.docling_profile import launch

            if args.selected_documents or args.select_document or args.chat_documents:
                if (
                    args.input_root is not None
                    or args.configure
                    or ((args.select_document or args.chat_documents) and args.ocr is not None)
                ):
                    raise ValueError(
                        "File selection cannot use directory configuration or picker OCR overrides."
                    )
                from runtime.selection import SelectionStore

                store = SelectionStore(args.client)
                if args.select_document:
                    from runtime.selection_ui import run

                    return run(store)
                args.input_root = store.prepare()
                if args.chat_documents:
                    from runtime.chat_selection import LocalSelectionProvider

                    args.ocr = "true"
                    return launch(args, root, selection_provider=LocalSelectionProvider(store))
            return launch(args, root)
        if args.configure:
            if args.input_root is None:
                raise ValueError("Setup requires --input-root with an explicit directory.")
            configure(args.client, args.input_root)
            print(
                "Directory configured. Source copies remain locally until removed. Retrieved excerpts enter your agent context."
            )
            return 0
        grant = args.input_root or read_grant(args.client)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    from openreading.mcp_server.main import main as core_main

    store = client_root(args.client) / "v1"
    return core_main(
        [
            "--profile",
            "local-document-proof-v1",
            "--input-root",
            str(grant),
            "--artifact-root",
            str(store),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
