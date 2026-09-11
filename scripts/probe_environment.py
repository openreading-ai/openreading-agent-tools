"""Fingerprint the installed developer engine without importing a native converter.

The probe rechecks these bytes before every model call. Distribution versions alone
cannot detect an edited dependency, so sources, native libraries, and metadata are hashed.
Model assets and extraction settings use core's verified engine identity contract.
"""

import argparse
import hashlib
import json
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.docling_feasibility import selected_environment  # noqa: E402


def snapshot(profile, lock):
    from openreading.adapters.docling_local.config import LocalDoclingConfig
    from openreading.artifacts.limits import DoclingLimits, ProfileConfig
    from openreading.artifacts.service import engine_identity

    environment = selected_environment(lock)
    data = json.loads(profile.read_text())
    local = dict(data.pop("docling"))
    local["dependency_lock"] = str(lock)
    config = ProfileConfig(
        Path("/input"),
        Path("/artifacts"),
        DoclingLimits(**data),
        LocalDoclingConfig.from_wire(local),
    )
    digest = hashlib.sha256()
    for name in sorted(environment["packages"]):
        distribution = metadata.distribution(name)
        for entry in sorted(distribution.files or [], key=str):
            if entry.suffix == ".pyc":
                continue
            path = Path(distribution.locate_file(entry))
            if path.is_file():
                digest.update(f"{name}/{entry}\0".encode())
                digest.update(hashlib.sha256(path.read_bytes()).digest())
    return {
        "environment": environment,
        "engine": engine_identity(config).wire(),
        "installed_files_sha256": digest.hexdigest(),
        "python_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(snapshot(args.profile, args.lock), sort_keys=True))


if __name__ == "__main__":
    main()
