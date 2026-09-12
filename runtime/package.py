"""Assemble client directories from one verified native runtime and one shared skill.

The output contains review candidates, not published releases. MCPB validation and packing
use the separately pinned official CLI. No archive is signed or submitted automatically.
The historical assembler refuses format-2 runtimes. An explicit Docling Desktop path
assembles a development candidate for local installation checks, never a signed release.
WORKFLOW.md is a review copy; actual model instructions come from the pinned core server.
"""

from __future__ import annotations

import argparse
import json
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
            REPOSITORY / "clients" / client, target, ignore=shutil.ignore_patterns("docling")
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


def package_docling_desktop(runtime: Path, output: Path) -> Path:
    metadata = verify_release(runtime)
    if metadata["format_version"] != "2":
        raise ValueError("The Desktop development candidate requires a Docling runtime.")
    if output.exists():
        raise ValueError("Choose a new package output directory.")
    shutil.copytree(REPOSITORY / "clients/claude-desktop/docling", output)
    shutil.copytree(runtime, output / "server", symlinks=True)
    shutil.copy2(REPOSITORY / "skills/read-local-document/SKILL.md", output / "WORKFLOW.md")
    verify_release(output / "server")
    # Bind the review materials without claiming these hashes authenticate a publisher.
    (output / "package-info.json").write_text(
        json.dumps(
            {
                "distribution": "development-only",
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
    args = parser.parse_args()
    if args.docling_desktop:
        paths = {
            "claude-desktop": package_docling_desktop(args.runtime.resolve(), args.output.resolve())
        }
    else:
        paths = package_clients(args.runtime.resolve(), args.output.resolve())
    print(json.dumps({name: str(path) for name, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
