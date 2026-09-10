# Local Docling feasibility

This developer harness tests the selected revision 2 engine before binary packaging.
It uses an isolated dependency lock and never imports a sibling checkout.
The historical revision 1 bundle and measurement runtime remain separate.

## Run

`make verify` checks this lock against its declared inputs without network access or installing the candidate.
Install the locked environment with `uv sync --frozen --project runtime/feasibility`.
Preparation explicitly downloads three pinned layout files and the upstream model README:

```sh
uv run --frozen --project runtime/feasibility python scripts/docling_feasibility.py prepare --assets /absolute/models
```

The model revision and file digests live in the pinned core configuration module.
Provide your installed Tesseract executable, directory containing `eng.traineddata` and `osd.traineddata`, and font file:

```sh
uv run --frozen --project runtime/feasibility python scripts/docling_feasibility.py measure \
  --assets /absolute/models --output /absolute/new-run-directory \
  --tesseract /absolute/tesseract --tessdata /absolute/tessdata \
  --font /absolute/font.ttf --lock /absolute/openreading-agent-tools/runtime/feasibility/uv.lock
```

Measurement requires Apple Silicon macOS and uses operating-system network denial for every conversion child.
It refuses installed torch, torchvision, docling_ibm_models, and PyMuPDF packages.
It generates deterministic synthetic inputs with native text, raster text, and a table region.
The report records font, input, and lock hashes; no font or model weights are committed here.
Each of eight cells runs one cold conversion and two warm conversions at 1, 10, 30, or 100 pages, with OCR off or on.
A cell fails if any physical page lacks its expected native text, raster text, table text, or measured origin.
The matrix exercises core conversion and page projection, rather than inspecting only aggregated Markdown.
The diagnostic ceiling is 300 seconds and 4 GiB sampled process-tree RSS per three-conversion cell.
These ceilings are safeguards, not supported product limits.

## Interpretation

`matrix.json` contains observations and failures; sibling logs retain native diagnostics for investigation.
Keep run outputs outside this repository, or in the private company repository for durable review.
Repeated conversions in one process are not independent cold repetitions or p95 evidence.
Conversion timing excludes retained-artifact commit and does not establish client tool-call timeouts.
A development-machine result does not establish base M-series performance or clean-host installation.
No parser measurements establish token savings.

The standard upstream initialization currently imports torch through CPU selection and disabled table-plugin loading.
Core's explicit standard-pipeline subclass initializes selected stages without patching global factories.
Orientation detection uses the same selected tessdata directory; both language and orientation files enter engine identity.
The explicit upstream PIL preprocessor avoids the Torch-dependent generic image loader in Transformers 5.
The same upstream pipeline still owns layout postprocessing, page assembly, and reading order.
This integration needs revalidation whenever the pinned upstream version changes.

## Remaining gates

Native host timeout probes, base-machine measurements, and supported release defaults remain unverified.
The artifact service requires explicit page, deadline, RSS, idle, asset, and lock configuration.
The offline retrieval corpus and paid token study are separate steps.
Signing, notarization, bundled OCR dependencies, and Desktop installation are later release prerequisites.

The selected candidate pins Docling slim 2.126.0, Transformers 5.16.1, and CPU ONNX Runtime 1.30.0.
An earlier Transformers 4.57.6 candidate converted successfully but failed the dependency audit and was rejected.
Docling's convenience ONNX extra selected the GPU distribution on Linux; the candidate instead pins CPU ONNX directly.

## Recorded developer result

Core `f997ee62fcb83f9c93f2670e025e17bf48f6fadf` passed all eight cells on September 10, 2026.
The machine was an Apple M4 Max with 128 GiB RAM, macOS 15.1, and CPython 3.11.15.
The lock SHA-256 was `ce23307a66c51fcb8ffea376d02481ea52e4bdea2bdc0168fb02c68a9d63f0d6`.
The installed package origin matched that core commit, and two independent fixture generations matched the measured input hashes.

Each timing includes core client conversion and physical-page projection.
The first conversion includes native initialization; warm values are the next two conversions in that process.
RSS is the peak sampled process-tree sum across the whole cell, reported in GiB.

| Pages | OCR | First conversion (s) | Warm conversions (s) | Peak RSS (GiB) |
| --- | --- | --- | --- | --- |
| 1 | off | 1.48 | 0.26, 0.25 | 0.80 |
| 1 | on | 1.72 | 0.51, 0.54 | 0.74 |
| 10 | off | 4.35 | 3.05, 3.05 | 1.17 |
| 10 | on | 5.42 | 4.26, 4.26 | 1.23 |
| 30 | off | 10.83 | 9.64, 9.94 | 1.30 |
| 30 | on | 13.16 | 11.55, 11.65 | 1.35 |
| 100 | off | 35.58 | 36.87, 44.10 | 1.56 |
| 100 | on | 48.28 | 44.58, 42.55 | 1.60 |

Real stdio import/search/read/restart also passed with network denied and OCR citations preserved.
Cancellation during an observed Tesseract child terminated the generation, removed staging, and allowed the next import to succeed.
These are developer checks, not installed Desktop evidence or a native-host timeout measurement.
The 100-page OCR observations exceed the historical 45-second limit; no release default is inferred from them.
