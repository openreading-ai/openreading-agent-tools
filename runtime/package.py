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
            ignore=shutil.ignore_patterns("docling", "historical", "selection"),
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


def package_docling_desktop(runtime: Path, output: Path, *, selection: bool = False) -> Path:
    metadata = verify_release(runtime)
    if metadata["format_version"] != "2":
        raise ValueError("The Desktop development candidate requires a Docling runtime.")
    if output.exists():
        raise ValueError("Choose a new package output directory.")
    if selection and not {
        "_internal/runtime/selection.py",
        "_internal/_tcl_data/init.tcl",
        "_internal/_tk_data/tk.tcl",
    }.issubset(metadata["files"]):
        raise ValueError("Rebuild the runtime with the file picker and bundled Tcl/Tk resources.")
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
            "Local file-selection development preview. Use the included OpenReading Choose Document app "
            "to select a PDF, then copy its reference into chat. No directory configuration is required. "
            "Selected source copies and evidence stay locally until removed. Retrieved evidence enters "
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
    parser.add_argument(
        "--selected-documents",
        action="store_true",
        help="with --docling-desktop, assemble the separate file-picker development candidate",
    )
    args = parser.parse_args()
    if args.selected_documents and not args.docling_desktop:
        parser.error("--selected-documents requires --docling-desktop")
    if args.docling_desktop:
        paths = {
            "claude-desktop": package_docling_desktop(
                args.runtime.resolve(), args.output.resolve(), selection=args.selected_documents
            )
        }
    else:
        paths = package_clients(args.runtime.resolve(), args.output.resolve())
    print(json.dumps({name: str(path) for name, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
