"""Assemble client directories from one verified native runtime and one shared skill.

The output contains review candidates, not published releases. MCPB validation and packing
use the separately pinned official CLI. No archive is signed or submitted automatically.
The historical assembler refuses format-2 runtimes. An explicit Docling Desktop path
assembles a development candidate for local installation checks, never a signed release.
The ChatGPT plugin path copies that same verified runtime into a relocatable local marketplace.
The host roots the explicit working directory; the executable path stays relative to it.
Legacy plugin MCP commands do not expand PLUGIN_ROOT. Packaging never changes host configuration.
The chatgpt storage namespace remains unchanged, including existing intake and exports.
WORKFLOW.md is a review copy; actual model instructions come from the pinned core server.
The selected-documents variant removes the directory setting and adds a co-located GUI app.
Its wrapper starts the verified worker without user-controlled shell interpolation.
Both chat packages include a Settings helper bound to their own client namespace.
The helper wrapper and plist have package hashes; signing remains a distribution gate.
The Cowork installer output separates a small native plugin upload from its bundled runtime.
Setup stages execution outside Downloads and backs up existing Claude state before a fresh trial.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import shutil
import zipfile
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
            REPOSITORY / "clients" / client / ("historical" if client == "claude-code" else ""),
            target,
            ignore=shutil.ignore_patterns("docling", "historical", "selection", "chat"),
        )
        if client in {"claude-desktop", "codex"}:
            # The repository index describes newer candidates that this archive cannot run.
            shutil.copy2(
                REPOSITORY / "clients" / client / "historical/README.md", target / "README.md"
            )
        shutil.copytree(runtime, target / "server", symlinks=True)
        if client != "claude-desktop":
            shutil.copytree(
                REPOSITORY / "skills",
                target / "skills",
                ignore=shutil.ignore_patterns("openreading-settings"),
            )
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


def _docling_runtime(runtime: Path, *, selection: bool = False, chat: bool = False) -> dict:
    metadata = verify_release(runtime)
    if metadata["format_version"] != "2":
        raise ValueError("The development candidate requires a Docling runtime.")
    if "_internal/openreading/artifacts/document.py" not in metadata["files"]:
        raise ValueError("Rebuild with full normalized document access before using this manifest.")
    delivery_schema = "_internal/openreading/schemas/document-tool.v0.4.json"
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
    job_schema = "_internal/openreading/schemas/import-job.v0.3.json"
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
                "_internal/openreading/adapters/docling_local/formats.py",
                "_internal/openreading/adapters/docling_local/unpaginated.py",
                "_internal/openreading/schemas/passage.v0.4.json",
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
    return metadata


def _server_destination(metadata: dict) -> None:
    if not {
        "_internal/runtime/server_profile.py",
        "_internal/runtime/server_imports.py",
        "_internal/runtime/server_selection.py",
        "_internal/runtime/server_transport.py",
        "_internal/runtime/destination_settings.py",
        "_internal/runtime/destination_ui.py",
        "_internal/runtime/settings_server.py",
        "_internal/runtime/app_settings.py",
        "_internal/runtime/storage_settings.py",
        "_internal/runtime/public_profile.py",
        "_internal/openreading/artifacts/retention.py",
        "_internal/openreading/schemas/local-document.v0.5.json",
        "_internal/openreading/schemas/agent-document-tool.v0.5.json",
        "_internal/openreading/schemas/import-job.v0.4.json",
    }.issubset(metadata["files"]):
        raise ValueError(
            "Rebuild with optional server destination support before packaging Settings."
        )


def _settings_helper(target: Path, client: str) -> tuple[Path, Path]:
    contents = target / "OpenReading Settings.app/Contents"
    executable = contents / "MacOS/openreading-settings"
    executable.parent.mkdir(parents=True)
    executable.write_text(
        f'#!/bin/sh\nset -eu\nbase=$(/usr/bin/dirname "$0")\nexec "$base/../../../server/openreading-worker" --client {client} --destination-settings\n'
    )
    executable.chmod(0o755)
    (contents / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleExecutable": "openreading-settings",
                "CFBundleIdentifier": f"ai.openreading.settings.{client}.preview",
                "CFBundleName": "OpenReading Settings",
                "CFBundlePackageType": "APPL",
                "CFBundleVersion": "1",
                "CFBundleShortVersionString": "0.2.0",
                "NSHighResolutionCapable": True,
            }
        )
    )
    return contents, executable


def package_chatgpt_plugin(runtime: Path, output: Path) -> Path:
    metadata = _docling_runtime(runtime, chat=True)
    _server_destination(metadata)
    if output.exists():
        raise ValueError("Choose a new package output directory.")
    target = output / "plugins/openreading-local-documents"
    shutil.copytree(REPOSITORY / "clients/chatgpt/plugin", target)
    shutil.copytree(runtime, target / "server", symlinks=True)
    shutil.copytree(REPOSITORY / "skills", target / "skills")
    verify_release(target / "server")
    # Bind package-owned inputs separately; the unchanged runtime retains its own inventory.
    files = [".codex-plugin/plugin.json", ".mcp.json", "README.md"]
    contents, executable = _settings_helper(target, "chatgpt")
    files.extend(
        path.relative_to(target).as_posix() for path in (executable, contents / "Info.plist")
    )
    files.extend(
        path.relative_to(target).as_posix() for path in (target / "skills").rglob("SKILL.md")
    )
    (target / "package-info.json").write_text(
        json.dumps(
            {
                "distribution": "development-only",
                "core_commit": metadata["core_commit"],
                "worker_sha256": metadata["worker_sha256"],
                "package_files": {name: sha256(target / name) for name in sorted(files)},
            },
            indent=2,
        )
        + "\n"
    )
    marketplace = output / ".agents/plugins/marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        json.dumps(
            {
                "name": "openreading-chatgpt-development",
                "interface": {"displayName": "OpenReading development preview"},
                "plugins": [
                    {
                        "name": "openreading-local-documents",
                        "source": {
                            "source": "local",
                            "path": "./plugins/openreading-local-documents",
                        },
                        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                        "category": "Productivity",
                    }
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return target


def package_cowork_plugin(runtime: Path, output: Path) -> Path:
    """Assemble a self-contained local Cowork candidate with a separate Settings connector."""
    metadata = _docling_runtime(runtime, chat=True)
    _server_destination(metadata)
    if output.exists():
        raise ValueError("Choose a new package output directory.")
    (output / ".claude-plugin").mkdir(parents=True)
    (output / ".claude-plugin/plugin.json").write_text(
        json.dumps(
            {
                "name": "openreading-local-documents",
                "version": "0.2.0-alpha.6",
                "description": "Local document tools and native OpenReading Settings. Development candidate.",
                "author": {"name": "OpenReading"},
            },
            indent=2,
        )
        + "\n"
    )
    servers = {}
    for name, flag in (
        ("openreading", "--chat-documents"),
        ("openreading-settings", "--settings-tools"),
    ):
        servers[name] = {
            "command": "${CLAUDE_PLUGIN_ROOT}/server/openreading-worker",
            "args": ["--client", "claude-desktop", flag],
        }
    (output / ".mcp.json").write_text(json.dumps({"mcpServers": servers}, indent=2) + "\n")
    shutil.copytree(runtime, output / "server", symlinks=True)
    shutil.copytree(REPOSITORY / "skills", output / "skills")
    shutil.copy2(REPOSITORY / "clients/claude-desktop/chat/README.md", output / "README.md")
    _settings_helper(output, "claude-desktop")
    verify_release(output / "server")
    files = {
        p.relative_to(output).as_posix(): sha256(p)
        for p in output.rglob("*")
        if p.is_file() and "server" not in p.relative_to(output).parts
    }
    (output / "package-info.json").write_text(
        json.dumps(
            {
                "distribution": "development-only",
                "core_commit": metadata["core_commit"],
                "worker_sha256": metadata["worker_sha256"],
                "package_files": files,
            },
            indent=2,
        )
        + "\n"
    )
    return output


def package_cowork_installer(runtime: Path, output: Path) -> Path:
    """Package an offline macOS setup command and Claude-owned plugin registration."""
    metadata = _docling_runtime(runtime, chat=True)
    _server_destination(metadata)
    if "_internal/runtime/fresh_install.py" not in metadata["files"]:
        raise ValueError("Rebuild with fresh-install support before packaging setup.")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(runtime, output / "runtime", symlinks=True)
    worker_hash = metadata["worker_sha256"]
    plugin = output / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin/plugin.json").write_text(
        json.dumps(
            {
                "name": "openreading-local-documents",
                "version": "0.2.0-alpha.7",
                "description": "OpenReading document tools and native settings. Uses the accompanying offline runtime installer.",
                "author": {"name": "OpenReading"},
            },
            indent=2,
        )
        + "\n"
    )
    (plugin / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    name: {"command": "/bin/sh", "args": ["${CLAUDE_PLUGIN_ROOT}/launch.sh", flag]}
                    for name, flag in (
                        ("openreading", "--chat-documents"),
                        ("openreading-settings", "--settings-tools"),
                    )
                }
            },
            indent=2,
        )
        + "\n"
    )
    launcher = plugin / "launch.sh"
    launcher.write_text(
        '#!/bin/sh\nset -eu\ncd "$HOME"\n'
        f'worker="$HOME/Library/Application Support/OpenReading/agent-tools/runtime-cache/{worker_hash}/openreading-worker"\n'
        'if [ ! -x "$worker" ]; then\n'
        '  echo "Run Install OpenReading.command from the matching setup package first." >&2\n'
        '  exit 2\nfi\nexec "$worker" --client claude-desktop "$@"\n'
    )
    launcher.chmod(0o755)
    shutil.copytree(REPOSITORY / "skills", plugin / "skills")
    (plugin / "README.md").write_text(
        "# OpenReading for Claude\n\nRun the accompanying offline installer before uploading this plugin.\n"
        "Use `/openreading-settings` for Processing, Storage and Advanced.\n"
        "The runtime lives in Application Support and never executes from the downloaded setup folder.\n"
        "This is a development build. Signing and clean-machine acceptance remain pending.\n"
    )
    with zipfile.ZipFile(output / "OpenReading-Claude.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(plugin.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(plugin))
    setup = output / "Install OpenReading.command"
    setup.write_text(
        """#!/bin/sh
set -eu
package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
install_base="$HOME/Library/Application Support/OpenReading/agent-tools"
for folder in "$HOME/Library" "$HOME/Library/Application Support" "$HOME/Library/Application Support/OpenReading" "$install_base"; do
  if [ -L "$folder" ]; then echo "Setup refuses a symbolic-link installation directory." >&2; exit 2; fi
done
mkdir -p "$install_base"
stage=$(mktemp -d "$install_base/.setup.XXXXXXXX")
trap 'rm -rf "$stage"' EXIT
echo "Copying the bundled runtime into Application Support..."
/usr/bin/ditto "$package_dir/runtime" "$stage/runtime"
actual=$(LC_ALL=C /usr/bin/shasum -a 256 "$stage/runtime/openreading-worker")
actual=${actual%% *}
"""
        + f'expected="{worker_hash}"\n'
        + """if [ "$actual" != "$expected" ]; then echo "Runtime checksum failed. Setup stopped." >&2; exit 2; fi
cd "$HOME"
"$stage/runtime/openreading-worker" --fresh-install
echo "Plugin to upload in Claude: $package_dir/OpenReading-Claude.zip"
"""
    )
    setup.chmod(0o755)
    (output / "OpenReading-test.md").write_text(
        "# OpenReading fresh-install check\n\nReference: OR-FRESH-001\n\n"
        "The test delivery contains 12 blue notebooks and 7 green folders.\n"
        "The total is 19 items.\n"
    )
    (output / "README.txt").write_text(
        "OPENREADING: FRESH CLAUDE INSTALL (macOS Apple Silicon)\n\n"
        "1. Finish or cancel OpenReading imports. Remove old OpenReading plugins/extensions in Claude.\n"
        "2. Quit Claude and close existing OpenReading Settings windows.\n"
        "3. Double-click Install OpenReading.command. Wait for the installed message in Terminal.\n"
        "4. Open Claude > Customize > Plugins > Add > Upload plugin. Select OpenReading-Claude.zip.\n"
        "5. Enable the plugin and accept its local-connector prompt.\n"
        "6. In a new Cowork task, run /openreading-settings.\n"
        "7. Check Processing, Storage and Advanced. Defaults are bundled Docling, ~/.openreading,\n"
        "   1000000 inline bytes and a 256 MiB server download limit. Save only changes you want.\n"
        "8. Reconnect the document connector after saving. Ask Claude to import a local document\n"
        "   with OpenReading and choose OpenReading-test.md. Ask for its reference and total.\n"
        "   Expected: OR-FRESH-001 and 19 items.\n\n"
        "Fresh setup backs up Claude's prior settings and default data partition. It does not delete them.\n"
        "Other clients and custom data directories stay intact. The backup path is printed.\n"
        "The installed runtime lives under ~/Library/Application Support/OpenReading/agent-tools/runtime-cache/.\n"
        "Claude manages the uploaded plugin. No user-installed Python, model download or server is required.\n"
        "After setup succeeds, the downloaded setup folder is not needed by the running plugin.\n"
        "Terminal may request access to Downloads while reading this installer. Normal runtime startup\n"
        "reads Application Support instead. Selecting documents in protected folders may require permission.\n\n"
        "This is a development build with ad-hoc signing. Signed distribution and clean-machine acceptance\n"
        "remain unverified. Optional Core server mode requires a separately running Core server.\n"
    )
    (output / "build.json").write_text(
        json.dumps(
            {
                "distribution": "development-only",
                "worker_sha256": worker_hash,
                "core_commit": metadata["core_commit"],
                "plugin_sha256": sha256(output / "OpenReading-Claude.zip"),
            },
            indent=2,
        )
        + "\n"
    )
    return output


def package_docling_desktop(
    runtime: Path, output: Path, *, selection: bool = False, chat: bool = False
) -> Path:
    if selection and chat:
        raise ValueError("Choose one selection candidate mode.")
    metadata = _docling_runtime(runtime, selection=selection, chat=chat)
    if chat:
        _server_destination(metadata)
    if output.exists():
        raise ValueError("Choose a new package output directory.")
    shutil.copytree(REPOSITORY / "clients/claude-desktop/docling", output)
    shutil.copytree(runtime, output / "server", symlinks=True)
    shutil.copy2(REPOSITORY / "skills/openreading/SKILL.md", output / "WORKFLOW.md")
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
        manifest["version"] = "0.2.0-alpha.3+server.20260920"
        manifest["display_name"] = "OpenReading Chat Documents (development)"
        manifest["long_description"] = (
            "The launcher disables ONNX Runtime telemetry before the document engine starts. "
            "Ask OpenReading to choose local documents or folders. The configured adapter supplies the supported formats. "
            "Bundled Docling processes selected documents locally with automatic OCR by default. "
            "OpenReading Settings can select your own Core server, with confirmation before sending selected bytes. "
            "Selected copies and evidence remain locally until removed; requested document content enters "
            "your assistant context. OCR can misread words and identifiers. Verify important "
            "quotes against the printed page. Use Cancel in the file dialog to dismiss it; "
            "the chat Stop button may not cancel local work. This unsigned development candidate "
            "does not establish public installation or measured token savings."
            "\n\nOpenReading Managed: Coming soon"
        )
        manifest["user_config"] = {}
        manifest["server"]["mcp_config"]["args"] = [
            "--client",
            "claude-desktop",
            "--chat-documents",
        ]
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.copy2(REPOSITORY / "clients/claude-desktop/chat/README.md", output / "README.md")
        contents, executable = _settings_helper(output, "claude-desktop")
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
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument(
        "--docling-desktop",
        action="store_true",
        help="assemble only a development Docling Desktop candidate for local checks",
    )
    targets.add_argument(
        "--cowork-installer",
        action="store_true",
        help="assemble offline fresh setup plus the Claude plugin upload archive",
    )
    targets.add_argument(
        "--cowork-plugin",
        action="store_true",
        help="assemble a self-contained Cowork development plugin with native settings",
    )
    targets.add_argument(
        "--chatgpt-plugin",
        action="store_true",
        help="assemble a development ChatGPT local plugin marketplace without host registration",
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
    if args.cowork_installer:
        paths = {"cowork": package_cowork_installer(args.runtime.resolve(), args.output.resolve())}
    elif args.cowork_plugin:
        paths = {"cowork": package_cowork_plugin(args.runtime.resolve(), args.output.resolve())}
    elif args.chatgpt_plugin:
        paths = {"chatgpt": package_chatgpt_plugin(args.runtime.resolve(), args.output.resolve())}
    elif args.docling_desktop:
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
