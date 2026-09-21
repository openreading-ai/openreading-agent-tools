"""Wrap a verified Docling Desktop candidate in Claude's plugin ZIP format.

This build-only operation never installs a plugin, changes host settings, or starts
any worker or helper. The input is an assembled extension, not an arbitrary archive.
Its runtime inventory and package-owned hashes must verify before output is created.
The source may pin an unmerged Core candidate; its exact identity remains in the receipt.
The current shared skill replaces the source extension workflow after input verification.
Its output hash and workflow version suffix distinguish guidance updates without rebuilding
the parser or accepting an unverified change to the source extension.

The plugin retains the claude-desktop namespace and its Settings helper so existing
candidate data stays discoverable. Do not enable the extension and plugin together:
both registrations expose the same tools and use the same saved processing destination.
Cowork upload, native launch, signing, and clean-machine acceptance remain separate gates.
The current archive supports regular-file runtimes; symlinks refuse rather than relying
on host-specific ZIP extraction behavior. Python and Docling are inside the runtime.
The optional first-use runtime download keeps compressed and expanded plugin sizes
below Claude's 200 MB limits. Packaging never performs or publishes that download.
The runtime payload retains local Docling and the reviewed optional server destination.
"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from runtime.claude_bootstrap import launcher
from runtime.runtime_download import pack, validate_base_url
from runtime.verify import sha256, verify_release

HELPER = "OpenReading Settings.app/Contents/MacOS/openreading-settings"
PLIST = "OpenReading Settings.app/Contents/Info.plist"
NAME = "openreading-local-documents"
REPOSITORY = Path(__file__).resolve().parent.parent
MAX_ARCHIVE_BYTES = 200_000_000
MAX_EXPANDED_BYTES = 200_000_000


def build(extension: Path, output: Path, *, runtime_base_url: str | None = None) -> Path:
    if output.exists():
        raise ValueError("Choose a new output directory.")
    if runtime_base_url is not None:
        validate_base_url(runtime_base_url)
    runtime = extension / "server"
    metadata = verify_release(runtime)
    if metadata["format_version"] != "2":
        raise ValueError("A verified Docling candidate is required.")
    info = json.loads((extension / "package-info.json").read_text())
    for key in ("core_commit", "worker_sha256"):
        if info[key] != metadata[key]:
            raise ValueError("Extension and runtime identity differ.")
    bound = {
        "manifest.json": "manifest_sha256",
        "WORKFLOW.md": "workflow_sha256",
        HELPER: "helper_sha256",
        PLIST: "helper_info_sha256",
    }
    for name, key in bound.items():
        if sha256(extension / name) != info[key]:
            raise ValueError(f"Extension file changed: {name}")
    if any(path.is_symlink() for path in extension.rglob("*")):
        raise ValueError("Plugin archive requires regular files, without symlinks.")
    source_manifest = json.loads((extension / "manifest.json").read_text())
    if "--chat-documents" not in source_manifest["server"]["mcp_config"]["args"]:
        raise ValueError("A chat-document extension is required.")
    if not (extension / HELPER).stat().st_mode & 0o111:
        raise ValueError("Settings helper must be executable.")

    target = output / "plugin"
    (target / ".claude-plugin").mkdir(parents=True)
    download = None
    if runtime_base_url is None:
        shutil.copytree(runtime, target / "server")
    else:
        download = pack(runtime, output / "runtime", runtime_base_url)
    for name in (HELPER, PLIST):
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extension / name, destination)
    skill = target / "skills/read-local-document/SKILL.md"
    skill.parent.mkdir(parents=True)
    shutil.copy2(REPOSITORY / "skills/read-local-document/SKILL.md", skill)
    manifest = {
        "name": NAME,
        "version": source_manifest["version"] + ".workflow.1",
        "description": "Read selected local documents with bundled Docling and exact evidence. Optional Core server processing.",
        "author": {"name": "OpenReading"},
        "skills": "./skills/",
        "mcpServers": "./.mcp.json",
    }
    (target / ".claude-plugin/plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
    config = {
        "mcpServers": {
            "openreading": {
                "command": "${CLAUDE_PLUGIN_ROOT}/server/openreading-worker",
                "args": ["--client", "claude-desktop", "--chat-documents"],
            }
        }
    }
    if download is not None:
        manifest["version"] += ".bootstrap.2"
        manifest["description"] += (
            " First use downloads the verified runtime; internet required for setup."
        )
        (target / ".claude-plugin/plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
        config["mcpServers"]["openreading"] = {
            "command": "/bin/sh",
            "args": ["${CLAUDE_PLUGIN_ROOT}/launch.sh", "--chat-documents"],
        }
        (target / "launch.sh").write_text(
            launcher(metadata, sha256(runtime / "release.json"), download)
        )
        (target / "launch.sh").chmod(0o755)
        (target / HELPER).write_text(
            '#!/bin/sh\nset -eu\nbase=$(/usr/bin/dirname "$0")\nexec /bin/sh "$base/../../../launch.sh" --destination-settings\n'
        )
    (target / ".mcp.json").write_text(json.dumps(config, indent=2) + "\n")
    shutil.copy2(
        Path(__file__).resolve().parent.parent / "clients/claude-cowork/README.md",
        target / "README.md",
    )
    if download is None:
        verify_release(target / "server")
    package_files = {
        path.relative_to(target).as_posix(): sha256(path)
        for path in sorted(target.rglob("*"))
        if path.is_file() and not path.is_relative_to(target / "server")
    }
    receipt = {
        "distribution": "development-only",
        "runtime_download": download,
        "runtime_release_sha256": sha256(runtime / "release.json"),
        "runtime_asset_published": False,
        "target": "Claude Cowork on macOS arm64; native acceptance pending",
        "version": manifest["version"],
        "core_commit": metadata["core_commit"],
        "worker_sha256": metadata["worker_sha256"],
        "source_package_info_sha256": sha256(extension / "package-info.json"),
        "package_files": package_files,
    }
    (target / "package-info.json").write_text(json.dumps(receipt, indent=2) + "\n")
    archive = output / "openreading-claude-cowork.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as packed:
        for path in sorted(target.rglob("*")):
            if path.is_file():
                packed.write(path, path.relative_to(target).as_posix())
    with zipfile.ZipFile(archive) as packed:
        expanded = sum(item.file_size for item in packed.infolist())
    if expanded > MAX_EXPANDED_BYTES:
        archive.unlink()
        raise ValueError("Claude plugin uncompressed size exceeds the 200 MB limit.")
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        archive.unlink()
        raise ValueError(
            "Claude plugin exceeds the 200 MB upload limit. Use --runtime-base-url for a separate runtime payload."
        )
    receipt.update(
        archive_sha256=sha256(archive),
        archive_bytes=archive.stat().st_size,
        archive_expanded_bytes=expanded,
    )
    (output / "candidate.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return archive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extension", required=True, type=Path, help="verified assembled chat extension"
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="new directory for the plugin and ZIP"
    )
    parser.add_argument(
        "--runtime-base-url",
        help="HTTPS asset directory for a separate pinned runtime download; does not publish it",
    )
    args = parser.parse_args(argv)
    print(
        build(
            args.extension.resolve(), args.output.resolve(), runtime_base_url=args.runtime_base_url
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
