"""Run the diagnostic Docling profile from verified, relocated bundle resources.

P0 uses finite 100-page, 300-second, 4-GiB safeguards, not supported host limits.
Each invocation writes its own private profile until core has closed its owned workers.
No model tool or environment variable selects the backend, resources, or input grant.
HF_HUB_OFFLINE and TRANSFORMERS_OFFLINE are set for launch and restored on exit.
"""

from __future__ import annotations

import json
import os
import secrets
from contextlib import contextmanager
from pathlib import Path

from runtime.configuration import client_root, configure_v2, ocr_value, select_settings


@contextmanager
def profile_file(client, settings, bundle):
    from openreading.artifacts.intake import directory
    from openreading.artifacts.limits import ProfileConfig
    from openreading.artifacts.store import Store

    root = client_root(client) / "v2"
    with directory(root, create=True):
        store = Store(ProfileConfig(settings.input_root, root / "artifacts"))
        close = getattr(store, "close", None)
        if close:
            close()
    resources = bundle / "resources"
    profile = {
        "pages": 100,
        "deadline_seconds": 300,
        "worker_memory_bytes": 4 * 1024**3,
        "worker_idle_seconds": 60,
        "docling": {
            "artifacts_path": str(resources / "models"),
            "dependency_lock": str(resources / "docling-runtime.uv.lock"),
            "ocr": settings.ocr,
            "tesseract_cmd": str(resources / "tesseract/bin/tesseract"),
            "tessdata_path": str(resources / "tessdata"),
            "languages": ["eng"],
            "threads": 4,
        },
    }
    name = secrets.token_hex(16)
    launch = root / "launch"
    with directory(launch, create=True) as parent:
        os.fchmod(parent, 0o700)
        os.mkdir(name, 0o700, dir_fd=parent)
        try:
            with directory(launch / name) as child:
                fd = os.open(
                    "profile.json", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=child
                )
                try:
                    with os.fdopen(fd, "w") as stream:
                        json.dump(profile, stream)
                        stream.flush()
                        os.fsync(stream.fileno())
                    yield launch / name / "profile.json", root / "artifacts"
                finally:
                    os.unlink("profile.json", dir_fd=child)
        finally:
            os.rmdir(name, dir_fd=parent)


def launch(args, bundle: Path) -> int:
    from openreading.artifacts.limits import ArtifactError

    if args.configure:
        if args.input_root is None:
            raise ValueError("configuration_required: Setup needs a document directory.")
        configure_v2(args.client, args.input_root, ocr_value(args.ocr))
        print(
            "Directory configured. Retained source copies stay locally; retrieved excerpts enter the assistant context. This grant limits OpenReading tools only."
        )
        return 0
    settings = select_settings(args.client, args.input_root, args.ocr)
    previous = {key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}
    try:
        os.environ.update(dict.fromkeys(previous, "1"))
        with profile_file(args.client, settings, bundle) as (path, store):
            from openreading.mcp_server.main import main as core_main

            return core_main(
                [
                    "--profile",
                    "local-document-proof-v2",
                    "--profile-config",
                    str(path),
                    "--input-root",
                    str(settings.input_root),
                    "--artifact-root",
                    str(store),
                ]
            )
    except (ArtifactError, OSError):
        raise ValueError(
            "configuration_required: Cannot open the configured document or artifact directory."
        ) from None
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
