"""Freeze locked core into a native macOS directory bundle for local review.

Run through the locked runtime project: uv run --project runtime --group build
python -m runtime.build --output dist/runtime. The command refuses a different platform,
Python patch, dirty lock resolution, or an already populated output directory.
Notices conservatively include installed build tools, not an exact frozen inventory.
Signing, notarization, license review, and binary publication are separate release gates.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from runtime.verify import inventory, sha256, verify_release

HERE = Path(__file__).resolve().parent


def materialize_links(root: Path) -> None:
    # MCPB dereferences library links; hash the install representation before packing.
    inventory(root)
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            target = path.resolve(strict=True)
            path.unlink()
            if target.is_dir():
                shutil.copytree(target, path, symlinks=False)
            else:
                shutil.copy2(target, path)


def locked_identity() -> dict:
    lock = tomllib.loads((HERE / "uv.lock").read_text())
    package = next(p for p in lock["package"] if p["name"] == "openreading")
    commit = package["source"]["git"].split("#")[-1]
    installed = json.loads(
        importlib.metadata.distribution("openreading").read_text("direct_url.json") or "{}"
    )
    if installed.get("vcs_info", {}).get("commit_id") != commit:
        raise ValueError("Installed core revision differs from the frozen lock.")
    from openreading.artifacts.worker import SETTINGS

    return {
        "core_commit": commit,
        "core_version": importlib.metadata.version("openreading"),
        "backend_id": "pymupdf",
        "backend_version": importlib.metadata.version("pymupdf"),
        "extraction_settings": {**SETTINGS, "dependency_lock_sha256": sha256(HERE / "uv.lock")},
    }


def notices() -> str:
    sections = [
        "OpenReading local proof: build-environment license inventory.\nIncludes build tools; this is not an exact list of frozen dependencies.\nThis is not a legal determination or binary distribution approval.\n"
    ]
    for distribution in sorted(
        importlib.metadata.distributions(), key=lambda d: d.metadata["Name"].lower()
    ):
        name = distribution.metadata["Name"]
        license_name = (
            distribution.metadata.get("License-Expression")
            or distribution.metadata.get("License")
            or "See included license text and upstream metadata."
        )
        sections.append(f"\n{name} {distribution.version}\n{license_name}\n")
        for file in distribution.files or []:
            if any(
                part.lower().startswith(("license", "copying", "notice")) for part in file.parts
            ):
                path = distribution.locate_file(file)
                if path.is_file():
                    sections.append(path.read_text(errors="replace"))
    return "\n".join(sections)


def build_runtime(output_dir: Path) -> Path:
    if (
        sys.platform != "darwin"
        or platform.machine() != "arm64"
        or platform.python_version() != "3.11.15"
    ):
        raise ValueError("Build requires native macOS arm64 and locked Python 3.11.15.")
    if output_dir.exists():
        raise ValueError(
            "Choose a new output directory; builds never overwrite an existing runtime."
        )
    identity = locked_identity()
    with tempfile.TemporaryDirectory(prefix="openreading-freeze-") as temporary:
        scratch = Path(temporary)
        identity_file = scratch / "engine-identity.json"
        identity_file.write_text(json.dumps(identity))
        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--noupx",
            "--name",
            "openreading-worker",
            "--distpath",
            str(scratch / "dist"),
            "--workpath",
            str(scratch / "build"),
            "--specpath",
            str(scratch),
            "--paths",
            str(HERE.parent),
            "--collect-all",
            "pymupdf",
            "--collect-data",
            "openreading",
            "--copy-metadata",
            "openreading",
            "--copy-metadata",
            "pymupdf",
            "--copy-metadata",
            "mcp",
            "--hidden-import",
            "openreading.artifacts.worker",
            "--hidden-import",
            "openreading.mcp_server.main",
            "--add-data",
            f"{identity_file}:openreading",
            str(HERE / "entrypoint.py"),
        ]
        subprocess.run(command, check=True)
        candidate = scratch / "dist" / "openreading-worker"
        (candidate / "THIRD_PARTY_NOTICES.txt").write_text(notices())
        materialize_links(candidate)
        entries = inventory(candidate)
        metadata = {
            "format_version": "1",
            "release_version": "0.1.0-alpha.1",
            "os": "darwin",
            "arch": "arm64",
            "minimum_os_version": platform.mac_ver()[0],
            "core_commit": identity["core_commit"],
            "core_version": identity["core_version"],
            "python_version": platform.python_version(),
            "dependency_lock_sha256": sha256(HERE / "uv.lock"),
            "worker_sha256": entries["openreading-worker"]["sha256"],
            "files": entries,
            "licenses": ["THIRD_PARTY_NOTICES.txt"],
        }
        (candidate / "release.json").write_text(json.dumps(metadata, indent=2) + "\n")
        verify_release(candidate)
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(candidate, output_dir, symlinks=True)
    verify_release(output_dir)
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(build_runtime(args.output.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
