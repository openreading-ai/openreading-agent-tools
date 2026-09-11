# Revision 3 implementation plan

**Status:** assistant integration is proposed. Revision 2 developer engine, retrieval, and Claude M0 tooling exist; Docling client distribution remains unbuilt.
**Contracts:** [ProductSpec revision 3](../product/specs/local-document-proof.product-spec.md), [assistant integration](assistant-clients.md), [engine design](local-document-proof.md), and [evaluation design](token-evaluation.md).

Continue on the existing feature branches and preserve unrelated work.
Never merge either repository's PR automatically.
Each implementation commit names the acceptance criteria it addresses and leaves unmet host checks explicit.
A passing offline gate is necessary but cannot replace native application, signing, or paid-study evidence.

ProductSpec revision 3 changes client scope and measurement intent.
It does not rename `local-document-proof-v2`, modify historical locks, or authorize paid calls.
Revision 1 binaries and revision 2 probe manifests retain their original meanings.
The current documentation task completes N0's contract and independent protocol investigation only.
Actual host connection, installation, and model invocation remain pending.

## Existing baseline

The [feasibility guide](../runtime/feasibility/README.md) owns the implemented Docling candidate, immutable lock, and reproduction commands.
Core owns the adapter, worker supervision, provenance, retained artifacts, and lexical retrieval contracts.
The [measurement guide](../measurement/README.md) owns the implemented corpus, retrieval/restart gate, and unscored Claude M0 driver.
Use those current contracts rather than copying historical core commits, test counts, or retriever constants from a proposal.
The [review dispositions](review-disposition.md) preserve unresolved design obligations and earlier decisions.

These developer checks do not establish a supported page cap, native client compatibility, or a signed distribution.
No further parser implementation belongs in a client adapter.

## N0. Assistant contract and connection feasibility

Acceptance: AC-23 through AC-25. Files: ProductSpec, assistant design, client READMEs, repository index.

- [x] Define primary Claude Desktop and ChatGPT desktop targets, with Claude Code and Codex as separate developer surfaces.
- [x] Preserve the selected engine, core surface boundaries, historical execution contracts, and deferred alternate backends.
- [x] Inspect current official connection guidance and installed CLI registration syntax without changing host configuration.
- [x] Run independent STDIO initialization, tool listing, and outside-grant refusal against the pinned Docling candidate.
- [x] Record missing native evidence in the client matrix instead of transferring results between clients.
- [ ] Observe the native configuration interface and executable launch for both primary desktop targets.

The ChatGPT UI check is currently unavailable because the computer-use tool refused access to the installed app.
Do not bypass that restriction or treat an API invocation as an alternative UI check.
A later owner-operated check can close it using the named app/version and synthetic input.
Stop a client-specific implementation if its documented connection does not exist in the selected application mode.
Other common implementation work can continue without that unsupported claim.

## N1. Common configuration and launcher migration

Prerequisites: reviewed revision 3 contract and usable core candidate.
Acceptance: AC-2, AC-4, AC-13, AC-21, AC-23, AC-25.
Owners: `runtime/configuration.py`, `runtime/entrypoint.py`, runtime tests, and the runtime README.

1. Write failing tests for the proposed closed version 2 setup object, explicit OCR defaults, direct-versus-persisted precedence, and unknown fields.
2. Test missing grants, relative paths, cancelled setup, legacy settings, invalid replacements, changed roots, spaces, and Unicode.
3. Extend the existing configuration reader and atomic writer using core grant validation; do not create a second path-security implementation.
4. Add the proposed `chatgpt` client label and setup-only OCR flag, treating labels solely as storage selection.
5. Build the core profile from verified release resources and reviewed limits; keep model tools unable to select engines, URLs, or OCR.
6. Preserve historical settings on failure and require explicit setup before migration; do not reinterpret revision 1 stores.
7. Test that ordinary core behavior never depends on this configuration and that no provider SDK enters the document runtime.
8. Update flag help, startup-error guidance, retained-data cleanup, and configuration examples beside their implementation.

Resource defaults are a C1 measurement output, not values for an agent to invent.
An intermediate developer launcher may require an explicitly labeled diagnostic profile; it cannot be packaged as release-ready.
Pass focused regressions and `make verify`; prove fix-removal failures for defects discovered during implementation.
Commit configuration and launcher changes together only when their tests pass.

## N2. Thin host adapters and native functional checks

Prerequisites: N1 plus the corresponding N0 native connection observation.
Acceptance: AC-1, AC-11, AC-12, AC-14, AC-24, EVAL-1.
Owners: `clients/`, `runtime/package.py`, the existing shared skill, adapter tests, and client READMEs.

1. Inspect the existing packaging implementation and keep the common runtime independent of any one host manifest format.
2. Add host-specific setup translation and workflow delivery using the shared configuration semantics.
3. Test argument arrays with shell metacharacters, spaces, Unicode, absent configuration, and host-qualified tool names.
4. Test that every wrapper resolves the same profile, tool schemas, and workflow text without importing provider SDKs.
5. For OpenAI's shared MCP settings, disclose the actual set of clients receiving the registration and grant.
6. Use the assistant design's synthetic functional matrix in each native application and record the exact executable and tool calls.
7. Include cancellation, restart, outside-root refusal, OCR setup, missing facts, document instructions, and exact citations.
8. Record application/version/mode, platform, runtime identity, setup path, instruction channel, and any required host permission.

Keep host configuration changes scoped and reviewable; preserve preexisting registrations.
If a model call requires an unapproved account or spend, stop that case and continue offline work.
Source-runtime checks are developer evidence only; packaged installation remains P1/H1.
A host without a skill mechanism gets supported instructions, not a fork of the evidence workflow.
Do not implement a tunnel or HTTP bridge to rescue an unavailable local connection.

## C1. Remaining engine and host resource evidence

Acceptance: AC-4, AC-9, AC-21, AC-22. Owners: candidate harness, core tests, and host probes.

- [ ] Inspect mixed-origin passages and native cross-page provenance; page-marker fixtures alone do not cover either.
- [ ] Close broader table/footnote and orientation-detection gaps with selected-engine evidence or explicit limitations.
- [ ] Verify cancellation before startup, during model loading, during OCR, and immediately before artifact commit.
- [ ] Add base M-series measurements, independent cold/warm repetitions, and staging/preflight/commit timing.
- [ ] Measure each native host's absolute and inactivity timeout with and without progress notifications.
- [ ] Select page cap, deadline, sampled RSS ceiling, idle policy, and trial timeout using the engine design's p95 margin rule.
- [ ] Stop release when useful imports cannot fit; do not introduce asynchronous jobs or an unapproved fallback profile.

The developer harness's 300-second/4-GiB limits are diagnostic safeguards, not release defaults.
If the accepted cap excludes a corpus document, revise and refreeze the study before live execution.
Packaging must preserve complete engine identity, including installed dependency metadata, source files, OCR configuration, and native versions.

## M0. Cheap existing Claude probe before packaging spend

Acceptance: diagnostic only; M0 cannot pass AC-17 or establish public savings.
Owners: existing measurement driver and its private evidence directory.
Prerequisites: matching engine/retrieval/restart evidence and explicit owner approval of account, manifest hash, model, and finite budget.

- [ ] Revalidate the prepared draft against current executable sources and environment; regenerate only when its bound inputs changed.
- [ ] Finalize after the owner selects the exact model, account, and dated prices. Finalization alone is not spending approval.
- [ ] Run the frozen nine trials only after approval, retaining failures, limited baselines, incomplete usage, and mixed document access.
- [ ] Review paired answer quality before interpreting direction, reporting actual character sizes alongside page counts.
- [ ] Decide whether to pursue a token headline or emphasize installation and citations from the observed outcome.

This documentation revision does not invalidate an otherwise matching version 2 draft by itself.
Do not relabel it revision 3 or enlarge its budget to include another provider.
A negative or incomplete probe is a finding, not a reason to handicap the baseline.

## M1. Provider-neutral measurement extension

Prerequisites: N0 contract, existing fair baseline, and verified complete counters for the selected additional execution surface.
Acceptance: AC-15 through AC-18, EVAL-2.
Owners: `measurement/` adapters and versioned schemas, accounting/report modules, synthetic log fixtures, and measurement README.

1. Inventory the existing runner's execution, permission, identity, budget, and accounting boundaries before extracting shared code.
2. Preserve the version 1 driver and version 2 Claude probe; write new closed version 3 manifest/trial contracts with explicit provider and surface.
3. Move provider execution behind the design's small adapter interface with fixture tests proving unchanged Claude outcomes.
4. Investigate instrumented Codex usage first; choose an OpenAI API harness only as an explicitly reviewed, separately labeled baseline.
5. Verify pinned raw-counter semantics and test caches, cumulative updates, nested work, retries, errors, missing usage, and reasoning/output overlap.
6. Freeze usable A tools and identical B/C extraction, including physical-page citation information and treatment instructions.
7. Preserve environment and artifact identity checks, raw-event resume verification, frozen prices, approved budgets, and stop reasons.
8. Generate independent provider reports with quality-gated comparisons, all failures, actual input sizes, and C adherence.
9. Add calibration, null controls, and the separately registered primary/follow-up schedules before claiming full-study support.
10. Require separate owner approval for every provider run; no live invocation belongs in `make verify`.

Do not introduce a generic API loop that lacks the ordinary tools the comparison claims to represent.
If a native chat host lacks complete counters, keep it functional-only rather than estimating hidden tokens.
All affected Python and Node coverage metrics retain their enforced 95% floors.
New accounting and budget regressions must fail when their fixes are removed.

## P1. Later signed distribution

Prerequisites: C1 release profile, reviewed native connection routes, and M0 decision.
Acceptance: AC-1, AC-13, AC-19.
Owners: runtime lock, build/verifier, package metadata, notices, packaging tests, and client guides.

- [ ] Pin the passing core and complete runtime; reject prohibited packages and verify model, metadata, source, and tessdata inventory.
- [ ] Inventory every collected dependency and applicable notice, rather than presenting the build-environment superset as an exact distribution audit.
- [ ] Sign nested native components, record minimal entitlements, notarize, and then hash the final installed representation.
- [ ] Exercise the signed app/installer fallback if MCPB extraction or notarization layout fails.
- [ ] Record archive/installed size, extraction, full integrity-check cost, and online/offline first-launch behavior.

Missing signing credentials block distribution, not offline implementation.
No unsigned fallback or instructions to bypass OS protections are permitted.

## H1. Clean-host release and pilot

Prerequisites: signed candidate and owner-authorized host/pilot work.
Acceptance: AC-1, AC-2, AC-11 through AC-14, AC-19, AC-20, AC-24, and pilot metrics.

- [ ] Use a snapshotted clean Apple Silicon VM with image identity and no user-installed interpreter or developer-tool dependency.
- [ ] Verify Claude Desktop and ChatGPT desktop separately; record executable resolution, actual local execution, and cited answers.
- [ ] Verify Claude Code and Codex separately before labeling their Docling distributions supported.
- [ ] Test setup cancellation, root changes, permissions, process cleanup, update, removal, retained-data cleanup, spaces, and Unicode.
- [ ] Record actual host logs and recovery steps; do not infer which process needs OS permissions without observing it.
- [ ] Review evidence and any public claims before the five-participant pilot or distribution.
- [ ] Move implemented facts beside code and delete completed proposal sections without deleting unmet requirements.

No release or merge occurs automatically when tests pass.
