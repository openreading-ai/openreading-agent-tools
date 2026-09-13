# Unsigned Docling build

P0 builds a development-only macOS arm64 executable with its own Python runtime.
It preserves the historical [runtime lock](../uv.lock) and [Docling candidate lock](../feasibility/uv.lock).
This project retains the feasibility dependency root and adds pinned PyInstaller build dependencies in a separate lock.
An offline regression requires every candidate package's version and source to remain identical.
The selected engine contains Docling Slim, CPU ONNX Runtime, PDFium and Tesseract; PyMuPDF and Torch are excluded.

## Build and exercise

Use macOS on Apple Silicon with Python 3.11.15 through uv and the Apple command-line build tools.
Prepare the pinned model assets with the [feasibility guide](../feasibility/README.md) before building.
Supply Tesseract and its explicit language directory; this build does not install or download them.
Run from the repository root, choosing a new output directory outside this checkout:

~~~sh
uv sync --frozen --project runtime/p0
runtime/p0/.venv/bin/python -m runtime.build_docling \
  --output /absolute/new-runtime \
  --models /absolute/models \
  --tesseract /absolute/tesseract \
  --tessdata /absolute/tessdata
/absolute/new-runtime/openreading-worker --version
~~~

The builder refuses another platform, Python patch, unpinned installed environment or an existing output.
The source and metadata required for engine identity accompany the executable.
The freezer discovers Docling's plugin entry point through package metadata, preserving its dynamic module import.
The inventory includes the model, lock, Tesseract dependency closure, English/orientation data and `configs/tsv`.
Tesseract libraries use relative install names; unresolved or ambiguous library searches fail the build.
Modified native files receive ad-hoc signatures required for local execution on Apple Silicon.
These signatures provide no publisher identity or notarization; they are not a distribution approval.
The notices cover installed Python/build distributions; complete native/model license review remains a release requirement.

Use the frozen corpus's `functional.pdf` from the [retrieval preparation](../../measurement/README.md).
The smoke needs the separate feasibility interpreter for its measurement libraries, not the end-user runtime:

~~~sh
uv sync --frozen --project runtime/feasibility
runtime/feasibility/.venv/bin/python -m scripts.docling_package_smoke \
  --runtime /absolute/new-runtime \
  --fixture /absolute/evidence/documents/functional.pdf
~~~

Do not wrap that command in another `sandbox-exec`; the checker applies its own child policy.
A system Perl socket probe must observe EPERM under that exact policy before document calls begin.
Frozen children cannot read Homebrew, this checkout, `/usr/local`, or uv's developer Python installation.
Their PATH contains only system directories, and their working directory is temporary and unrelated to the bundle.
The checker inspects Tesseract's actual loaded-library trace and rejects dependencies outside the bundle or system libraries.
It checks native evidence on physical page one, OCR-only evidence on physical page two, a distinct warm conversion and reuse after restart.
Wrong pages, text, origins, receipts, outside-grant access and missing memory samples fail the check.

The checker creates a temporary synthetic input grant and isolated home using the `codex/v2` namespace.
It reads no saved setup and changes no client registration. Temporary evidence is removed when the check ends.
It passes an inherited telemetry opt-in and fails if the worker creates ONNX telemetry state in that home.
The report records inventory bytes, verification and initialization time, import/warm/restart observations, progress events and sampled process-tree RSS.
RSS includes the measurement driver and is not the worker's own memory limit.
Progress timestamps do not separate every internal phase; closely spaced stages may be coalesced by core.
No result proves a fresh-machine installation, native assistant compatibility, p95 performance or token savings.

## Review boundary

Full inventory verification runs before core import, worker dispatch or tool registration, including on worker spawn.
A small bootstrap/verifier necessarily executes first; no first-parse verification deferral is used.
A one-second optional catalog grace is distinct from the host's initialization timeout.
Native probes must establish eventual discovery and a usable setup route before the client can be supported.

The September 12 packed/unpacked development smoke passed with core `e12c2fd3d4761b2349051861e6d57da91aa0e7d1` and Docling integration v5.
Native and OCR imports, warm conversion and restart reuse pass through the same frozen executable.
The earlier `7d97b75` runtime supplied the following separate integrity observations.
A relocated copy with spaces and Unicode in its path verifies native and OCR citations through public MCP reads.
Twenty changed or missing source, metadata, lock, model and OCR inputs refuse startup.
These observations replace no historical result and establish no native assistant support.
Raw run records remain private. Exact timings and release limits require separate reviewed evidence and base-machine repetitions.
Native client installation, signing, notarization, and helper packaging remain gated by the [implementation plan](../../design/implementation-plan.md).
Do not share this build or assemble historical client packages from it.
The explicit `runtime.package --docling-desktop` path assembles a separate local Desktop installation candidate; see the [Desktop guide](../../clients/claude-desktop/README.md).
That path does not authorize distribution or establish native installation acceptance.

The September 13 candidate at core `9af2606f6a53da632ab0a8f11a3cf8478099f941` added the optional local chooser contract.
Its unpacked frozen smoke passes extraction, OCR, restart and same-profile catalog parity.
The separate chat package also matches the provider-enabled core catalog without any setup fields.
Its direct stdio chooser call returned a sanitized timeout, not a native-host result.
The process-exit observation lacked a retained PID capture and cannot establish native dialog disappearance.
Successful user selection remains unverified.
These results do not replace named-host interaction or clean-machine acceptance.

The current candidate pins core `b03a6606ae8a8afd1d16d867e42ffbbf97bee774`, with explicit provider cleanup responsibilities.
The format 2 launcher sets `ORT_DISABLE_TELEMETRY=1` before core or native parser imports, including worker dispatch.
ONNX Runtime's later Python API opt-out alone does not prevent its device identifier and telemetry database initialization.
See the pinned [upstream privacy contract](https://github.com/microsoft/onnxruntime/blob/v1.30.0/docs/Privacy.md).
Fresh-home frozen checks remain distinct from installed-host traffic observation; old shared telemetry files are not deleted.
