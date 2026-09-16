"""Assemble client directories from one verified native runtime and one shared skill.

The output contains review candidates, not published releases. MCPB validation and packing
use the separately pinned official CLI. No archive is signed or submitted automatically.
The historical assembler refuses format-2 runtimes. An explicit Docling Desktop path
assembles a development candidate for local installation checks, never a signed release.
WORKFLOW.md is a review copy; actual model instructions come from the pinned core server.
The selected-documents variant removes the directory setting and adds a co-located GUI app.
Its wrapper starts the verified worker without user-controlled shell interpolation.
The helper wrapper and plist have package hashes; signing remains a distribution gate.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import shutil
from pathlib import Path

from runtime.verify import sha256, verify_release

REPOSITORY = Path(__file__).resolve().parent.parent


def package_clients(runtime: Path, output: Path) -> dict[str, Path]:
    metadata = verify_release(runtime)
    if metadata["format_version"] != "1":
        raise ValueError(
            "Use --docling-desktop for a local Docling candidate; other clients await native setup."
        )
    if output.exists():
        raise ValueError("Choose a new package output directory.")
    paths = {}
    for client in ["claude-desktop", "claude-code", "codex"]:
        target = output / client
        if client != "claude-desktop":
            target = target / "plugins" / "openreading-local-proof"
        shutil.copytree(
            REPOSITORY / "clients" / client,
            target,
            ignore=shutil.ignore_patterns("docling", "historical", "selection", "chat"),
        )
        if client == "claude-desktop":
            # The repository index describes newer candidates that this archive cannot run.
            shutil.copy2(
                REPOSITORY / "clients/claude-desktop/historical/README.md", target / "README.md"
            )
        shutil.copytree(runtime, target / "server", symlinks=True)
        if client != "claude-desktop":
            shutil.copytree(REPOSITORY / "skills", target / "skills")
        verify_release(target / "server")
        paths[client] = target
    claude = output / "claude-code/.claude-plugin/marketplace.json"
    claude.parent.mkdir(parents=True)
    claude.write_text(
        json.dumps(
            {
                "name": "openreading-local-review",
                "owner": {"name": "OpenReading"},
                "plugins": [
                    {
                        "name": "openreading-local-proof",
                        "source": "./plugins/openreading-local-proof",
                    }
                ],
            },
            indent=2,
        )
        + "\n"
    )
    codex = output / "codex/.agents/plugins/marketplace.json"
    codex.parent.mkdir(parents=True)
    codex.write_text(
        json.dumps(
            {
                "name": "openreading-local-review",
                "interface": {"displayName": "OpenReading local review"},
                "plugins": [
                    {
                        "name": "openreading-local-proof",
                        "source": {"source": "local", "path": "./plugins/openreading-local-proof"},
                        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                        "category": "Productivity",
                    }
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return paths


def package_docling_desktop(
    runtime: Path, output: Path, *, selection: bool = False, chat: bool = False
) -> Path:
    if selection and chat:
        raise ValueError("Choose one selection candidate mode.")
    metadata = verify_release(runtime)
    if metadata["format_version"] != "2":
        raise ValueError("The Desktop development candidate requires a Docling runtime.")
    if output.exists():
        raise ValueError("Choose a new package output directory.")
    if "_internal/openreading/artifacts/document.py" not in metadata["files"]:
        raise ValueError("Rebuild with full normalized document access before using this manifest.")
    delivery_schema = "_internal/openreading/schemas/document-tool.v0.3.json"
    try:
        if not {
            delivery_schema,
            "_internal/openreading/artifacts/delivery.py",
            "_internal/openreading/mcp_server/delivery.py",
        }.issubset(metadata["files"]):
            raise ValueError
        delivery = json.loads((runtime / delivery_schema).read_text())
        if "TextOriginCounts" not in delivery["$defs"]:
            raise ValueError
        if set(delivery["$defs"]["DeliveryRequest"]["properties"]["delivery"]["enum"]) != {
            "fragments",
            "auto",
            "file",
        }:
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError("Rebuild with complete delivery before using this manifest.") from None
    if "_internal/openreading/artifacts/jobs.py" not in metadata["files"]:
        raise ValueError("Rebuild with background import support before using this manifest.")
    job_schema = "_internal/openreading/schemas/import-job.v0.2.json"
    try:
        if job_schema not in metadata["files"]:
            raise ValueError
        contract = json.loads((runtime / job_schema).read_text())
        if (
            not isinstance(contract, dict)
            or not isinstance(contract.get("$defs"), dict)
            or not {"ListRequest", "PageProgress"}.issubset(contract["$defs"])
        ):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError("Rebuild with job discovery before using this manifest.") from None
    if "_internal/openreading/mcp_server/selection.py" not in metadata["files"]:
        raise ValueError("Rebuild with the core selection contract before using this manifest.")
    if chat:
        try:
            contract = json.loads(
                (runtime / "_internal/openreading/schemas/selection-tool.v0.2.json").read_text()
            )
            if (
                "SelectionPage" not in contract["$defs"]
                or "cursor" not in contract["$defs"]["Request"]["properties"]
            ):
                raise ValueError
            if not {
                "_internal/runtime/native_selection.py",
                "_internal/runtime/snapshot_selection.py",
                "_internal/openreading/mcp_server/selection_pages.py",
            }.issubset(metadata["files"]):
                raise ValueError
        except (OSError, ValueError, KeyError, TypeError):
            raise ValueError(
                "Rebuild with snapshot selection before using this manifest."
            ) from None
    if (selection or chat) and not {
        "_internal/runtime/selection.py",
        "_internal/_tcl_data/init.tcl",
        "_internal/_tk_data/tk.tcl",
    }.issubset(metadata["files"]):
        raise ValueError("Rebuild the runtime with the file picker and bundled Tcl/Tk resources.")
    if chat and not {
        "_internal/runtime/chat_selection.py",
        "_internal/openreading/mcp_server/selection.py",
    }.issubset(metadata["files"]):
        raise ValueError("Rebuild with the chat chooser and core selection contract.")
    shutil.copytree(REPOSITORY / "clients/claude-desktop/docling", output)
    shutil.copytree(runtime, output / "server", symlinks=True)
    shutil.copy2(REPOSITORY / "skills/read-local-document/SKILL.md", output / "WORKFLOW.md")
    verify_release(output / "server")
    helper_metadata = {}
    if selection:
        manifest = json.loads((output / "manifest.json").read_text())
        manifest["name"] = "openreading-file-selection-preview"
        manifest["display_name"] = "OpenReading Selected Documents (development)"
        manifest["long_description"] = (
            "The launcher disables ONNX Runtime telemetry before the document engine starts. "
            "Local file-selection development preview. Use the included OpenReading Choose Document app "
            "to select a PDF, then copy its reference into chat. No directory configuration is required. "
            "Selected source copies and evidence stay locally until removed. Requested document content enters "
            "your assistant context. OCR is optional and can misread printed text; verify important quotes "
            "against the source page. This unsigned candidate does not establish public installation or token savings."
            "\n\nOpenReading Managed: Coming soon\nDocument processing on OpenReading's servers, without managing local compute. Planned after the public OSS launch."
        )
        del manifest["user_config"]["input_root"]
        manifest["server"]["mcp_config"]["args"] = [
            "--client",
            "claude-desktop",
            "--selected-documents",
            "--ocr",
            "${user_config.ocr}",
        ]
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.copy2(
            REPOSITORY / "clients/claude-desktop/selection/README.md", output / "README.md"
        )
        contents = output / "OpenReading Choose Document.app/Contents"
        executable = contents / "MacOS/openreading-select"
        executable.parent.mkdir(parents=True)
        executable.write_text(
            '#!/bin/sh\nset -eu\nbase=$(/usr/bin/dirname "$0")\nexec "$base/../../../server/openreading-worker" --client claude-desktop --select-document\n'
        )
        executable.chmod(0o755)
        (contents / "Info.plist").write_bytes(
            plistlib.dumps(
                {
                    "CFBundleExecutable": "openreading-select",
                    "CFBundleIdentifier": "ai.openreading.selection.preview",
                    "CFBundleName": "OpenReading Choose Document",
                    "CFBundlePackageType": "APPL",
                    "CFBundleVersion": "1",
                    "CFBundleShortVersionString": "0.2.0",
                    "NSHighResolutionCapable": True,
                }
            )
        )
        helper_metadata = {
            "helper_sha256": sha256(executable),
            "helper_info_sha256": sha256(contents / "Info.plist"),
        }
    if chat:
        manifest = json.loads((output / "manifest.json").read_text())
        manifest["name"] = "openreading-chat-selection-preview"
        manifest["display_name"] = "OpenReading Chat Documents (development)"
        manifest["long_description"] = (
            "The launcher disables ONNX Runtime telemetry before the document engine starts. "
            "Ask OpenReading to choose a local PDF. Choose your document in its OS file dialog, "
            "then ask a question in chat. OpenReading processes it locally with automatic OCR. "
            "Selected copies and evidence remain locally until removed; requested document content enters "
            "your assistant context. OCR can misread words and identifiers. Verify important "
            "quotes against the printed page. Use Cancel in the file dialog to dismiss it; "
            "the chat Stop button may not cancel local work. This unsigned development candidate "
            "does not establish public installation or measured token savings."
            "\n\nOpenReading Managed: Coming soon"
        )
        manifest["user_config"] = {
            "document_response_bytes": {
                "type": "number",
                "title": "Complete result response budget (bytes)",
                "description": "Advanced delivery setting. Enter a whole number of at least 4096. Default 1000000 counts the serialized MCP response. Larger results are saved under Downloads/OpenReading; document processing is not limited.",
                "default": 1_000_000,
                "min": 4096,
                "required": False,
            }
        }
        manifest["server"]["mcp_config"]["args"] = [
            "--client",
            "claude-desktop",
            "--chat-documents",
            "--document-response-bytes",
            "${user_config.document_response_bytes}",
        ]
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.copy2(REPOSITORY / "clients/claude-desktop/chat/README.md", output / "README.md")
    # Bind the review materials without claiming these hashes authenticate a publisher.
    (output / "package-info.json").write_text(
        json.dumps(
            {
                "distribution": "development-only",
                **helper_metadata,
                "core_commit": metadata["core_commit"],
                "worker_sha256": metadata["worker_sha256"],
                "manifest_sha256": sha256(output / "manifest.json"),
                "workflow_sha256": sha256(output / "WORKFLOW.md"),
            },
            indent=2,
        )
        + "\n"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--docling-desktop",
        action="store_true",
        help="assemble only a development Docling Desktop candidate for local checks",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--chat-documents",
        action="store_true",
        help="assemble the chat chooser candidate with automatic OCR",
    )
    modes.add_argument(
        "--selected-documents",
        action="store_true",
        help="with --docling-desktop, assemble the separate file-picker development candidate",
    )
    args = parser.parse_args()
    if (args.selected_documents or args.chat_documents) and not args.docling_desktop:
        parser.error("Selection candidates require --docling-desktop")
    if args.docling_desktop:
        paths = {
            "claude-desktop": package_docling_desktop(
                args.runtime.resolve(),
                args.output.resolve(),
                selection=args.selected_documents,
                chat=args.chat_documents,
            )
        }
    else:
        paths = package_clients(args.runtime.resolve(), args.output.resolve())
    print(json.dumps({name: str(path) for name, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
