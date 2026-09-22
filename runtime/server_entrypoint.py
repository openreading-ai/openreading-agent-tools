"""Run the parser-free connector against an explicitly configured Core HTTP server.

The plugin carries this runtime directly. Startup never downloads code or model assets.
Legacy local-mode preferences remain readable but require a native server save before use.
Settings stays available when document configuration fails. The proxy exposes the frozen
nine-tool catalog before setup and refuses new selections/imports after a destination save.
Retained data and Keychain references use the existing client partitions unchanged.
The server owns parsing; this entry point has no local parser dispatch.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import sys
from pathlib import Path

from runtime.app_settings import read_limits
from runtime.configuration import CLIENTS
from runtime.destination_settings import read_destination
from runtime.storage_settings import storage_session
from runtime.verify import verify_release


def require_server(client, *, home=None):
    settings = read_destination(client, home=home)
    if settings.mode != "server" or settings.destination is None:
        raise ValueError(
            "Open OpenReading Settings and save your Core server URL before selecting or processing documents. "
            "This plugin does not include a local parser. Existing saved documents are preserved."
        )
    return settings


def launch(args, metadata):
    from dataclasses import replace

    from runtime.server_profile import launch as server_launch

    settings = require_server(args.client)
    limits = read_limits(args.client)
    settings = replace(
        settings,
        destination=replace(settings.destination, response_bytes=limits.server_response_bytes),
    )
    with storage_session(args.client) as root:
        args.runtime_data_root = root
        if args.document_response_bytes is None:
            args.document_response_bytes = limits.document_response_bytes
        return server_launch(args, metadata, settings)


class EmbeddedManager:
    """Supply an already installed runtime to the MCP proxy without invoking provisioning."""

    def __init__(self, config, home, root, client, mode):
        self.config, self.home, self.installed_root = config, home, root
        self.client, self.mode = client, mode
        self.server_info = {"name": "openreading-connector", "version": "0.2.0-alpha.19"}
        self.root = None
        self.status = "OpenReading is ready."

    def start(self):
        try:
            if self.mode == "--chat-documents":
                require_server(self.client, home=self.home)
            self.root = self.installed_root
        except (OSError, ValueError) as error:
            self.root = None
            self.status = str(error)


def main(argv=None):
    if (
        sys.platform != "darwin"
        or platform.machine() != "arm64"
        or not getattr(sys, "frozen", False)
    ):
        raise ValueError("Run the packaged macOS Apple Silicon connector.")
    root = Path(sys.executable).parent
    metadata = verify_release(root)
    if metadata.get("profile") != "core-server-client-v1":
        raise ValueError("This executable requires a server-only release inventory.")
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        print(
            json.dumps(
                {key: metadata[key] for key in ("release_version", "core_commit", "worker_sha256")}
            )
        )
        return 0
    if argv[:1] == ["--internal-server-job"]:
        from runtime.server_profile import job_main

        return job_main(argv[1:], metadata)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True, choices=sorted(CLIENTS))
    modes = parser.add_mutually_exclusive_group(required=True)
    for mode in ("chat-documents", "settings-tools", "destination-settings"):
        modes.add_argument("--" + mode, action="store_true")
    parser.add_argument("--connector", action="store_true")
    parser.add_argument("--document-response-bytes", type=int)
    args = parser.parse_args(argv)
    if args.connector:
        from runtime.connector_proxy import serve

        mode = "--settings-tools" if args.settings_tools else "--chat-documents"
        config = json.loads((root / "catalogs.json").read_bytes())
        manager = EmbeddedManager(config, Path.home(), root, args.client, mode)
        serve(manager, mode, sys.stdin, sys.stdout)
        return 0
    if args.destination_settings:
        from runtime.destination_ui import run

        return run(args.client)
    if args.settings_tools:
        from runtime.settings_server import serve

        asyncio.run(serve(args.client))
        return 0
    return launch(args, metadata)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from None
