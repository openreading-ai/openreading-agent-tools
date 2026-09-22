"""Freeze and package the server-only Claude connector without downloadable dependencies.

The server_client lock selects Core's client-only Git build profile.
That wheel contains canonical shared retention and MCP code, with no engine modules.
A format-3 inventory binds the native worker, Python support files and tool catalogs.
The plugin is named OpenReading. Client storage partitions remain unchanged across upgrades.
Claude Code uses the same verified worker with its own client namespace and local marketplace.
Its separate marketplace archive omits manifests because authenticated archive sources require
strict=false. Claude Code 2.1.278 rejects even identity-only plugin.json files in that mode.
The marketplace declares the skills and MCP connectors; Desktop ZIPs retain their manifests.
Use --runtime to package an existing release without freezing or changing its executable.
Python modules are collected as files because Claude rejects nested ZIP archives.
The archive embeds the connector directly; it has no bootstrap URL or model provisioning.
Historical Docling builders remain available for the tagged pre-transition checkpoint.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from importlib import metadata
from pathlib import Path

from runtime.bootstrap_package import catalog
from runtime.build import materialize_links, notices
from runtime.client_boundary import validate_client_metadata
from runtime.verify import inventory, sha256, verify_release

HERE = Path(__file__).resolve().parent
LOCK = HERE / "server_client/uv.lock"
VERSION = "0.2.0-alpha.19"
EXCLUDES = [
    "runtime.bootstrap",
    "runtime.entrypoint",
    "runtime.docling_profile",
    "runtime.public_profile",
    "openreading.adapters",
    "openreading.api",
    "openreading.router",
    "openreading.server",
    "openreading.cli",
    "openreading.strategies",
    "openreading.derive",
    "openreading.artifacts.local_jobs",
    "openreading.artifacts.service",
    "openreading.artifacts.worker",
    "pypdf",
    "puremagic",
    "yaml",
    "docling",
    "docling_core",
    "docling_parse",
    "docling_ibm_models",
    "torch",
    "torchvision",
    "transformers",
    "onnxruntime",
    "pypdfium2",
    "pypdfium2_raw",
    "pymupdf",
    "fitz",
    "pytesseract",
    "numpy",
    "scipy",
    "pandas",
    "PIL",
]


def identity():
    packages = tomllib.loads(LOCK.read_text())["package"]
    package = next(row for row in packages if row["name"] == "openreading")
    commit = package["source"]["git"].split("#")[-1]
    validate_client_metadata(metadata.distribution("openreading").read_text("METADATA") or "")
    installed = json.loads(
        metadata.distribution("openreading").read_text("direct_url.json") or "{}"
    )
    if installed.get("vcs_info", {}).get("commit_id") != commit:
        raise ValueError("Installed Core differs from the server connector lock.")
    return {"core_commit": commit, "core_version": metadata.version("openreading")}


def spec_text():
    return f"""
from importlib import metadata
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = collect_data_files('openreading')
for distribution in metadata.distributions():
    if distribution.metadata['Name'].lower() not in {"pyinstaller", "pyinstaller-hooks-contrib", "altgraph", "macholib", "setuptools"}:
        datas += copy_metadata(distribution.metadata['Name'])
a = Analysis([{str(HERE / "server_entrypoint.py")!r}], pathex=[{str(HERE.parent)!r}],
    binaries=[], datas=datas, hiddenimports=['openreading.artifacts.jobs', 'openreading.mcp_server.session'],
    excludes={EXCLUDES!r}, noarchive=True,
    module_collection_mode={{'runtime': 'pyc', 'openreading': 'pyc'}})
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='openreading-worker', console=True, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='openreading-worker')
"""


def build_runtime(output):
    if (
        sys.platform != "darwin"
        or platform.machine() != "arm64"
        or platform.python_version() != "3.11.15"
    ):
        raise ValueError("Build requires native macOS arm64 and locked Python 3.11.15.")
    if output.exists():
        raise ValueError("Choose a new build directory; existing runtimes are never overwritten.")
    core = identity()
    with tempfile.TemporaryDirectory(prefix="openreading-server-build-") as temporary:
        scratch = Path(temporary)
        spec = scratch / "server.spec"
        spec.write_text(spec_text())
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--distpath",
                str(scratch / "dist"),
                "--workpath",
                str(scratch / "build"),
                str(spec),
            ],
            check=True,
        )
        candidate = scratch / "dist/openreading-worker"
        (candidate / "resources").mkdir()
        shutil.copy2(LOCK, candidate / "resources/server-client.uv.lock")
        (candidate / "THIRD_PARTY_NOTICES.txt").write_text(notices())
        materialize_links(candidate)
        entries = inventory(candidate)
        release = {
            "format_version": "3",
            "release_version": VERSION,
            "os": "darwin",
            "arch": "arm64",
            "minimum_os_version": platform.mac_ver()[0],
            **core,
            "python_version": platform.python_version(),
            "dependency_lock_sha256": sha256(LOCK),
            "worker_sha256": entries["openreading-worker"]["sha256"],
            "files": entries,
            "licenses": ["THIRD_PARTY_NOTICES.txt"],
            "profile": "core-server-client-v1",
            "distribution": "development-only",
        }
        (candidate / "release.json").write_text(json.dumps(release, indent=2) + "\n")
        verify_release(candidate)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(candidate, output)
    return output


def package(runtime, output, *, client="claude-desktop"):
    if client not in {"claude-desktop", "claude-code"}:
        raise ValueError("Unsupported client for this Claude package.")
    release = verify_release(runtime)
    if release.get("profile") != "core-server-client-v1":
        raise ValueError("Package requires a server-only runtime.")
    if release.get("release_version") != VERSION:
        raise ValueError(
            "Runtime version differs from the plugin version. Build the matching release first."
        )
    documents = catalog(runtime / "openreading-worker", "--chat-documents", server=True)
    settings = catalog(runtime / "openreading-worker", "--settings-tools")
    output.mkdir(parents=True, exist_ok=False)
    plugin = output / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    shutil.copytree(runtime, plugin / "runtime")
    (plugin / "runtime/catalogs.json").write_text(
        json.dumps(
            {"catalogs": {"--chat-documents": documents, "--settings-tools": settings}}, indent=2
        )
        + "\n"
    )
    release["files"] = inventory(plugin / "runtime")
    (plugin / "runtime/release.json").write_text(json.dumps(release, indent=2) + "\n")
    verify_release(plugin / "runtime")
    (plugin / ".claude-plugin/plugin.json").write_text(
        json.dumps(
            {
                "name": "openreading",
                "version": VERSION,
                "description": "Connect Claude to your OpenReading Core server. Native file selection, document tools and settings. No bundled parser or model download. Development candidate.",
                "author": {"name": "OpenReading"},
            },
            indent=2,
        )
        + "\n"
    )
    (plugin / "launch.sh").write_text(
        f'#!/bin/sh\nset -eu\nplugin=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\ncd "$HOME"\nexec "$plugin/runtime/openreading-worker" --client {client} --connector "$@"\n'
    )
    (plugin / "launch.sh").chmod(0o755)
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
    shutil.copytree(HERE.parent / "skills", plugin / "skills")
    (plugin / "README.md").write_text(
        "# OpenReading for Claude\n\n"
        "Upload this plugin ZIP in Claude and enable both connectors. No separate runtime download or Python installation is required.\n"
        "Open `/openreading-settings`, enter your OpenReading Core server URL, test the connection and save.\n"
        "Localhost may use HTTP. Remote servers require HTTPS. Start and configure Core separately.\n"
        "Quit and reopen Claude, start a new task, and ask to open the OpenReading file picker.\n"
        "Selected files are queued. Choose Process or Add more. Processing uploads the selected files to your configured server.\n"
        "Existing server settings, credentials and retained documents are preserved. A previous bundled-parser selection requires server setup.\n"
        "Storage and Advanced retain their own Save and Restore defaults controls. Restore processing defaults stages the localhost URL; Save is required.\n"
        "This is an unsigned development candidate. Clean-machine and full native acceptance remain pending.\n"
    )
    if client == "claude-code":
        shutil.copy2(HERE.parent / "clients/claude-code/README.md", plugin / "README.md")
        marketplace = output / ".claude-plugin/marketplace.json"
        marketplace.parent.mkdir()
        marketplace.write_text(
            json.dumps(
                {
                    "name": "openreading",
                    "owner": {"name": "OpenReading"},
                    "plugins": [{"name": "openreading", "source": "./plugin"}],
                },
                indent=2,
            )
            + "\n"
        )
    # Check content as well as suffixes so renamed dependency archives cannot slip through.
    for path in sorted(plugin.rglob("*")):
        if path.is_file():
            with path.open("rb") as stream:
                header = stream.read(4)
            # zipimport's bytecode embeds ZIP signatures; an archive starts with one.
            if path.suffix.lower() == ".zip" or (
                header in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08") and zipfile.is_zipfile(path)
            ):
                raise ValueError(
                    f"Claude plugins cannot contain nested ZIP files: {path.relative_to(plugin)}"
                )
    target = output / "OpenReading-Claude-Plugin.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(plugin.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(plugin))
    if target.stat().st_size >= 200_000_000:
        raise ValueError("Plugin exceeds the Claude upload limit.")
    marketplace_metadata = {}
    if client == "claude-code":
        marketplace_archive = output / "OpenReading-Claude-Code-Marketplace.zip"
        with zipfile.ZipFile(marketplace_archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(plugin.rglob("*")):
                relative = path.relative_to(plugin)
                if path.is_file() and str(relative) not in {
                    ".claude-plugin/plugin.json",
                    ".mcp.json",
                }:
                    archive.write(path, relative)
        marketplace_metadata = {"marketplace_sha256": sha256(marketplace_archive)}
    (output / "build.json").write_text(
        json.dumps(
            {
                "version": VERSION,
                "client": client,
                "distribution": "development-only",
                "profile": release["profile"],
                "core_commit": release["core_commit"],
                "worker_sha256": release["worker_sha256"],
                "plugin_sha256": sha256(target),
                "plugin_bytes": target.stat().st_size,
                "runtime_download": False,
                "document_tools": len(documents["tools"]),
                **marketplace_metadata,
            },
            indent=2,
        )
        + "\n"
    )
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--client", choices=("claude-desktop", "claude-code"), default="claude-desktop"
    )
    parser.add_argument(
        "--runtime", type=Path, help="Package an existing verified server-only runtime."
    )
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Choose a new output directory.")
    runtime = args.runtime.resolve() if args.runtime else build_runtime(output / "runtime")
    print(package(runtime, output / "package", client=args.client))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
