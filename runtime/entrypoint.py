"""Launch the verified core worker without an end-user Python installation.

Unsupported hosts and unfrozen source execution return status 2 before inventory access.
The client name selects only its retained-store location. It cannot change the core
profile or backend. Explicit directory arguments are never interpreted by a shell.
The internal child dispatch uses the same frozen executable and verified inventory.
"""

from __future__ import annotations

import argparse
import json
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
    if argv == ["--version"]:
        print(
            json.dumps(
                {key: metadata[key] for key in ["release_version", "core_commit", "worker_sha256"]}
            )
        )
        return 0
    if argv[:1] == ["--internal-artifact-worker"]:
        from openreading.artifacts.worker import main as worker_main

        return worker_main(argv[1:])
    parser = argparse.ArgumentParser(
        description="Run the verified local OpenReading document tools."
    )
    parser.add_argument(
        "--client", required=True, choices=["claude-desktop", "claude-code", "codex"]
    )
    parser.add_argument(
        "--configure", action="store_true", help="save an explicit input grant for this client"
    )
    parser.add_argument(
        "--input-root", type=Path, help="explicit document directory; no default grant"
    )
    args = parser.parse_args(argv)
    try:
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
