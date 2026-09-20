"""Wrap a verified Docling Desktop candidate in Claude's plugin ZIP format.

This build-only operation never installs a plugin, changes host settings, or starts
any worker or helper. The input is an assembled extension, not an arbitrary archive.
Its runtime inventory and package-owned hashes must verify before output is created.
The source may pin an unmerged Core candidate; its exact identity remains in the receipt.

The plugin retains the claude-desktop namespace and its Settings helper so existing
candidate data stays discoverable. Do not enable the extension and plugin together:
both registrations expose the same tools and use the same saved processing destination.
Cowork upload, native launch, signing, and clean-machine acceptance remain separate gates.
The current archive supports regular-file runtimes; symlinks refuse rather than relying
on host-specific ZIP extraction behavior. Python and Docling are inside the runtime.
"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from runtime.verify import sha256, verify_release

HELPER = "OpenReading Settings.app/Contents/MacOS/openreading-settings"
PLIST = "OpenReading Settings.app/Contents/Info.plist"
NAME = "openreading-local-documents"


def build(extension: Path, output: Path) -> Path:
    if output.exists():
        raise ValueError("Choose a new output directory.")
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
    shutil.copytree(runtime, target / "server")
    for name in (HELPER, PLIST):
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extension / name, destination)
    skill = target / "skills/read-local-document/SKILL.md"
    skill.parent.mkdir(parents=True)
    shutil.copy2(extension / "WORKFLOW.md", skill)
    manifest = {
        "name": NAME,
        "version": source_manifest["version"],
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
    (target / ".mcp.json").write_text(json.dumps(config, indent=2) + "\n")
    shutil.copy2(
        Path(__file__).resolve().parent.parent / "clients/claude-cowork/README.md",
        target / "README.md",
    )
    verify_release(target / "server")
    package_files = {
        path.relative_to(target).as_posix(): sha256(path)
        for path in sorted(target.rglob("*"))
        if path.is_file() and not path.is_relative_to(target / "server")
    }
    receipt = {
        "distribution": "development-only",
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
    receipt.update(archive_sha256=sha256(archive), archive_bytes=archive.stat().st_size)
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
    args = parser.parse_args(argv)
    print(build(args.extension.resolve(), args.output.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
