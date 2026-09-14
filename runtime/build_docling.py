"""Build an unsigned, development-only Docling runtime for the P0 feasibility check.

Use the separate runtime/p0 lock. Existing revision 1 binaries and the candidate lock
remain unchanged. This command requires macOS arm64, explicit pre-downloaded layout
assets and Tesseract inputs. It never downloads models or overwrites a prior build.
The diagnostic profile remains 100 pages and 300 seconds; neither is a release promise.
The emitted inventory includes Python source, distribution metadata, models, native
libraries, traineddata, configs/tsv, picker sources, and Tcl/Tk resources.
Publication, native accessibility and clean-machine support remain gated.
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
from runtime.native_bundle import bundle_native
from runtime.verify import inventory, sha256, verify_release
from scripts.docling_feasibility import selected_environment

HERE = Path(__file__).resolve().parent
LOCK = HERE / "p0/uv.lock"


def spec_text() -> str:
    # Frozen imports need both runnable bytecode and source files for core's fingerprint.
    # Metadata is runtime input: engine identity traverses all installed dependency edges.
    return f"""
from importlib import metadata
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata, collect_entry_point

datas = []
for distribution in metadata.distributions():
    datas += copy_metadata(distribution.metadata['Name'])
for name in ['openreading', 'docling', 'docling_core', 'docling_parse', 'pypdfium2_raw', 'onnxruntime']:
    datas += collect_data_files(name)
plugin_data, plugin_modules = collect_entry_point('docling')
datas += plugin_data
hidden = plugin_modules + ['openreading.artifacts.worker', 'openreading.artifacts.jobs', 'openreading.mcp_server.main']
for name in ['openreading.adapters.docling_local', 'docling.datamodel', 'docling_core.transforms', 'docling_parse']:
    hidden += collect_submodules(name)
a = Analysis([{str(HERE / "entrypoint.py")!r}], pathex=[{str(HERE.parent)!r}],
    binaries=[], datas=datas, hiddenimports=hidden,
    excludes=['torch', 'torchvision', 'docling_ibm_models', 'pymupdf', 'fitz'],
    module_collection_mode={{'runtime': 'pyz+py', 'openreading': 'pyz+py', 'docling': 'pyz+py', 'docling_core': 'pyz+py'}})
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='openreading-worker', console=True, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='openreading-worker')
"""


def build_runtime(output: Path, models: Path, tesseract: Path, tessdata: Path) -> Path:
    if (
        sys.platform != "darwin"
        or platform.machine() != "arm64"
        or platform.python_version() != "3.11.15"
    ):
        raise ValueError("Build requires native macOS arm64 and locked Python 3.11.15.")
    if output.exists():
        raise ValueError("Choose a new output directory; builds never overwrite a runtime.")
    inputs = [
        models / "docling-project--docling-layout-heron-onnx/model.onnx",
        tesseract,
        *[tessdata / name for name in ("eng.traineddata", "osd.traineddata", "configs/tsv")],
    ]
    if not all(path.is_file() for path in inputs):
        raise ValueError("The model, executable, traineddata and TSV config must already exist.")
    identity = selected_environment(LOCK)
    with tempfile.TemporaryDirectory(prefix="openreading-docling-p0-") as temporary:
        scratch = Path(temporary)
        spec = scratch / "docling.spec"
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
        shutil.copytree(models, resources / "models", symlinks=False)
        for name in ("eng.traineddata", "osd.traineddata", "configs/tsv"):
            target = resources / "tessdata" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tessdata / name, target)
        native = bundle_native(tesseract, resources / "tesseract")
        (resources / "native-inputs.json").write_text(json.dumps(native, indent=2) + "\n")
        shutil.copy2(LOCK, resources / "docling-runtime.uv.lock")
        (candidate / "THIRD_PARTY_NOTICES.txt").write_text(notices())
        materialize_links(candidate)
        entries = inventory(candidate)
        metadata = {
            "format_version": "2",
            "release_version": "0.2.0-p0",
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
            "profile": "local-document-proof-v2",
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
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--tesseract", type=Path, required=True)
    parser.add_argument("--tessdata", type=Path, required=True)
    args = parser.parse_args(argv)
    print(
        build_runtime(
            args.output.resolve(),
            args.models.resolve(),
            args.tesseract.resolve(),
            args.tessdata.resolve(),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
