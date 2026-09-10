# Docling local proof migration design

**Status:** proposed revision 2 implementation contract; current executable behavior remains revision 1.
**Intent:** [ProductSpec revision 2](../product/specs/local-document-proof.product-spec.md).
**Review:** [finding dispositions](review-disposition.md) record accepted changes and reasoned exceptions.

## 1. Engine decision and boundaries

The first distributed profile becomes `local-document-proof-v2`, using an in-process Docling adapter owned by core.
The existing core `docling` HTTP adapter remains separate and compatible.
The proposed new adapter identifier is `docling_local`; its descriptor controls its supported formats and capabilities.
Agent Tools consumes an immutable core commit after that adapter and the revised artifact contract pass core verification.
It never copies parser, provenance, or retrieval logic into a launcher.

| Role | Revision 2 choice |
| --- | --- |
| Conversion | Docling's standard PDF pipeline, with the selected docling-parse PDF backend. |
| Preflight/rendering | pypdfium2 with its pinned PDFium library. |
| Layout | Layout Heron ONNX weights, ONNX Runtime CPU provider, explicit local artifacts path. |
| Reading order | Docling's emitted item order and supported provenance. |
| OCR | Bundled Tesseract CLI, Leptonica, image libraries, and selected tessdata; setup-controlled and disabled by default. |
| Table structure | Disabled. Preserve independently available table-region text or disclose its absence. |
| Prohibited payload | PyMuPDF, torch, torchvision, and docling-ibm-models. |

The no-torch rule controls footprint and dependency scope; it is not a statement that torch is nonpermissively licensed.
Top-level license labels are candidates for review, not proof that the complete bundle satisfies distribution requirements.
Exact dependency and weight revisions are selected by the feasibility task, then frozen with hashes and notices.
Review-time versions or performance estimates must not be copied into release evidence as tested facts.

Run the pipeline with the prohibited packages absent and network access blocked before committing a release lock.
Check whether the pinned transformers preprocessing path operates without torch and whether table-region text survives disabled structure recognition.
If either requirement fails, stop the migration at feasibility and report the concrete incompatibility.
Do not add torch, download weights at runtime, use docling-serve, or substitute a different backend silently.
One Docling profile is the current decision; a fast PDFium-only profile requires new evidence and owner agreement.

## 2. Setup and grant identity

Desktop uses required `user_config` for the document directory and an OCR switch defaulting to false.
Claude Code keeps its tested explicit installation configuration for the directory and gains the same setup-only OCR option.
Codex uses the bundled worker's `--configure --input-root ABSOLUTE_DIRECTORY` command and adds explicit `--ocr on|off`, defaulting to off.
The persisted configuration remains outside replaceable plugin caches under each client's application-data directory.
Core receives a closed profile configuration; model-facing tools accept neither backend selectors nor OCR switches.
A filename is required from the user; the skill asks when it is absent and never guesses paths or probes directories by trial imports.

Unset, cancelled, or invalid setup produces a nonzero startup exit and a fixed `configuration_required` stderr message before registering tools.
This retains the implemented fail-closed startup model instead of introducing an unconfigured server state.
Guides give the exact host setup command and observed host log location after the host check records it.
They must not promise that a tool returns an error when startup prevented tool registration.

Resolve a deliberately chosen root once, open its canonical directory, and bind the grant to that descriptor's identity.
Symlinks in the user-selected root spelling are allowed at setup; symlinks beneath the granted directory remain refused.
On macOS, obtain the canonical spelling from the opened descriptor using the supported descriptor-path API.
Do not lowercase or Unicode-normalize path strings to guess filesystem identity.
Use device/inode comparisons across opened ancestor chains to refuse identical or overlapping input and artifact roots.
Record canonical path and directory identity in the grant identity so replacing the directory does not inherit its artifacts.
On a case-sensitive volume, differently cased directories remain distinct.
On a case-insensitive volume, aliases of the same opened directory produce one grant.
Use the matched directory-entry spelling for display names and keep artifact identifiers derived from source bytes and engine identity.

Open source components relative to the grant descriptor with no-follow and close-on-exec behavior.
Open the final component nonblocking, require a regular file with `fstat`, then clear nonblocking before copying.
Copy and hash through that same descriptor; the parser reads only the staged copy.
Filesystem permission errors use `os_permission_denied`, distinct from a traversal or nonregular-file `access_denied` error.
Recovery explains that OS or volume permissions may need adjustment; on macOS it points to the host's Files and Folders settings without asserting which process owns the permission before testing it.

## 3. Worker lifecycle and resource profile

The MCP parent never imports Docling, ONNX Runtime, PDFium, or OCR bindings.
A dedicated child owns all engine initialization, preflight, inference, and subprocesses.
The child receives one staged document at a time over a bounded private control channel.
Native diagnostics remain separate from MCP stdout, and child failures become sanitized domain errors.

Use one warm worker per installation with one active import and a proposed 60-second idle shutdown.
A second import returns `busy`; there is no unbounded queue or durable background job.
Each job has an identifier; late results from a cancelled generation are discarded.
Deadline, cancellation, worker crash, memory excess, or control-channel corruption kills and reaps the owned process group before releasing its slot.
Restart lazily on the next explicit import, with no automatic retry of the failed document.
On parent shutdown or disconnect, terminate owned work and remove incomplete staging.
Tests cover cancellation before startup, during model loading, during OCR, and just before commit.

A sampled memory watchdog checks aggregate owned-worker and OCR-process RSS, initially every 100 milliseconds.
Exceeding the configured threshold returns `memory_limit` and kills the process group.
Failure to sample reliably ends the import with a sanitized worker-monitoring failure rather than disabling enforcement.
Shared-memory accounting may overcount; disclose the metric and sampling method.
This is a best-effort sampled limit, not a hard OS memory reservation or protection against allocation bursts.
Model files and warm-worker memory are not charged against the retained-document disk quota.

### Limits and timing acceptance

Keep the existing source, extraction, store, and response byte caps as compatibility constraints until measured evidence requires a separate change.
The revision 1 values are documented beside [the current implementation](../runtime/README.md); they are not Docling throughput promises.
Page count, import deadline, worker RSS ceiling, and idle policy require a measured revision 2 profile before release.
No missing profile field may silently inherit the old 100-page/45-second combination.

The feasibility harness explores cold and warm 1-, 10-, 30-, and 100-page inputs, with OCR off and on.
It includes a base M-series machine and records model initialization, staging, preflight, conversion, commit, peak sampled RSS, and total elapsed time.
Use finite diagnostic caps of 300 seconds and 4 GiB aggregate sampled RSS; these are probe safeguards, not supported product limits.
Record repetitions, raw timings, failures, and sample size; do not infer a reliable 95th percentile from one successful run.

A separate synthetic MCP delay server measures each named host's absolute and inactivity tool-call timeouts, with and without progress notifications.
Progress is emitted only when the caller supplies a progress token, at meaningful stages and at most once per second.
Use monotonically increasing progress values and do not invent page completion percentages during model initialization.
Progress is user feedback, not an assumption that the host extends its deadline.

Choose the largest page cap whose measured cold and warm p95 fits the strictest measured host timeout with at least 20% margin.
The application deadline cannot exceed that host budget, and the SDK trial timeout must allow the frozen retrieval workflow to finish.
If the minimum useful document size cannot fit, stop and review a smaller cap or a separately scoped fast profile.
Do not introduce asynchronous jobs to hide an incompatible timeout.
If the accepted cap excludes the proposed 80-page corpus, revise and refreeze the study before any paid run.
Production limits remain an explicit unresolved measurement output; no support claim exists until that output is reviewed.

## 4. Evidence, OCR, and retrieval

Version the artifact and tool schemas deliberately in core; do not rewrite released schema bytes.
The extraction identity records core, adapter, Docling, docling-parse, PDFium, ONNX Runtime, Tesseract, and preprocessing versions.
It also records layout-weight and tessdata hashes, OCR enablement/languages, table settings, pipeline choice, and dependency-lock hash.
A changed setting or engine creates a distinct artifact; revision 1 artifacts are never relabeled as Docling output.
Keep the original source snapshot so a reviewer can recover the exact bytes parsed after the original changes.
Setup explains the original file plus an additional retained copy, with extraction taking further space.
All retained grants, including inaccessible old grants and staging, count toward the store quota.

Map every Docling provenance entry instead of selecting the first entry or defaulting a missing page to one.
Split item text only where upstream spans establish the page association.
Never duplicate an entire cross-page item onto every page or invent offsets when provenance is ambiguous.
Ambiguous text is omitted from page-addressable evidence with a warning; an import with no usable evidence fails explicitly.
Preserve physical source pages independently of printed labels and convert geometry only from known coordinate systems.

Add measured source-kind values for native, OCR, and mixed-origin passages and search hits.
Source kind follows the actual extraction path, not merely the fact that OCR was enabled.
Where exact origin separation is unavailable, label conservatively as mixed rather than claiming native text.
Quotes remain exact extracted spans; an OCR label does not imply accuracy or confidence.
With OCR off, disclose image-only pages; fail an entirely unreadable document with `no_readable_text`.
With table structure off, test header, cell, and footnote coverage and disclose missing text without fabricating a table.

Name and freeze the retriever revision in the artifact and experiment identities.
Search-side dehyphenation may join a hyphen followed by a line break and lowercase continuation while preserving an offset map to original text.
Stored passages and quoted substrings remain unchanged; joined search terms never rewrite evidence.
Add a synthetic offline retrieval gate with two or three frozen ordinary-language queries per answerable task.
Every required supporting page must appear in the top five results of at least one registered query, and every answerable task must pass before paid trials.
Evaluate individual-query recall separately, and keep these diagnostic queries hidden from the model prompts.
Add line-break hyphens, ligatures, columns, repeated headers, mismatched printed page numbers, and a table footnote to the corpus.
Missing-fact questions use a separate scoped-refusal rubric; they cannot have positive retrieval ground truth.
If common-term flooding still fails the gate, evaluate a separately versioned deterministic term-weighting change and rerun the same frozen queries.

Keep read atomic: one unknown evidence identifier fails the request with `evidence_not_found`.
The model uses returned identifiers and cursor continuation; it is never instructed to construct neighboring identifiers.
Page-scoped navigation and PDF outlines remain later scope unless the recall gate demonstrates a concrete need.
Keep complete artifact verification on load and import reuse initially.
Measure its cost before considering per-operation verification, which would require a new integrity dependency proof.
Do not replace staged copy-and-hash with a hash-only cache lookup that reopens mutable source paths.
The durability promise remains survival of process restart, not guaranteed power-loss persistence.

Tool descriptions carry retrieval limits once; the receipt does not repeat the limit table.
Skills identify import/search/read by purpose and tolerate host-qualified names observed in compatibility tests.
Coding-client answers include evidence identifiers; Desktop may show filename, physical page, quote, and OCR label without displaying the identifier.
The test record must still resolve that displayed quote to exact evidence, and ambiguity is a failed citation check.

## 5. Signing, packaging, and fallback

Developer ID signing and notarization are prerequisites for a distributed native candidate, not optional cleanup after installation testing.
Inventory the launcher, Python library, extension modules, ONNX Runtime, PDFium, Tesseract, Leptonica, and transitive native image libraries.
Sign nested components in dependency order, use the hardened runtime, and record each entitlement and its demonstrated need.
Do not enable broad entitlement exceptions speculatively.
Freeze and verify final signed bytes; signing after an inventory was hashed changes those bytes and invalidates it.
Include licenses for the interpreter, native libraries, model weights, and OCR data, plus source-offer obligations where applicable.

Test downloaded archive quarantine, executable bits after host extraction, notarization lookup, and online/offline first launch.
The selected fallback for an MCPB extraction or ticket-layout failure is a signed, notarized app/installer containing the same engines, with a thin MCP launcher.
This changes installation evidence and must pass the same no-user-Python acceptance test before release.
If that fallback also fails, keep the developer harness only and block binary release.
Host-managed Python and a different parser are alternatives requiring a separate product decision, not automatic substitutes.
Missing signing credentials defer distribution; they do not authorize bypassing Gatekeeper or asking users to disable protection.

Use a snapshotted Apple Silicon macOS VM with recorded image identity for the clean-host check.
A fresh user on the developer machine is insufficient evidence.
Record client versions, archive size, installed size, download/extraction time, startup hashing time, host limits, and whether developer tools are installed.
Observe child processes to prove the worker never invokes system Python or its developer-tools shim.
Record actual log locations and sanitized recovery steps after observing each client.
Codex plain MCP registration is an explicitly named integration fallback if a future pinned client cannot load plugins; it is not plugin-support evidence.
Installation and release execution remain deferred as requested by the owner.

## 6. References and unresolved evidence

[Docling advanced options](https://docling-project.github.io/docling/usage/advanced_options/) documents explicit local artifact paths.
[Docling pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/) and [installation guidance](https://docling-project.github.io/docling/getting_started/installation/) are inputs to the pinned feasibility check.
Their current APIs are not a substitute for running the selected locked dependency set.
[Apple notarization guidance](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) establishes the signing and hardened-runtime workflow.
[Apple packaging guidance](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution) informs the container fallback.

Unresolved evidence is named rather than guessed: torch-free pipeline execution, table-text coverage, mixed OCR provenance, measured host deadlines, resource constants, and complete licensing/notarization results.
The [implementation plan](implementation-plan.md) assigns each one a pass/fail task before dependent work.
