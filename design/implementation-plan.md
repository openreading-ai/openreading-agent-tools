# Revision 5 implementation plan

**Status:** shared configuration, P0 diagnostic freezing, E0 and synthetic probe tooling are implemented. Native client adapters, release packaging and Desktop proof remain proposed.
**Contracts:** [ProductSpec revision 5](../product/specs/local-document-proof.product-spec.md), [assistant integration](assistant-clients.md), [engine design](local-document-proof.md), and [evaluation design](token-evaluation.md).

Continue on the existing feature branches and preserve unrelated work.
Never merge either repository's PR automatically.
Each implementation commit names the acceptance criteria it addresses and leaves unmet host checks explicit.
A passing offline gate is necessary but cannot replace native application or signing evidence.

ProductSpec revision 5 resolves mode-specific acceptance, setup, configuration coexistence, host budgets, citation checks, and study prerequisites.
Revision 5 prohibits provider API trials and removes their release prerequisites.
It preserves `local-document-proof-v2`, historical locks, native acceptance, and owner-operated Desktop testing.
Revision 1 binaries and revision 2 probe manifests retain their original meanings.
This documentation pass adjudicates the review and defines E0 through E6 in the [probe plan](native-probes.md).
The implementation adds developer protocol and frozen-runtime checks. Native host installation, client registration and model invocation remain separate gates.
N1, bounded P0 build work, and independently authorized native probes can begin without waiting on ChatGPT support.
P0 assembles the diagnostic candidate alongside N1 and consumes its frozen-launch changes before N2.
Then use measured C1 limits for release, perform Claude N2 first, and admit ChatGPT N2 only after E1.
M0/M1/M2 are retired. P1 precedes clean-host H1 without an API-study dependency.

## Existing baseline

The [feasibility guide](../runtime/feasibility/README.md) owns the implemented Docling candidate, immutable lock, and reproduction commands.
Core owns the adapter, worker supervision, provenance, retained artifacts, and lexical retrieval contracts.
The [measurement guide](../measurement/README.md) owns the implemented corpus, retrieval/restart gate, and offline historical accounting.
Use those current contracts rather than copying historical core commits, test counts, or retriever constants from a proposal.
The [review dispositions](review-disposition.md) preserve unresolved design obligations and earlier decisions.

These developer checks do not establish a supported page cap, native client compatibility, or a signed distribution.
No further parser implementation belongs in a client adapter.

## N0. Assistant contract and connection feasibility

Acceptance: AC-23 through AC-25. Files: ProductSpec, assistant design, client READMEs, repository index.

- [x] Define Claude Desktop and conditional ChatGPT Chat-mode acceptance, with Work and Codex local threads separately identified.
- [x] Preserve the selected engine, core surface boundaries, historical execution contracts, and deferred alternate backends.
- [x] Inspect current official connection guidance and installed CLI registration syntax without changing host configuration.
- [x] E0: retain the reproducible tool-list/refusal check with stable schema hashes and exact reads across two fresh processes.
- [x] Record missing native evidence in the client matrix instead of transferring results between clients.
- [ ] E1: establish the exact local ChatGPT mode, form, shared settings, approval prompts, and trace export.
- [ ] E5: verify Claude Desktop form substitution, cancellation, and log capture.

The ChatGPT UI check is currently unavailable because the computer-use tool refused access to the installed app.
Do not bypass that restriction or treat an API invocation as an alternative UI check.
A later owner-operated check can close it using the named app/version and synthetic input.
The selected ChatGPT setup candidate is a signed helper app plus an argument-free executable path pasted into native Settings.
Do not write shared TOML or substitute Codex-mode evidence for the Chat conversation target.
Stop ChatGPT-specific N2 if E1 cannot establish that mode and setup route; Claude Desktop remains independently releasable.
Other common implementation work can continue without that unsupported claim.

## N1. Common configuration and launcher migration

Implemented under ProductSpec revision 5. Its durable behavior and remaining native checks live in the [runtime guide](../runtime/README.md).
Tests cover closed settings, exact OCR tokens, atomic replacement, grant refusal, direct-versus-saved precedence and v1/v2 coexistence.
Independent profile lifetimes, exceptional cleanup and verified resource paths are exercised offline.
The diagnostic launcher does not complete host-dependent AC-2, AC-13 or AC-23 by itself.
C1 still owns supported limits, and N2 still owns actual form substitution and client installation.

## N2. Thin host adapters and native functional checks

Prerequisites: N1, passing P0, and the corresponding E1/E5 native setup observation. Start Claude Desktop first; ChatGPT waits on E1.
Acceptance: AC-1, AC-11, AC-12, AC-14, AC-24, EVAL-1.
Owners: `clients/`, `runtime/package.py`, the existing shared skill, adapter tests, and client READMEs.

1. Inspect the existing packaging implementation and keep the common runtime independent of any one host manifest format.
2. Add host-specific setup translation and workflow delivery using the shared configuration semantics.
3. After E1, implement the named argument-free ChatGPT entrypoint and Python/tkinter helper in assistant design section 7, including inventory, coverage, and native GUI checks.
4. Test argument arrays with shell metacharacters, spaces, Unicode, absent configuration, and host-qualified tool names.
5. Test that every wrapper resolves the same profile, tool schemas, and workflow text without importing provider SDKs.
6. For OpenAI's shared MCP settings, disclose the actual set of clients receiving the registration and grant.
7. Use frozen corpus task IDs and the page-2 instruction fixture; never regenerate the corpus to match a stale spec example.
8. Use the implemented [citation checker](../measurement/README.md#citation-evidence-checker) and add verified per-host transcript/tool capture. Native capture provenance and human completeness review remain required.
9. Verify restart, refusals, OCR, and the observed E3 interruption paths; unsupported cancellation stays explicit.
10. Record application/version/mode, local process ancestry, runtime identity, setup path, instruction channel, approval prompts, and required host permissions.

Keep host configuration changes scoped and reviewable; preserve preexisting registrations.
Use only the owner-authorized Desktop app for model-assisted checks. Provider API calls and SDK substitutes are prohibited.
The existing launcher refuses source execution; N2 uses the P0 frozen candidate with owner-authorized local installation.
Keep signing and clean-machine evidence in P1/H1; an unsigned candidate is not distributed.
A host without a skill mechanism gets supported instructions, not a fork of the evidence workflow.
Do not implement a tunnel or HTTP bridge to rescue an unavailable local connection.

## C1. Remaining engine and host resource evidence

Acceptance: AC-4, AC-9, AC-21, AC-22. Owners: candidate harness, core tests, and host probes.

- [ ] Inspect mixed-origin passages and native cross-page provenance; page-marker fixtures alone do not cover either.
- [ ] Close broader table/footnote and orientation-detection gaps with selected-engine evidence or explicit limitations.
- [ ] Verify cancellation before startup, during model loading, during OCR, and immediately before artifact commit.
- [ ] Add base M-series measurements, independent cold/warm repetitions, and staging/preflight/commit timing.
- [ ] E2: measure startup, initial catalog grace, eventual discovery, absolute/inactivity tool budgets, and progress behavior for the actual setup route.
- [ ] Include full frozen inventory verification on parent startup and worker spawn; derive separate startup and import margins.
- [ ] Select page cap, deadline, sampled RSS ceiling, idle policy, and trial timeout using the engine design's p95 margin rule.
- [ ] Stop release when useful imports cannot fit; do not introduce asynchronous jobs or an unapproved fallback profile.

The developer harness's 300-second/4-GiB limits are diagnostic safeguards, not release defaults.
The release cap bounds native large-document checks. Register their source bytes and density separately without rewriting the frozen citation corpus.
Packaging must preserve complete engine identity, including installed dependency metadata, source files, OCR configuration, and native versions.

## P0. Bounded unsigned frozen-build feasibility

Implemented as a development-only [isolated builder and smoke](../runtime/p0/README.md), separate from historical client packaging.
The local check covers frozen native/OCR import, a distinct warm conversion, exact physical-page evidence and restart reuse.
Relocation and missing/changed identity-input checks supply development-machine evidence; native setup, signing and supported performance remain unverified.
This result allows the corresponding owner-authorized N2 checks after E1 or E5, without claiming those checks have passed.
P1 waits on its resource, native, licensing and signing requirements. It does not wait on M0 or token measurements.

## M0, M1 and M2. Retired API studies

The nine-trial probe, provider driver expansion and scored API study are superseded by the owner's Desktop-only decision.
Do not finalize, execute or revive them, even when historical files contain account or budget approval fields.
Keep unrun drafts with a supersession record outside Git. Preserve offline accounting and report readers for historical records.
No provider execution SDK or API-key study path belongs in the active implementation.

## D1. Desktop document-access and optional usage evidence

Acceptance: AC-15 through AC-18 and EVAL-2. Owners: native walkthroughs, citation checks, and private evidence.

1. Add negative tests proving old execution/finalization entry points refuse before credentials, processes or writes.
2. Complete N2 on each supported Desktop mode using the owner's existing app account.
3. Register a separate large synthetic document, realistic text density, source hashes, resource bounds, question and rubric; preserve the frozen citation corpus.
4. Observe the app's ordinary upload and document workflow on those exact bytes without constraining its tools.
5. Test OpenReading on the same bytes; record retrieval calls, exact citations, missing evidence, timings and resource use.
6. Claim access beyond an app limit only when its actual failure and OpenReading's successful sourced answer are both recorded.
7. Inspect whether that Desktop app exposes complete usage. If not, report token savings as unmeasured without blocking packaging.
8. Any future token comparison requires a separate Desktop-specific counter and quality protocol; provider API adapters are not a fallback.

Keep application/version/mode, source size, physical pages, extracted characters, failures, and capture completeness in every record.
A sparse 80-page fixture does not establish performance on a dense 80-page document or a thousand-page input.
No quota, billing, context-window or total-token claim follows from smaller returned tool payloads.

## P1. Later signed distribution

Prerequisites: C1 release profile and reviewed native connection routes. No API study or token measurement is required.
Acceptance: AC-1, AC-13, AC-19.
Owners: runtime lock, build/verifier, package metadata, notices, packaging tests, and client guides.

- [ ] Pin the passing core and complete runtime; reject prohibited packages and verify model, metadata, source, and tessdata inventory.
- [ ] Inventory every collected dependency and applicable notice, rather than presenting the build-environment superset as an exact distribution audit.
- [ ] Sign nested native components, the helper app and argument-free launcher, record minimal entitlements, notarize, and then hash the final installed representation.
- [ ] Exercise the signed app/installer fallback if MCPB extraction or notarization layout fails.
- [ ] Record archive/installed size, extraction, full integrity-check cost, and online/offline first-launch behavior.

Missing signing credentials block distribution, not offline implementation.
No unsigned fallback or instructions to bypass OS protections are permitted.

## H1. Clean-host release and pilot

Prerequisites: signed candidate and owner-authorized host/pilot work.
Acceptance: AC-1, AC-2, AC-11 through AC-14, AC-19, AC-20, AC-24, conditional AC-26, and pilot metrics.

- [ ] Use a snapshotted clean Apple Silicon VM with image identity and no user-installed interpreter or developer-tool dependency.
- [ ] Verify Claude Desktop independently, then only the ChatGPT modes E1 established; record executable resolution, local execution, and checked citations.
- [ ] Mark AC-26 unmet if no qualifying Chat conversation exists; never claim full target completion from a Claude-only release.
- [ ] Verify Claude Code and Codex separately before labeling their Docling distributions supported.
- [ ] Test setup cancellation, root changes, permissions, process cleanup, update, removal, retained-data cleanup, spaces, and Unicode.
- [ ] Record actual host logs and recovery steps; do not infer which process needs OS permissions without observing it.
- [ ] Review evidence and any public claims before the five-participant pilot or distribution.
- [ ] Move implemented facts beside code and delete completed proposal sections without deleting unmet requirements.

No release or merge occurs automatically when tests pass.
