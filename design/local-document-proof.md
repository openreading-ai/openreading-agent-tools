# Docling local proof migration design

**Status:** remaining revision 2 migration and release contract. Core mechanisms and the isolated feasibility harness are implemented; distributed clients remain revision 1.
**Intent:** [ProductSpec revision 6](../product/specs/local-document-proof.product-spec.md).
**Review:** [finding dispositions](review-disposition.md) record accepted changes and reasoned exceptions.

OSS product v1 launches before managed product v2. The [launch design](oss-launch.md) requires complete pinned-core MCP coverage and a static Coming soon visual only; no managed components are part of this work. Internal v2 profiles and settings keep their existing local meaning.

## 1. Engine decision and boundaries

The first distributed profile becomes `local-document-proof-v2`, using an in-process Docling adapter owned by core.
The existing core `docling` HTTP adapter remains separate and compatible.
The implemented adapter identifier is `docling_local`; its descriptor controls its supported formats and capabilities.
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

The [runtime guide](../runtime/README.md) owns the implemented shared configuration contract.
The [assistant integration design](assistant-clients.md) owns the remaining native setup work.
It preserves explicit grants, setup-only OCR disabled by default, and settings outside replaceable plugin caches.
Core receives a closed profile configuration; model-facing tools accept neither backend selectors nor OCR switches.
A filename is required from the user; the skill asks when it is absent and never guesses paths or probes directories by trial imports.

Unset, cancelled, or invalid setup produces a nonzero startup exit and a fixed `configuration_required` stderr message before registering tools.
This retains the implemented fail-closed startup model instead of introducing an unconfigured server state.
Guides give the exact host setup command and observed host log location after the host check records it.
They must not promise that a tool returns an error when startup prevented tool registration.

Core now owns implemented grant behavior in `openreading.artifacts.intake` and `openreading.artifacts.store`.
Client integration must preserve those descriptor-bound roots and distinguish OS permissions from traversal errors.
Matched directory-entry display spelling and actual host-specific permission recovery still need client evidence.
Do not guess the responsible macOS permission process before observing the installed host.

## 3. Worker lifecycle and resource profile

The supervised worker contract is implemented in core's `openreading.artifacts.supervisor`, `worker`, and MCP modules.
Use the [candidate harness](../runtime/feasibility/README.md) and its immutable dependency pin to reproduce engine checks.
The launcher must pass explicit resource limits and close the service during shutdown.
Record host cancellation notifications, deadlines, and process termination as distinct interruption paths; absence of a host cancel button stays explicit.
Packaging must preserve private control descriptors and owned process-group cleanup.
These integration obligations still need installed-host validation.
Regression tests must cover cancellation before startup, during model loading, during OCR, and just before commit.
Cancellation during an OCR child has developer observation only; treat each missing stage test as open work.

### Limits and timing acceptance

[OpenAI's MCP guide](https://learn.chatgpt.com/docs/extend/mcp) documents 10-second startup and 60-second tool-call defaults.
It also documents a 1000-ms optional-server catalog grace and configurable overrides.
These are starting hypotheses for the installed mode, not measured deadlines or fixed platform ceilings.
E2 must record startup, initial tool visibility, eventual discovery, and per-call timeout separately under the actual setup route.
Claude Desktop limits remain unverified; do not assume its SDK supplies the same defaults.

Keep full inventory verification before core import, worker dispatch, and MCP registration; do not move it to the first parse.
The Python/freezer bootstrap and verifier necessarily execute to perform that check; do not claim verification precedes all executable code.
The startup allowance means the initialization timeout, not the optional-server catalog grace.
A server missing the initial catalog may pass only if E2 proves later discovery and the guide waits for explicit ready/tool visibility before the first question.
If later discovery fails, that registration remains unsupported; do not weaken identity to fit a one-second catalog window.
Measure frozen cold startup from process creation through inventory verification and MCP initialization.
Worker startup repeats verification in the current launcher, so include that cost in cold import timing too.
Require cold/warm startup p95 within 80% of the observed startup allowance and imports within 80% of the observed tool allowance.
Unmodified 10/60-second limits imply 8-second startup and 48-second import budgets.
A verified alternative registration may change them; unsupported manual TOML edits cannot rescue the nondeveloper path.
Do not assume progress extends an absolute deadline or that a server absent from the initial catalog becomes discoverable later.

Keep the existing source, extraction, store, and response byte caps as compatibility constraints until measured evidence requires a separate change.
The revision 1 values are documented beside [the current implementation](../runtime/README.md); they are not Docling throughput promises.
Page count, import deadline, worker RSS ceiling, and idle policy require a measured revision 2 profile before release.
No missing profile field may silently inherit the old 100-page/45-second combination.

The feasibility harness explores first and warm 1-, 10-, 30-, and 100-page inputs, with OCR off and on.
It currently records first-conversion time including initialization, conversion with projection, peak sampled RSS, and total cell time.
The release measurement must add a base M-series machine and separate staging, preflight, and commit phases.
Use finite diagnostic caps of 300 seconds and 4 GiB aggregate sampled RSS; these are probe safeguards, not supported product limits.
Record repetitions, raw timings, failures, and sample size; do not infer a reliable 95th percentile from one successful run.

A separate synthetic MCP delay server measures each named host's absolute and inactivity tool-call timeouts, with and without progress notifications.
Progress is emitted only when the caller supplies a progress token, at meaningful stages and at most once per second.
Use monotonically increasing progress values and do not invent page completion percentages during model initialization.
Progress is user feedback, not an assumption that the host extends its deadline.

Choose the largest page cap whose measured cold and warm p95 fits the strictest measured timeout among release-included modes with at least 20% margin.
Adding a later mode requires revalidating the shared profile; an untested mode cannot block a truthful narrower release or inherit its evidence.
The application deadline cannot exceed that host budget, and the SDK trial timeout must allow the frozen retrieval workflow to finish.
If the minimum useful document size cannot fit, stop and review a smaller cap or a separately scoped fast profile.
Do not introduce asynchronous jobs to hide an incompatible timeout.
If the accepted cap excludes a document, record the refusal and do not claim support for its size.
Register separate large-document Desktop fixtures within measured limits; keep the original citation corpus unchanged.
Production limits remain an explicit unresolved measurement output; no support claim exists until that output is reviewed.

## 4. Evidence, OCR, and retrieval

Core's v0.3 artifact and tool contracts implement engine identity, physical-page spans, and measured text origins.
Their owning documentation is `openreading.artifacts.models`, `service`, and `adapters.docling_local.projection`.
The client migration must consume those contracts without relabeling revision 1 artifacts or inventing page associations.
Explain retained source copies during setup and preserve OCR labels in answers.
The implemented corpus, frozen queries, and real retrieval checks are documented in the [measurement guide](../measurement/README.md).
The source schema preserves blank and unknown origins; lexical search keeps original offsets when joining line-break hyphens.
Missing-fact and adversarial-document answers remain a model and human quality gate.
Page-scoped navigation and PDF outlines remain later scope unless measured retrieval failures demonstrate a need.

Keep read atomic: one unknown evidence identifier fails the request with `evidence_not_found`.
The model uses returned identifiers and cursor continuation; it is never instructed to construct neighboring identifiers.
Keep complete artifact verification on load and import reuse initially.
Measure its cost before considering per-operation verification, which would require a new integrity dependency proof.
Do not replace staged copy-and-hash with a hash-only cache lookup that reopens mutable source paths.
The durability promise remains survival of process restart, not guaranteed power-loss persistence.

Tool descriptions carry retrieval limits once; the receipt does not repeat the limit table.
Skills identify import/search/read by purpose and tolerate host-qualified names observed in compatibility tests.
Coding-client answers include evidence identifiers; Desktop may show filename, physical page, quote, and OCR label without displaying the identifier.
The test record must still resolve that displayed quote to exact evidence, and ambiguity is a failed citation check.

## 5. Signing, packaging, and fallback

Developer ID signing and notarization are prerequisites for distributing a native candidate to another machine or user.
A bounded unsigned P0 build may run on the development machine without becoming a distributable candidate.
Owner-authorized native development tests may use it locally; they never authorize bypassing OS protection or sharing it.
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

Unresolved evidence includes broader table/footnote coverage, cross-page provenance from engine output, orientation detection, base-machine and host deadlines, resource constants, and complete licensing/notarization results.
The feasibility guide records developer-engine observations separately from these release requirements.
The [implementation plan](implementation-plan.md) assigns each one a pass/fail task before dependent work.
