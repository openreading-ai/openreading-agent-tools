# Revision 9 implementation plan

**Status:** shared configuration, P0 diagnostic freezing, E0 and synthetic probe tooling are implemented. Native client adapters, release packaging and Desktop proof remain proposed.
**Contracts:** [ProductSpec revision 9](../product/specs/local-document-proof.product-spec.md), [assistant integration](assistant-clients.md), [engine design](local-document-proof.md), and [evaluation design](token-evaluation.md).

Continue on the existing feature branches and preserve unrelated work.
Never merge either repository's PR automatically.
Each implementation commit names the acceptance criteria it addresses and leaves unmet host checks explicit.
A passing offline gate is necessary but cannot replace native application or signing evidence.

ProductSpec revision 7 resolves mode-specific acceptance, setup, configuration coexistence, host budgets, citation checks, and study prerequisites.
Revision 8 adds A0 for public file selection without directory configuration. The current form remains developer evidence.
Revision 9 requires chat-driven selection without reference copying and automatic local OCR. A1 below owns these unbuilt production changes.
Revision 5 prohibited provider API trials and removed their release prerequisites.
Revision 6 defines public OSS product v1, full pinned-core MCP parity, and a static Coming soon visual; managed product v2 follows launch.
It preserves `local-document-proof-v2`, historical locks, native acceptance, and owner-operated Desktop testing.
Revision 1 binaries and revision 2 probe manifests retain their original meanings.
This documentation pass adjudicates the review and defines E0 through E6 in the [probe plan](native-probes.md).
The implementation adds developer protocol and frozen-runtime checks. Native host installation, client registration and model invocation remain separate gates.
N1, bounded P0 build work, and independently authorized native probes can begin without waiting on ChatGPT support.
P0 assembles the diagnostic candidate alongside N1 and consumes its frozen-launch changes before N2.
Then use measured C1 limits for release, perform Claude N2 first, and admit ChatGPT N2 only after E1.
M0/M1/M2 are retired. P1 precedes clean-host H1 without an API-study dependency.

## Release dependency order

This is a dependency order, not a claim about which unfinished task will take longest.
Akshay owns core merge and release approval. Maintainers prepare the release and pin change; agents never merge.

~~~text
Core PR review -> owner merge -> core release -> R0 immutable release pin
N1 + P0 + E5 -> developer Claude Desktop N2
A1 production handoff + automatic OCR + developer N2 -> public Claude Desktop N2
N1 + P0 + E1 + A1 production handoff -> named ChatGPT N2 (conditional)
R0 + C1 resource limits + N2 supported route + license/signing readiness -> P1
P1 + C0 final package check + N3 presentation + R1 guide -> H1 clean-host checks
H1 + owner approval -> packaged OSS launch
H1 + L1 recruited/consenting cohort -> observed pilot -> follow-up review
~~~

Continue N2, C1, licensing preparation, R1 and pilot planning against the immutable development candidate while core review/release proceeds.
Do not wait for a core release to learn whether the host setup works. Rebuild and repeat affected evidence after the released pin is selected.
C0 travels with pin updates and packaging; reuse E0/P0/N2 instead of blocking N2 behind a new broad harness.
Source publication and supported binary distribution have separate readiness decisions; never distribute an unsigned development bundle as the supported release.

## R0. Released core dependency

Owner: core maintainer prepares; Akshay approves merge/release; Agent Tools maintainer updates pins.
Acceptance: AC-13 and AC-27.

- [ ] Complete review of the core MCP work, then obtain owner merge and a core release containing it.
- [ ] Record release version/tag, immutable commit, default-branch ancestry and the corresponding published source/distribution identity.
- [ ] Update the candidate and P0 locks to that released commit; retain earlier branch hashes as development evidence.
- [ ] Rebuild and rerun affected integrity, profile, extraction, instruction and C0 checks. Do not relabel old artifacts as release evidence.

## Release risks and stop conditions

| Risk | Owner and decision |
| --- | --- |
| Frozen size, startup, memory or useful document limits miss C1's measured envelope | Packaging/core maintainers investigate within the approved slim profile. Stop binary release if useful imports cannot fit; an owner-approved scope change is required for another engine or job model. P0 already freezes successfully, so do not restart basic feasibility on speculation. |
| Signing/notarization or archive extraction fails | Release maintainer uses the already planned signed app/installer fallback and repeats native/clean-host checks. If neither supported route passes, stop binary distribution; do not recommend bypassing OS protections. |
| A host changes its extension format or cannot deliver local tools/instructions | Client maintainer revalidates a documented route on the named version. Stop support claims for that route if it fails; do not substitute a coding mode for Chat or build an unapproved bridge. Independently passing hosts may ship. |

A delayed core release blocks final release pinning, not development checks. Release timing follows these dependencies rather than an invented date.

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
- [x] Preserve the selected engine, core surface boundaries, historical execution contracts, and the independent full-core route for other backends.
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

## C0. Complete pinned-core MCP catalog

Acceptance: AC-27 and AC-29. Owners: core owns tool implementation; Agent Tools owns wrapper parity.
Contract: [OSS launch design](oss-launch.md). This is proposed release verification, not an already completed gate.

- [ ] On every core pin update, obtain the direct-core catalog and initialization instructions under the same effective Docling profile as the frozen runtime.
- [ ] Extend E0/P0 to compare names, schemas, annotations and profile-expected descriptions/instructions, including OCR off and on.
- [ ] Check the Claude Desktop manifest's repeated tool names and semantic setup claims; reuse N2 for actual host discovery and invocation.
- [ ] Reuse existing valid/refusal cases for import/search/read; add cases only for uncovered behavior or new tools.
- [ ] Add focused regressions for omitted tools, changed schemas, wrong profile prose and missing instructions.
- [ ] Check the final package after R0/P1. A pin-update check is necessary for the first release too; it is not a separate prerequisite for beginning N2.

The current core catalog is import, search and read. There is no duplicate engine contract to implement in wrappers.
The [launch design](oss-launch.md) defines strict fields and permitted profile/presentation differences.

## N1. Common configuration and launcher migration

Implemented before ProductSpec revision 7. Its durable behavior and remaining native checks live in the [runtime guide](../runtime/README.md).
Tests cover closed settings, exact OCR tokens, atomic replacement, grant refusal, direct-versus-saved precedence and v1/v2 coexistence.
Independent profile lifetimes, catchable-exit cleanup and verified resource paths are exercised offline.
SIGKILL cannot run process cleanup; stale-directory recovery remains separate work, not a proven lifecycle guarantee.
The diagnostic launcher does not complete host-dependent AC-2, AC-13 or AC-23 by itself.
C1 still owns supported limits, and N2 still owns actual form substitution and client installation.

## A0. Public local file selection

Acceptance: AC-1, AC-2, AC-3, AC-14 and AC-25. Owner: Agent Tools maintainer; Akshay reviews the selected experience.
Contract: public file selection in [the assistant design](assistant-clients.md#public-file-selection-proposed-a0-contract).
This is required before public setup implementation and acceptance, while existing developer protocol checks may continue.

- [x] Observe a host-local file handoff or prototype the helper picker and copyable reference using synthetic files, without provider API calls.
- [x] Freeze the reference format, private intake publication, byte limits, source identity handoff, retention and removal rules before implementation.
- [ ] Confirm no installation step requests a directory, broad filesystem grant or path configuration; never infer local attachment access from a chat upload button.
- [x] Implement the selected thin helper/handoff under the existing coverage gate, preserving core parsing and evidence ownership.
- [x] Test cancelled/invalid selection, unselected paths, traversal, symlinks, duplicate names, source mutation, disk failure, size caps, restart and catchable-failure cleanup.
- [x] Test startup during copying, quota recovery across sessions, and staging recovery after killing a publisher process.
- [x] Inventory helper sources and GUI resources; bind the wrapper and plist in package metadata.
- [ ] Resolve native accessibility and pointer interaction before accepting the non-developer walkthrough.
- [ ] Integrate and sign the helper alongside the runtime, then repeat native and clean-machine walkthroughs using the public selection route.

The [implemented selection guide](../clients/claude-desktop/selection/README.md) owns the development behavior and tests.
Native picker plus direct MCP evidence does not mark the public setup or assistant-conversation checks complete.

If neither local route works in the named host, stop that host's public launch. Directory setup does not satisfy AC-2.
The existing developer form is retained for diagnostics; no candidate or historical native record is retroactively marked compliant.

## A1. Production handoff and automatic OCR

Acceptance: AC-2, AC-3, AC-4, AC-21 and AC-25. Contract: [public document experience](public-document-experience.md).
Owner: Agent Tools maintainer owns the picker and package; core maintainer owns any new MCP selection contract.

- [ ] Run E2 for the named host before accepting a picker-inside-call interaction; measure absolute/inactivity deadlines, progress and delayed approval.
- [ ] Use the documented local tool route to prepare a selection probe. Prove native dialog focus, cancel, timeout and automatic reference return on the named host before choosing final UI.
- [ ] Prefer an OpenReading action within chat. Ordinary host drag/drop requires separate evidence that bytes reach local OpenReading before host upload; never infer interception from a file picker or plugin file API.
- [ ] Review and implement any selection tool/provider interface in core first, preserving headless CLI/HTTP behavior and default dependencies. Agent Tools supplies only the trusted local selection provider.
- [ ] Keep the existing private intake, byte cap, publication, removal and source-retention contracts. Return selected references through the tool response without clipboard or model-supplied source paths.
- [ ] Build a distinct public launcher/profile using selective local OCR automatically. Preserve existing developer settings and artifacts, and retain diagnostic off/on controls outside public setup.
- [ ] Verify native-only, image-only, mixed-page, blank, damaged-text-layer and rotated text cases. Retained text, origin labels, missing-text warnings and converter reuse must match observed output.
- [ ] Repeat C1 resource measurements with automatic OCR before selecting public limits. If the existing selective pipeline misses needed text, fix core or disclose the limitation; do not add an undocumented retry engine.
- [ ] Rebuild after the supported core pin change and repeat catalog, integrity, retrieval/restart and native citation checks. A0's POC or a source probe cannot satisfy A1.

The local timing diagnostic is implemented in [measurement](../measurement/README.md#desktop-timing-diagnostic).
It helps inspect existing logs but cannot isolate engine stages or establish native deadlines.
Exact startup/model-load/extraction/write timing remains C1 work at the responsible core/launcher boundary.

## N2. Thin host adapters and native functional checks

Developer prerequisites: N1, passing P0, and the corresponding E1/E5 native setup observation.
Public setup additionally requires A1. Start Claude Desktop first; ChatGPT waits on E1 and A1.
Acceptance: AC-1, AC-11, AC-12, AC-14, AC-24, EVAL-1.
Owners: `clients/`, `runtime/package.py`, the existing shared skill, adapter tests, and client READMEs.

1. Inspect the existing packaging implementation and keep the common runtime independent of any one host manifest format.
2. Add host-specific setup translation and workflow delivery using the shared configuration semantics.
3. After E1 and A1, implement the named argument-free ChatGPT entrypoint and reviewed native selection provider in assistant design section 7, including inventory, coverage, and native GUI checks.
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

## N3. Static Coming soon presentation

Acceptance: AC-28 and AC-29. Owners: README, existing release presentation and their review checks.
The README contains the proposed static copy; installed-host presentation and negative verification remain pending.

- [ ] Use the exact title and explanatory copy in [the launch design](oss-launch.md), with no signup, processing button or endpoint.
- [ ] Show it in the existing release description or setup/help surface supported by that host; build no new service or UI subsystem.
- [ ] Check copy and inventory for no managed URL, server registration, credentials, upload path, billing dependency, polling or dormant tools.
- [ ] Verify presentation does not initiate network activity or change the local catalog, errors or evidence payloads.
- [ ] Confirm local use works offline after installation and requires no company account.

Do not put commercial text in model-facing evidence, tool results, or system instructions to force a chat upsell.

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

## R1. Independent full-core connection guide

Owner: Agent Tools maintainer owns [the connection guide](../clients/full-core/README.md); core maintainer reviews its profile contract.
Acceptance: AC-20 and AC-29. This is a separate power-user installation, not a backend menu in the bundled product.

- [ ] After R0, replace the candidate reference with the released version and verify the documented clean-environment install.
- [ ] Exercise both explicit profiles, including the Docling profile JSON, local assets, dependency lock and optional Tesseract data.
- [ ] Register the standalone executable through one verified assistant route without changing unrelated registrations; capture tool discovery and a cited read.
- [ ] Confirm the guide distinguishes full core's CLI/Python/HTTP backends from its presently limited MCP profiles. Installing all extras does not expand MCP automatically.
- [ ] Publish the independently verified guide with the install/limits material before the packaged OSS launch.

## L1. Pilot recruitment and observation

Owner: Akshay recruits and obtains consent. The release maintainer prepares the install task, observation sheet and follow-up instructions.
Do not send invitations or collect participant data without the owner's authorization.

- [ ] Prepare invitation text for existing personal/community relationships and voluntary referrals outside engineering. Use existing communication channels, not a product waitlist or telemetry.
- [ ] Recruit five non-developers who do not routinely set up Python/development tools, plus five developers for diagnostic comparison. Agree a schedule and record consent privately.
- [ ] Use H1's clean-machine result to establish runtime independence; record each pilot machine's preexisting tools and assistance separately.
- [ ] Target 4/5 non-developers and 8/10 overall completing the cited-answer task within 15 minutes without installation help.
- [ ] Target 3/5 non-developers returning within seven days, and 5/10 overall within fourteen days. Check all ten understand excerpt disclosure.
- [ ] Report both cohorts, every failure and assistance received. Missing recruits are missing evidence, not successes or developer replacements.

Confirm these proposed targets before recruitment. Failure of the non-developer cohort blocks the non-developer onboarding claim even if the pooled result passes.
Pilot observations follow signed clean-host readiness; an unfilled roster does not prevent offline implementation.

## P1. Later signed distribution

Prerequisites: R0 released-core pin, C1 release profile and reviewed native connection routes. No API study or token measurement is required.
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
Acceptance: AC-1, AC-2, AC-11 through AC-14, AC-19, AC-20, AC-24, conditional AC-26, AC-27 through AC-29, and pilot metrics.

- [ ] Use a snapshotted clean Apple Silicon VM with image identity and no user-installed interpreter or developer-tool dependency.
- [ ] Verify Claude Desktop independently, then only the ChatGPT modes E1 established; record executable resolution, local execution, and checked citations.
- [ ] Mark AC-26 unmet if no qualifying Chat conversation exists; never claim full target completion from a Claude-only release.
- [ ] Verify Claude Code and Codex separately before labeling their Docling distributions supported.
- [ ] Test setup cancellation, root changes, permissions, process cleanup, update, removal, retained-data cleanup, spaces, and Unicode.
- [ ] Record actual host logs and recovery steps; do not infer which process needs OS permissions without observing it.
- [ ] Review evidence and any public claims before the ten-participant, separately reported pilot cohorts or distribution.
- [ ] Move implemented facts beside code and delete completed proposal sections without deleting unmet requirements.

No release or merge occurs automatically when tests pass.
