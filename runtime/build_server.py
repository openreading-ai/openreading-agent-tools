"""Build the server-only ChatGPT runtime without bundled local parsing dependencies.

This development profile sends only explicitly selected snapshot copies to an operator-run
Core server. It has no local fallback. The pinned P0 environment supplies the server protocol,
while the freezer excludes Docling, OCR and local parser packages before inventory hashing.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from runtime.build import materialize_links, notices
from runtime.verify import inventory, sha256, verify_release
from scripts.docling_feasibility import selected_environment

HERE = Path(__file__).resolve().parent
LOCK = HERE / "p0/uv.lock"


def spec_text() -> str:
    """Return the freezer specification for the server selection and transfer surface."""
    return f"""
from importlib import metadata
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = collect_data_files('openreading')
for distribution in metadata.distributions():
    datas += copy_metadata(distribution.metadata['Name'])
hidden = [
    'openreading.artifacts.jobs', 'openreading.mcp_server.main',
    'runtime.server_profile', 'runtime.server_imports', 'runtime.server_selection',
    'runtime.server_transport', 'runtime.server_keychain', 'runtime.destination_settings',
    'runtime.destination_ui', 'runtime.selection', 'runtime.chat_selection',
    'runtime.native_selection', 'runtime.snapshot_selection',
]
a = Analysis([{str(HERE / "entrypoint.py")!r}], pathex=[{str(HERE.parent)!r}],
    binaries=[], datas=datas, hiddenimports=hidden,
    excludes=['docling', 'docling_core', 'docling_parse', 'docling_ibm_models',
              'onnxruntime', 'transformers', 'torch', 'torchvision', 'pandas', 'scipy',
              'pypdfium2_raw', 'pymupdf', 'fitz'],
    module_collection_mode={{'runtime': 'pyz+py', 'openreading': 'pyz+py'}})
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='openreading-worker', console=True, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='openreading-worker')
"""


def build_runtime(output: Path) -> Path:
    """Freeze a new server-only runtime and verify its immutable release inventory."""
    if (
        sys.platform != "darwin"
        or platform.machine() != "arm64"
        or platform.python_version() != "3.11.15"
    ):
        raise ValueError("Build requires native macOS arm64 and locked Python 3.11.15.")
    if output.exists():
        raise ValueError("Choose a new output directory; builds never overwrite a runtime.")
    identity = selected_environment(LOCK)
    with tempfile.TemporaryDirectory(prefix="openreading-server-client-") as temporary:
        scratch = Path(temporary)
        spec = scratch / "server-client.spec"
        spec.write_text(spec_text())
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--distpath",
                str(scratch / "dist"),
                "--workpath",
                str(scratch / "build"),
                str(spec),
            ],
            check=True,
        )
        candidate = scratch / "dist/openreading-worker"
        resources = candidate / "resources"
        resources.mkdir()
        shutil.copy2(LOCK, resources / "server-runtime.uv.lock")
        (candidate / "THIRD_PARTY_NOTICES.txt").write_text(notices())
        materialize_links(candidate)
        entries = inventory(candidate)
        metadata = {
            "format_version": "3",
            "release_version": "0.2.0-server",
            "os": "darwin",
            "arch": "arm64",
            "minimum_os_version": platform.mac_ver()[0],
            "core_commit": identity["core_commit"],
            "core_version": identity["packages"]["openreading"],
            "python_version": platform.python_version(),
            "dependency_lock_sha256": sha256(LOCK),
            "worker_sha256": entries["openreading-worker"]["sha256"],
            "files": entries,
            "licenses": ["THIRD_PARTY_NOTICES.txt"],
            "profile": "server-client-v1",
            "distribution": "development-only",
        }
        (candidate / "release.json").write_text(json.dumps(metadata, indent=2) + "\n")
        verify_release(candidate)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(candidate, output, symlinks=True)
    verify_release(output)
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(build_runtime(args.output.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
