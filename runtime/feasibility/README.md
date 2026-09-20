# Local Docling feasibility

This developer harness tests the selected revision 2 engine before binary packaging.
It uses an isolated dependency lock and never imports a sibling checkout.
The historical revision 1 bundle and measurement runtime remain separate.

## Run

The current candidate pins core `fb8967e424b199a788b8a8537a918118893a0b66` with Docling integration v5 and updated bounded-evidence instructions.
Dependency versions remain unchanged. The core update retains picture-child text and complete normalized-document retrieval. It adds persistent background imports.

`make verify` checks this lock against its declared inputs without network access or installing the candidate.
It also refuses prohibited packages in the lock and requires this guide to name the locked core and engine versions.
`make audit` queries advisories for this lock through uv's experimental audit command and requires network access.
Install the locked environment with `uv sync --frozen --project runtime/feasibility`.
Preparation explicitly downloads three pinned layout files and the upstream model README:

```sh
uv run --frozen --project runtime/feasibility python scripts/docling_feasibility.py prepare --assets /absolute/models
```

The model revision and file digests live in the pinned core configuration module.
Provide your installed Tesseract executable, directory containing `eng.traineddata`, `osd.traineddata`, and `configs/tsv`, and font file:

```sh
uv run --frozen --project runtime/feasibility python scripts/docling_feasibility.py measure \
  --assets /absolute/models --output /absolute/new-run-directory \
  --tesseract /absolute/tesseract --tessdata /absolute/tessdata \
  --font /absolute/font.ttf --lock /absolute/openreading-agent-tools/runtime/feasibility/uv.lock
```

Measurement requires Apple Silicon macOS and uses operating-system network denial for every conversion child.
Each child records a loopback connection attempt; a cell fails unless the operating system refuses it.
It refuses importable torch, torchvision, docling_ibm_models, PyMuPDF, or `fitz` modules.
It also refuses any installed distribution absent from, or at a different version than, the supplied lock.
The imported core must come from the installed distribution at the locked commit, never a sibling checkout on `PYTHONPATH`.
Active dependencies missing from the environment are refused, including dependencies selected through extras and platform markers.
Inaccessible memory samples fail a cell; exited children do not discard the surviving process totals.
Conversion children use the run directory for native libraries' relative writes.
It generates deterministic synthetic inputs with native text, raster text, and a table region.
Input hashes depend on the supplied font, so the report records the font hash beside them.
The report also records the core commit, installed versions, Tesseract version, and layout, Tesseract, tessdata, and lock hashes.
No font or model weights are committed here.
Each of eight cells runs one first conversion and two warm conversions at 1, 10, 30, or 100 pages, with OCR off or on.
A cell fails if any physical page lacks its expected native text, raster text, table text, or measured origin.
Each page must also carry only its own physical page marker, so shifted or duplicated page text fails.
Any projection warning other than the disclosed table-region warning also fails the cell.
With OCR off, the raster sentence must be absent from every page.
The matrix exercises core conversion and page projection, rather than inspecting only aggregated Markdown.
The synthetic items each fit on one page, so the matrix does not exercise cross-page provenance.
Page origin is checked per page; passage-level origin labels remain a core and client check.
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
In the recorded OCR cells, Tesseract logged `OSD failed` with "Too few characters" for every OCR region.
Recognition still succeeded, but the synthetic matrix does not show that orientation detection works.
The explicit upstream PIL preprocessor avoids the Torch-dependent generic image loader in Transformers 5.
The same upstream pipeline still owns layout postprocessing, page assembly, and reading order.
This integration needs revalidation whenever the pinned upstream version changes.

## Remaining gates

A frozen v2 bundle must retain core module sources and dependency distribution metadata for identity discovery.
It must also include the hashed Tesseract `configs/tsv` output configuration.

Native host timeout probes, base-machine measurements, and supported release defaults remain unverified.
The artifact service requires explicit page, deadline, RSS, idle, asset, and lock configuration.
The offline retrieval corpus supports native Desktop checks. Provider API token studies are retired.
Signing, notarization, bundled OCR dependencies, and Desktop installation are later release prerequisites.

The selected candidate pins Docling slim 2.126.0, Transformers 5.16.1, and CPU ONNX Runtime 1.30.0.
An earlier Transformers 4.57.6 candidate converted successfully but failed the dependency audit and was rejected.
Docling's convenience ONNX extra selected the GPU distribution on Linux; the candidate instead pins CPU ONNX directly.

## Historical developer result

Core `f997ee62fcb83f9c93f2670e025e17bf48f6fadf` passed all eight cells on September 10, 2026.
The machine was an Apple M4 Max with 128 GiB RAM, macOS 15.1, and CPython 3.11.15.
The lock SHA-256 was `ce23307a66c51fcb8ffea376d02481ea52e4bdea2bdc0168fb02c68a9d63f0d6`.
The installed package origin matched that core commit, and two independent fixture generations matched the measured input hashes.
The font SHA-256 was `25eceb458d4baf628ee0b6a135a9f8ac5ec7b2826646720834bd2bf00dfc825a`.
The 100-page input SHA-256 was `efd1e0fdc0b8792fce90d87d4489acfa7397b28b7c6bdde23806c5137d54fd9f`.
That run used report format `docling-feasibility.v1`.
It predates the page-marker, warning, installed-identity, and network-canary checks above.
Rerun the matrix before citing it as `docling-feasibility.v2` evidence.

Each timing includes core client conversion, per-conversion asset hash verification, and physical-page projection.
Core's default four inference threads and English OCR were used.
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

## Reviewed v2 developer result

The stricter harness passed all eight cells with core `f241c28b9709dd1d87f0ff139846646bfe4a5d20`.
The lock SHA-256 is `a4038d9a1d709f64cc9958f242ef65ed621b035e638c95e7e0400648be2b4a81`.
The font SHA-256 is `25eceb458d4baf628ee0b6a135a9f8ac5ec7b2826646720834bd2bf00dfc825a`.
The 100-page input SHA-256 is `efd1e0fdc0b8792fce90d87d4489acfa7397b28b7c6bdde23806c5137d54fd9f`.
This run used the same M4 Max machine and Helvetica font as the historical run.
Every cell observed network denial and verified page markers, all fixture text, page origins, and projection warnings.
Installed core origin and all active locked dependencies were checked before conversion.

| Pages | OCR | First conversion (s) | Warm conversions (s) | Peak RSS (GiB) |
| --- | --- | --- | --- | --- |
| 1 | off | 1.39 | 0.25, 0.25 | 0.77 |
| 1 | on | 1.65 | 0.50, 0.49 | 0.82 |
| 10 | off | 4.16 | 3.02, 2.99 | 1.24 |
| 10 | on | 5.29 | 4.15, 4.14 | 1.19 |
| 30 | off | 11.10 | 9.63, 9.84 | 1.28 |
| 30 | on | 12.83 | 13.74, 11.86 | 1.37 |
| 100 | off | 39.01 | 38.43, 32.79 | 1.53 |
| 100 | on | 37.15 | 36.52, 36.39 | 1.63 |

The first stricter attempt failed its 100-page non-OCR cell because the monitor confused normal process exit with inaccessible memory.
The corrected monitor passed a full rerun; that earlier attempt remains a failed measurement.
These remain developer observations with one first and two warm conversions per cell, not release limits or p95 evidence.
Orientation, cross-page items, passage-level retrieval, host deadlines, and artifact commit timing remain separate checks.

The `25c15c4` candidate adds `openreading_get_document` for the complete retained normalized result, excluding raw provider payloads.
Search remains optional. Requested document content enters the assistant context; full retrieval can include all extracted text.
The profile still controls available channels, including its table limitations.
Updated frozen and native checks remain separate from the historical observations above.
