"""Launch the nine Core tools against one explicit operator-run HTTP destination.

Only verified native entry points supply metadata and settings to this module.
The source grant remains the client's completed selection intake; exports use Downloads.
Detached children reconstruct fixed roots, limits and retaining-runtime identity.
Serialized execution contains a client name and nonsecret destination snapshot, never code.
Settings changes never reroute a running transfer. Unsubmitted stale approvals are refused.
The external profile has no parser or overall server wait deadline. Transport bounds apply.
No page count or aggregate storage ceiling is configured, and retained data has no eviction.
For example, successive imports grow disk use until the user removes their retained data.
A stalled server can keep a detached job waiting until explicit local cancellation.
The response byte budget limits downloads, not peak memory during decoding and retention.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import asdict
from pathlib import Path

from runtime.configuration import client_root
from runtime.destination_settings import decode_settings
from runtime.server_imports import ServerArtifactService
from runtime.server_selection import ServerSelectionProvider, ServerSelectionStore
from runtime.server_transport import UPLOAD_BYTES


def config_for(client, settings):
    from openreading.artifacts.limits import ExternalLimits, ProfileConfig

    if settings.mode != "server" or settings.destination is None:
        raise ValueError("Configure an explicit Core server destination.")
    selection = ServerSelectionStore(client)
    limits = ExternalLimits(
        source_bytes=UPLOAD_BYTES, extraction_bytes=settings.destination.response_bytes
    )
    return ProfileConfig(
        selection.prepare(), client_root(client) / "v2/artifacts", limits
    ), selection


def identity_for(metadata):
    from openreading.artifacts.models import EngineIdentity

    return EngineIdentity(
        core_commit=metadata["core_commit"],
        core_version=metadata["core_version"],
        backend_id="external-response",
        backend_version="1",
        extraction_settings={
            "retention_revision": "1",
            "retaining_worker_sha256": metadata["worker_sha256"],
        },
    )


def launch(args, metadata, settings):
    config, selection = config_for(args.client, settings)
    from openreading.artifacts.jobs import ImportExecution
    from openreading.artifacts.limits import ArtifactError
    from openreading.mcp_server.main import serve

    execution = ImportExecution(
        (sys.executable, "--internal-server-job"),
        {"client": args.client, "destination": settings.wire()},
    )
    try:
        asyncio.run(
            serve(
                config,
                selection_provider=ServerSelectionProvider(selection, settings),
                selection_timeout_seconds=None,
                document_response_bytes=args.document_response_bytes,
                document_export_root=Path.home() / "Downloads/OpenReading",
                service_factory=lambda config: ServerArtifactService(
                    config, settings=settings, selection=selection, identity=identity_for(metadata)
                ),
                execution=execution,
            )
        )
    except KeyboardInterrupt:
        return 130
    except ArtifactError as error:
        print(error.envelope().error.message, file=sys.stderr)
        return 2
    return 0


def job_main(argv, metadata):
    from openreading.artifacts.jobs import main

    def factory(request):
        snapshot = request["execution"]
        if not isinstance(snapshot, dict) or set(snapshot) != {"client", "destination"}:
            raise ValueError("Invalid server job configuration.")
        settings = decode_settings(snapshot["destination"])
        config, selection = config_for(snapshot["client"], settings)
        if (
            request["input_root"] != str(config.input_root)
            or request["artifact_root"] != str(config.artifact_root)
            or request["limits"] != asdict(config.limits)
            or request["docling"] is not None
        ):
            raise ValueError("Server job configuration differs from its fixed profile.")
        return ServerArtifactService(
            config, settings=settings, selection=selection, identity=identity_for(metadata)
        )

    return main(argv, service_factory=factory)
