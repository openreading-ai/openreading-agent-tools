"""Build a small Claude plugin plus a separately hosted, hash-pinned runtime archive.

The download URL is explicit build input. Local ngrok testing and later GitHub releases
use the same HTTPS contract. This builder neither publishes files nor resets user state.
Catalogs come from the exact frozen runtime under an isolated home before packaging.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from runtime.package import REPOSITORY, _docling_runtime, _server_destination
from runtime.verify import sha256


def catalog(worker, mode):
    with tempfile.TemporaryDirectory(prefix="openreading-catalog-") as home:
        home = str(Path(home).resolve())
        child = subprocess.Popen(
            [str(worker), "--client", "claude-desktop", mode],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env={**os.environ, "HOME": home},
            cwd=home,
        )
        try:
            messages = [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "package-check", "version": "1"},
                    },
                },
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            ]
            for message in messages:
                child.stdin.write(json.dumps(message) + "\n")
                child.stdin.flush()
                if "id" in message:
                    response = json.loads(child.stdout.readline())
                    if "error" in response:
                        raise ValueError("Frozen runtime catalog failed.")
            return response["result"]
        finally:
            child.stdin.close()
            child.wait(timeout=15)
            child.stdout.close()


def package(runtime, bootstrap, output, url):
    if urlsplit(url).scheme != "https" or not urlsplit(url).hostname:
        raise ValueError("Provide an HTTPS runtime archive URL.")
    metadata = _docling_runtime(runtime, chat=True)
    _server_destination(metadata)
    output.mkdir(parents=True, exist_ok=False)
    archive_path = output / "OpenReading-runtime-macOS-arm64.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(runtime, arcname="runtime")
    config = {
        "url": url,
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": sha256(archive_path),
        "worker_sha256": metadata["worker_sha256"],
        "catalogs": {
            mode: catalog(runtime / "openreading-worker", mode)
            for mode in ("--chat-documents", "--settings-tools")
        },
    }
    plugin = output / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin/plugin.json").write_text(
        json.dumps(
            {
                "name": "openreading-local-documents",
                "version": "0.2.0-alpha.8",
                "description": "OpenReading document processing and native settings. Downloads its verified runtime automatically on first use. Development candidate.",
                "author": {"name": "OpenReading"},
            },
            indent=2,
        )
        + "\n"
    )
    shutil.copy2(bootstrap, plugin / "openreading-bootstrap")
    (plugin / "openreading-bootstrap").chmod(0o755)
    (plugin / "bootstrap.json").write_text(json.dumps(config, indent=2) + "\n")
    (plugin / "launch.sh").write_text(
        '#!/bin/sh\nset -eu\nplugin=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\ncd "$HOME"\nexec "$plugin/openreading-bootstrap" "$plugin/bootstrap.json" "$@"\n'
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
    shutil.copytree(REPOSITORY / "skills", plugin / "skills")
    (plugin / "README.md").write_text(
        "# OpenReading for Claude\n\nUpload OpenReading-Claude-Plugin.zip in Claude and enable both connectors.\n"
        "The plugin downloads and verifies its runtime automatically. No separate installer or Python is required.\n"
        "Use `/openreading-settings` for Processing, Storage and Advanced.\n"
        "While downloading, tools report progress. Retry after setup completes.\n"
        "The runtime remains in Application Support. Settings and documents are preserved.\n"
        "This development build uses a temporary ngrok download. The tunnel must remain available for a first install.\n"
        "Signed distribution and clean-machine acceptance remain pending.\n"
    )
    target = output / "OpenReading-Claude-Plugin.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(plugin.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(plugin))
    (output / "build.json").write_text(
        json.dumps(
            {
                "distribution": "development-only",
                "worker_sha256": metadata["worker_sha256"],
                "core_commit": metadata["core_commit"],
                "plugin_sha256": sha256(target),
                "archive_sha256": config["archive_sha256"],
                "archive_bytes": config["archive_bytes"],
                "url": url,
            },
            indent=2,
        )
        + "\n"
    )
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("runtime", "bootstrap", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    print(
        package(args.runtime.resolve(), args.bootstrap.resolve(), args.output.resolve(), args.url)
    )


if __name__ == "__main__":
    main()
