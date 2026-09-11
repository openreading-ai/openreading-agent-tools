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
    # Scan complete installation roots, including unowned .pth hooks and cached bytecode.
    # Snapshot and trial interpreters use -B so their imports cannot change these inputs.
    roots = {
        Path(metadata.distribution(name).locate_file("")).resolve()
        for name in environment["packages"]
    }
    for root in sorted(roots):
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            digest.update(f"{root}/{path.relative_to(root)}\0".encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return {
        "environment": environment,
        "engine": engine_identity(config).wire(),
        "installed_files_sha256": digest.hexdigest(),
        "python_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
    }


def verify_artifacts(profile, lock, input_root, artifact_root):
    """Load each C artifact through core before comparing it with the frozen B projection."""
    from openreading.adapters.docling_local.config import LocalDoclingConfig
    from openreading.artifacts.limits import DoclingLimits, ProfileConfig
    from openreading.artifacts.service import ArtifactService
    from openreading.artifacts.store import safe_read

    data = json.loads(profile.read_text())
    local = dict(data.pop("docling"))
    local["dependency_lock"] = str(lock)
    config = ProfileConfig(
        input_root, artifact_root, DoclingLimits(**data), LocalDoclingConfig.from_wire(local)
    )
    service = ArtifactService(config)
    try:
        records = []
        for path in sorted(service.store.documents.iterdir()):
            manifest, _ = service.store.load(path.name)
            response = json.loads(
                safe_read(path / "response.json", manifest.files["response.json"].length)
            )
            text = "\n\n".join(
                f"[Physical page {page['page_number']}]\n{page.get('text') or ''}"
                for page in response["document"]["pages"]
            )
            records.append(
                {
                    "source_relative_path": manifest.source_relative_path,
                    "document_sha256": manifest.document_sha256,
                    "engine": manifest.engine.wire(),
                    "full_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                }
            )
        return records
    finally:
        service.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args(argv)
    if bool(args.input_root) != bool(args.artifact_root):
        parser.error("Input and artifact roots must be supplied together.")
    result = (
        verify_artifacts(args.profile, args.lock, args.input_root, args.artifact_root)
        if args.artifact_root
        else snapshot(args.profile, args.lock)
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
