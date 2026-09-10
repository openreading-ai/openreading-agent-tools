# Revision 2 implementation plan

**Status:** design corrections first; Docling migration, new studies, and release checks remain unbuilt.
**Contract:** [ProductSpec revision 2](../product/specs/local-document-proof.product-spec.md), [engine design](local-document-proof.md), and [evaluation design](token-evaluation.md).

Continue on the existing feature branches. Never merge the review branch or either implementation PR automatically.
The review branch supplies feedback, not executable changes or empirical evidence.
Existing runtime locks and trial records identify the historical revision 1 prototype; never relabel them revision 2.
No new production runtime pin or scored study can claim revision 2 until its corresponding implementation passes.

## R0. Contract revision and review

Files: the ProductSpec, these three designs, [review dispositions](review-disposition.md), and repository status/index READMEs.

- [ ] Review the engine decision, setup-only OCR, signing fallback, strict read behavior, and timing decision rule.
- [ ] Carry the required adapter/artifact changes into core's unbuilt design records before changing its public schemas.
- [ ] Identify changed and preserved acceptance criteria without transferring revision 1 package evidence to Docling.
- [ ] Confirm `make sync`, `make verify`, and ProductSpec validation evidence for the reviewed revision.

This review pass is documentation work. It does not execute installation, notarization, or a paid model probe.

## C1. Engine and timeout feasibility before packaging

Proposed owners: core `adapters/docling_local/` and `artifacts/worker.py`; tools `runtime/` feasibility checks.
Acceptance: AC-4, AC-9, AC-21, AC-22.

- [ ] Pin a candidate torch-free Docling/PDFium/ONNX dependency set in an isolated harness, including transformers preprocessing.
- [ ] Run with prohibited packages absent, weights/data local, network blocked, OCR off and explicitly on.
- [ ] Inspect table-region text, mixed-origin passages, and every cross-page provenance entry.
- [ ] Measure the engine matrix and synthetic host-timeout probe defined in the engine design.
- [ ] Derive the release page cap, deadline, RSS threshold, idle policy, and SDK trial timeout from those measurements.
- [ ] Record exact incompatibilities and stop if the selected engine or useful page cap cannot satisfy the contract.

Do not infer performance from upstream report medians or silently adopt the old profile constants.
RapidOCR and ocrmac may be compared later as diagnostic alternatives; Tesseract remains selected unless the owner changes that decision.
Native host timing measurements can wait with installation testing, but no dependent support claim can pass without them.

## C2. Core adapter, identity, and worker supervision

Files: core's new adapter descriptor and methods, vendored schema revisions, artifact models/service/worker, CLI profile configuration, and focused tests.
Acceptance: AC-3 through AC-10, AC-21, AC-22.

- [ ] Add the in-process adapter independently of the existing Docling HTTP adapter; follow core's adapter conformance runbook.
- [ ] Move preflight to PDFium in the child and prove the parent never imports engine bindings.
- [ ] Implement bounded warm-worker control, sampled process-tree memory monitoring, progress, idle shutdown, cancellation, and process-group cleanup.
- [ ] Add engine/weight/data/settings identity and conservative native/OCR/mixed provenance without invented page-one defaults.
- [ ] Canonicalize chosen roots once; verify directory identities and ancestor overlap using descriptors.
- [ ] Add OS-permission errors, nonblocking FIFO rejection, root replacement/case/Unicode tests, and retained-store cleanup guidance.
- [ ] Preserve exact-copy hashing, strict reads, complete integrity checks, and process-restart durability.
- [ ] Add failing tests before each behavior and demonstrate regressions fail when their fixes are removed.
- [ ] Run core `make verify` before committing an immutable dependency candidate.

## C3. Corpus and offline retrieval gate

Files: tools `measurement/prepare.py`, public synthetic generation manifest/rubric, and offline tests; core lexical search and passage tests.
Acceptance: AC-7, AC-11, AC-22; prerequisites for EVAL-1 and EVAL-2.

- [ ] Replace the synthetic generator's PyMuPDF dependency with a permitted deterministic PDF-generation toolchain.
- [ ] Publish the synthetic questions, answers, task-kind mapping, generation recipe, expected hashes, and diagnostic query set.
- [ ] Prove byte-identical independent generation and isolate ground truth outside live document grants.
- [ ] Include the extraction edge cases named in the engine design.
- [ ] Version search identity, add offset-preserving dehyphenation, and enforce top-five supporting-page recall across the frozen answerable tasks.
- [ ] Keep missing-fact and adversarial-document behavior separate from positive retrieval recall.

Do not pay for model trials while this deterministic gate fails.

## M0. Cheap unscored token probe

Files: tools measurement schema, harness configuration, driver, and offline fixture tests.
Prerequisites: selected engine executes and C3 passes; explicit owner approval of account, manifest, and finite budget.

- [ ] Implement the nine-trial developer-harness probe from the evaluation design without requiring native packaging.
- [ ] Verify per-model counters, arm inventories, calls, latency, and stop-budget behavior against offline fixtures.
- [ ] Prepare a concrete frozen manifest for review. Its creation is not spending approval.
- [ ] Run only after approval, retain all failures, and report direction by document size without a public savings percentage.
- [ ] Choose the next product emphasis from measured evidence; a negative token result preserves the installability-and-citations goal.

M0 precedes further packaging expenditure. Historical packaging work is not erased or treated as evidence for this engine.

## C4. Client configuration and workflow

Files: `runtime/configuration.py`, `entrypoint.py`, client manifests/READMEs, shared skill, and offline tests.
Acceptance: AC-2, AC-11, AC-12, AC-14, AC-21.

- [ ] Keep explicit Claude Code install configuration and Codex persisted setup; add setup-only OCR disabled by default.
- [ ] Test missing/invalid setup, cancellation, changed grants, OCR settings, and configuration persistence outside plugin caches.
- [ ] Explain additional retained copies, local vision inference, shared excerpts, and manual cleanup.
- [ ] Ask for absent filenames and recognize host-qualified tools by purpose; never guess neighbor evidence identifiers.
- [ ] Make identifiers optional in Desktop presentation while preserving exact citation resolution in evidence.

## M1. Revision 2 measured study tooling

Files: measurement manifest and trial schemas, prepare/run/accounting/report modules, public corpus, and tests.
Acceptance: AC-15 through AC-18 and EVAL-2.

- [ ] Add the closed revision 2 manifest and trial record contracts; retain revision 1 as historical evidence only.
- [ ] Add null controls, per-tool adherence, effective plugin configuration, per-model prices, and partial-blinding projections.
- [ ] Enforce shared task-kind and document-category quality checks and complete usage across all arms.
- [ ] Support the separately budgeted preregistered follow-up sessions without double-counting cumulative usage.
- [ ] Derive the primary budget from calibration, disclose worst-case schedule cost, and refuse a scored claim from an incomplete run.
- [ ] Preserve every failure and unrun reason; keep the primary input-volume rules unchanged by secondary cost estimates.

No live study runs during this design-fix task.

## P1. Later distribution gate

Files: runtime lock/build/verifier/package metadata and tests. Acceptance: AC-1, AC-13, AC-19.

- [ ] Pin the passing core and engine revisions; reject prohibited dependencies and verify weights and tessdata in the final inventory.
- [ ] Inventory interpreter and all native/data/model licenses before sharing binaries. The current build-environment notice superset is insufficient for exact collected-dependency review (CR-4b).
- [ ] Sign nested native code, record minimal entitlements, notarize, then hash and verify the final install representation.
- [ ] Exercise the selected signed app/installer fallback if native MCPB extraction or ticket handling fails.
- [ ] Record size, extraction time, startup cost, child executable identities, and offline/online first-launch behavior.

Do not publish an unsigned fallback or tell pilot users to bypass OS protection.

## H1. Later host and release evidence

Acceptance: AC-1, AC-2, AC-11 through AC-14, AC-19, AC-20, EVAL-1, and pilot metrics.

- [ ] Use a snapshotted clean Apple Silicon VM, record image identity, and verify no developer tools or Python shim are invoked.
- [ ] First record Desktop installation and executable launch, including extraction permissions and command resolution (CR-2). MCPB resolver tests alone do not pass this gate.
- [ ] Measure full-tree verification and cold/warm host startup without weakening integrity checks (CR-4d). Installation remains deferred by the owner.
- [ ] Complete Desktop, Claude Code, and Codex cited-answer checks on individually named versions.
- [ ] Record setup cancellation, permission prompts, restart, update, removal, read-only inputs, changed roots, spaces, Unicode, and host logs.
- [ ] Run approved calibration and primary/follow-up studies separately, review quality, and report the supported outcome.
- [ ] Complete the five-person pilot only after distribution approval.
- [ ] Move implemented facts beside code and remove completed design sections as each migration stage lands.
