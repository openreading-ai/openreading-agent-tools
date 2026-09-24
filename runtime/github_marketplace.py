"""Assemble Git-hosted marketplaces around the verified parser-free connector.

Publish the output on a versioned distribution branch, not the source branch.
Both host catalogs reference complete plugin directories. Git preserves executable
bits and deduplicates identical runtime blobs across the four client packages.
Source catalogs can pin that distribution commit with git-subdir sources. They
never resolve a moving branch as a plugin version or run a download helper.
Desktop identities differ from code identities because hosts may share catalogs.
The launcher's client label preserves existing preferences and retained documents.
Native host installation and owner-operated workflows remain separate gates.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

from runtime import build_server
from runtime.verify import sha256, verify_release

REPOSITORY = "https://github.com/openreading-ai/openreading-agent-tools.git"
CLIENTS = {
    "claude-code": "openreading",
    "claude-desktop": "openreading-cowork",
    "codex": "openreading",
    "chatgpt": "openreading-chatgpt",
}


def catalogs(commit=None):
    if commit is not None and not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A remote marketplace requires a full immutable Git commit.")
    claude = {"name": "openreading", "owner": {"name": "OpenReading"}, "plugins": []}
    openai = {"name": "openreading", "interface": {"displayName": "OpenReading"}, "plugins": []}
    for client, name in CLIENTS.items():
        path = f"plugins/{client}/{name}"
        is_claude = client.startswith("claude-")
        source = (
            {"source": "git-subdir", "url": REPOSITORY, "path": path, "sha": commit}
            if commit is not None
            else (f"./{path}" if is_claude else {"source": "local", "path": f"./{path}"})
        )
        entry = {"name": name, "source": source}
        if is_claude:
            entry["version"] = build_server.VERSION
            entry["description"] = (
                f"OpenReading for {'Cowork' if client == 'claude-desktop' else 'Claude Code'}. "
                "Apple Silicon only. Connects to your separately running Core server."
            )
        else:
            entry.update(
                policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                category="Productivity",
            )
        (claude if is_claude else openai)["plugins"].append(entry)
    return {".claude-plugin/marketplace.json": claude, ".agents/plugins/marketplace.json": openai}


def assemble(runtime: Path, output: Path):
    release = verify_release(runtime)
    output.mkdir(parents=True, exist_ok=False)
    clients = {}
    with tempfile.TemporaryDirectory(prefix="openreading-github-packages-") as temporary:
        for client, name in CLIENTS.items():
            stage = Path(temporary) / client
            build_server.package(runtime, stage, client=client)
            original = stage / (f"plugins/{name}" if client in {"codex", "chatgpt"} else "plugin")
            plugin = output / "plugins" / client / name
            shutil.copytree(original, plugin)
            if client == "claude-desktop":
                manifest_path = plugin / ".claude-plugin/plugin.json"
                manifest = json.loads(manifest_path.read_text())
                manifest["name"] = name
                manifest["description"] = (
                    "OpenReading for Cowork. Apple Silicon connector for your separately running Core server."
                )
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
                shutil.copy2(
                    build_server.HERE.parent / "clients/claude-desktop/README.md",
                    plugin / "README.md",
                )
            clients[client] = {
                "path": plugin.relative_to(output).as_posix(),
                "worker_sha256": sha256(plugin / "runtime/openreading-worker"),
                "launcher_sha256": sha256(plugin / "launch.sh"),
            }
    for name, value in catalogs().items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")
    shutil.copy2(build_server.HERE.parent / "LICENSE", output / "LICENSE")
    (output / "README.md").write_text(
        "# OpenReading GitHub distribution\n\n"
        "Install through your host's GitHub marketplace. Do not download or copy these folders.\n"
        "Choose openreading-cowork for Cowork, openreading-chatgpt for ChatGPT Work, or openreading for the matching code client.\n"
        "This unsigned Apple Silicon preview contains the parser-free connector. Start Core separately.\n"
        "Other platforms, native walkthroughs and clean-machine acceptance remain pending.\n"
        "See https://github.com/openreading-ai/openreading-agent-tools for setup and release status.\n"
    )
    (output / "distribution.json").write_text(
        json.dumps(
            {
                "version": build_server.VERSION,
                "profile": release["profile"],
                "core_commit": release["core_commit"],
                "worker_sha256": release["worker_sha256"],
                "platform": "macos-arm64",
                "distribution": "development-only",
                "clients": clients,
            },
            indent=2,
        )
        + "\n"
    )
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(assemble(args.runtime.resolve(), args.output.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
