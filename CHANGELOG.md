# Changelog

## Server-only connector candidate

- Install the Claude Code candidate through a GitHub marketplace and a pinned complete plugin archive, without manual copying or state resets.

- Add a Claude Code local marketplace using the verified server-only worker and isolated Claude Code settings.
- Replace the Claude Code installation guide and preserve the old assembler inputs under historical/.

- Package the native-tested Settings activation instructions in alpha.17 for clean installation.

- Explicitly activate Claude's connected computer when the Settings command cannot yet see its local opener.

- Discover local plugin tools through Claude's connected device before reporting unavailable settings or selection.
- Report session discovery failures without falsely claiming the installed package lacks a connector.
- Remove the nested Python standard-library ZIP that caused Claude to reject alpha.14 uploads.
- Reject nested ZIP contents during packaging before producing an upload candidate.
- Package a parser-free Claude connector directly, with no Docling, OCR binaries, model assets or runtime download.
- Require an explicit Core server URL while preserving native settings, file selection, job control, retained results and exports.
- Preserve existing server credentials and storage; old local-mode preferences request server setup.
- Keep Advanced download limits separate from destination approval identity.
- Reduce current client acceptance to four server-backed surfaces.

## Native settings integration candidate

- Replace vague Settings reconnect instructions with quit, reopen, and open the OpenReading file picker steps.
- Show the saved storage choice with active, pending or blocked migration status in Settings.
- Ignore abandoned legacy launch records after checking live workers, while preserving active-session and unfinished-job migration guards.
- Queue selected files, offer Process or Add more, and wait for the user's processing instruction.
- Label native server selection approval Add files and report selection errors without guessing connection state.

- Refuse new selections and imports through a stale Claude plugin connection after saving a processing destination.
- Keep existing jobs and retained-result access available while the document connector awaits reconnect.

- Fix the native server-mode picker failing before display when an absent file-type filter was bridged as NSNull.

- Continue from document or folder selection into processing every selected file without an extra conversational confirmation.
- Keep explicit selection-only tests, native server consent, cancellation and per-file progress in the workflow.

- Accept both verified processing-mode catalogs and expose the active mode's descriptions and upload annotations to Claude.

- Add a small native Claude plugin that downloads its verified runtime automatically through the development ngrok route.
- Preserve settings and documents during setup, share concurrent downloads, and answer tool discovery while installation proceeds.

- Add a complete offline Claude setup package with an Application Support runtime cache and reversible fresh-state backups.

- Color server connection results and disable server checks while bundled processing is selected.

- Organize Settings into Processing, Storage and Advanced with independent saves and Restore defaults.
- Move response limits into Advanced, default server downloads to 256 MiB, and remove Managed from Settings.

- Add `/openreading-settings` with native storage, delivery, processing and credential controls.
- Default public data and exports to client partitions beneath `~/.openreading`.
- Copy and rebind retained evidence at reconnect while preserving the original store and refusing active imports.
- Keep Settings available independently of document startup and preserve the pinned Core tool catalog.
- Track exact-build host, accessibility and distribution acceptance separately under ProductSpec revision 20.

- Harden optional server progress, Unicode consent rows, cached responses and stopped-selection recovery.
- Expose the response download budget and clarify retained-token and storage behavior.

## Optional server transport foundation

- Include a client-bound Settings app in the Claude chat candidate as well as ChatGPT.

- Preserve literal URL and filename text in the native upload confirmation.

- Add a source HTTP client for one selected snapshot and an explicitly configured Core destination.
- Reject unsafe URLs, redirects, oversized responses, duplicate JSON keys, and nonfinite values.
- Stop local waiting on cancellation without claiming remote cancellation or retrying submitted work.
- Add revisioned destination settings and a Keychain wrapper tested without real credentials.
- Add a native Settings window and bounded document-free connection checks, covered by offline tests.
- Wire the chat launcher to explicit settings and package a relocatable ChatGPT Settings app.
- Confirm destination and selected byte counts before upload, and refuse stale or modified selections.
- Serialize detached imports, stop batches after shared failures, and recover completed downloads without another upload.
- Keep frozen/native feature acceptance separate under ProductSpec revision 18.

## Development Core integration pin

- Pin the Docling candidate and P0 runtime to development Core `e53e6a1`.
  This includes external response retention and trusted detached-job execution.
  The legacy v1 runtime retains its historical pin. This is a development pin, not a released package.

## Unreleased ChatGPT development plugin

- Replace the unexpanded plugin command placeholder with an explicit working directory and relative executable path.
  ChatGPT 26.911.61220's bundled CLI resolved the configuration; a separate network-denied MCP process passed.
  Independent capture of native GUI startup after reinstall remains pending.

- Assemble a local plugin marketplace around the verified Docling worker and shared evidence workflow.
- Resolve the executable relative to the installed plugin, preserving existing data without editing host settings.
- Keep native plugin installation, ordinary Chat, signing and clean-machine acceptance pending.

## Unreleased adapter-driven formats

- Use the configured core adapter's extensions for chat selection and recursive snapshots.
- Preserve explicitly selected hidden files while continuing to skip hidden descendants.
- Require the pageless evidence contracts and cite artifact identifiers with evidence identifiers.
- Keep the existing local OCR and raster table settings; provider-reported model-free cells remain available.

- Add a native multi-file/folder chooser with private snapshot copies, disclosed skips and paginated core receipts.
  Each PDF retains its own import job and citations. Native and clean-machine acceptance remain pending.

## Native evidence review

- Pin observed page-assembly progress in background import status, without estimated percentages or extraction changes.
  Preserve status access for older jobs; page assembly does not imply completed document publication.

- Require complete-delivery v0.3 metadata for measured page origins, empty-text pages and explicit warning-record counts.
  Denied process cleanup reports a permission error; inaccessible abandoned exports do not prevent new exports.

- Pin precise provenance warnings and crash-safe export cleanup. Active writes and completed exports remain intact.
  Search and exact reads retain document-level warning flags.
  Parser cleanup preserves failure and cancellation when macOS process-group signaling races leader exit.

- Pin the literal Docling list-provenance repair and reviewed complete-export fixes.
  Existing artifacts require reimport to recover omitted list text. The bundled OCR engine remains unchanged.

- Expose the supported minimum for the advanced response budget and strengthen complete-delivery packaging guards.
- Add native export permission and approval checks, with local export retention and indexing disclosure.

- Add complete-result delivery configuration and Downloads/OpenReading exports without adding processing cutoffs or an execution environment.
- Update public-v1 acceptance for native file access, parser quality, folder snapshots and explicit analytics.

- Pin core `4f4351a` and require grant-scoped import-job discovery in the manifest and package.
  Earlier eight-tool runtimes are refused before package output is written.
- Require exact parser-crash error checks and large-artifact retrieval memory measurements.
  Document detached-job uninstall behavior and unreachable-chooser recovery.

- Package background import dispatch and all core job tools. Remove the prototype input, page, extraction, storage and elapsed-time ceilings while retaining selected-file access. Remove the local memory cutoff and chooser-copy deadline; explicit cancellation and actual OS failures still apply.

- Update the Docling candidate to core `25c15c4` and expose complete normalized document retrieval.
  Search is optional; full results keep existing structure, warnings, origins and citation references.
  Reject older runtimes before packaging a manifest that advertises the new tool.

- Present the chat chooser without attaching a macOS sheet to its hidden Tk owner.

- Keep selection and clearing usable when rollback revokes entries during directory scans.
  Quota accounting counts moved files once and still refuses corruption on remaining entries.

- Revoke failed selections without waiting for the publisher lock; preserve original errors when cleanup fails.
- Suppress ONNX Runtime telemetry at process startup and check fresh-home persistence in the frozen smoke.
- Exercise provider forwarding, nonzero chooser exits and real versioned configuration files in regression tests.

- Add a separate chat chooser candidate with automatic local OCR and no directory or OCR configuration.
- Add transactional chooser cancellation and a four-tool catalog at the refreshed core pin.

- Distinguish compact transport results from errors in timing format 3, without inspecting tool payloads.
- Record validated probe intervals and progress-token presence for reproducible native progress checks.
- Document continuing imports after an undelivered host Stop and separate observed Claude budgets from other host hypotheses.

## Probe correlation

- Add UTC timestamps and transport receipt events to the synthetic host probe for native delayed-approval checks.

## Timing and selection review

- Mark timing segments as inferred log boundaries, count unpaired requests in both directions, and suppress ambiguous restart timings.
- Restrict the proposed picker to fixed, argument-free UI and a busy response; require host deadline evidence before interaction acceptance.
- Align the ChatGPT proposal with automatic OCR and chat-driven selection, and specify the trusted core provider seam and catalog comparison.

## Proposed public document experience

- Revise the production contract to chat-driven local selection without reference copying and automatic local OCR.
- Preserve development picker controls and runtime identities; native handoff and automatic-profile acceptance remain open.

## Local timing diagnostics

- Add a read-only Claude Desktop log diagnostic that separates tool-call intervals from gaps without exporting document payloads.
- Refuse ambiguous request pairing and preserve unknown parser, document and answer timings.

## Coverage requirements

- Separate historical Desktop package instructions from the Docling candidate guide.
- Refuse incomplete catalog references before launching smoke workers and sanitize input failures.
- Explain OCR transcription limits and correct current candidate pin references without relabeling older evidence.
- Revise public setup acceptance to require local file selection without directory configuration; implementation remains gated by A0.

- Accept the reviewed core search/origin fixes through the pinned Docling candidate.
- Verify trial artifact identity, preserve per-model usage, and expose size, adherence, and stop diagnostics.
- Stop on unpriced models or observed budget overruns; salt per-study account fingerprints.
- Include all Python proof scripts in the 95% coverage gate and fingerprint complete installation directories.

- Enforce 95% Python line and branch coverage and 95% Node line, branch, and function coverage.
- Exercise runner authorization, runtime integrity, trial failures, and resumable budgets with offline fixtures.

## Reviewed Docling candidate

- Pin core `f241c28` and reject missing active dependencies or inaccessible memory samples.

## Unreleased

- Keep the selected-file connector available while the picker copies a document.
- Reclaim abandoned intake staging under the publisher lock and add confirmed cleanup of copies from earlier sessions.
- Explain symlink refusals and shared artifact retention without changing the pinned core catalog.

- Add a separate local file-picker candidate with a private, bounded intake and copyable chat references.
- Bundle picker resources and remove directory configuration from that candidate while preserving existing developer and historical launchers.
- Test selection failure, cancellation, source changes, publication, retention and official MCPB argument resolution.
- Keep public installation and accessibility acceptance separate from the demonstrated native picker and local MCP handoff.

- Record partial Claude Desktop installation, native-text and OCR observations, with fresh-chat guidance after settings changes.

- Add a distinct Docling Desktop development candidate with an explicit directory and default-off OCR form.
- Refresh the core pin for current evidence instructions and check packed tool/instruction parity against a same-profile core reference.
- Preserve historical client packages; native installation acceptance and signed distribution remain pending.

- Clarify revision 7 release dependencies, focused profile-aware MCP checks, independent core setup, and separate non-developer pilot evidence.

- Define ProductSpec revision 6: OSS launch v1 before managed v2, full pinned-core MCP catalog parity, and a static Coming soon visual only.
- Keep the slim Docling bundle and independent full-core setup route; build no managed endpoint, stub, auth, upload or billing components.
- Preserve internal profile/settings versions and runtime pins; new release parity and presentation checks remain proposed.

- Adopt ProductSpec revision 5: Desktop-only proof, no provider API trials or token-study packaging gate.
- Remove the provider execution SDK and refuse historical execution, preparation and finalization entry points.
- Preserve offline accounting and report readers, with superseded unrun drafts kept outside Git.
- Test citation format boundaries independently, require unknown-origin labels, and balance source-header parentheses.

- Accept explicit review v2 source headers and citation lists without weakening historical v1 placement checks.
- Clarify returned-ID retrieval, block offsets and generic warnings in the shared assistant workflow.
- Record partial owner-run Claude Desktop evidence separately from complete native acceptance.

- Reject trivial quote selections and citation labels borrowed from later or unrelated answer text.
- Distinguish unedited citation CLI output from annotated development records.

- Refresh candidate and P0 locks to core `7d97b75`, preserving historical revision 1 pins.
- Reimport integration v5 evidence and verify frozen OCR, relocation, restart and identity refusal.
- Add protocol-based citation review with exact answer spans, capture hashes and negative provenance tests.

- Implement version 2 grants, closed OCR settings and private Docling launch profiles with v1 coexistence.
- Add an isolated, unsigned P0 freezer preserving candidate pins, complete identity inputs and relocated Tesseract libraries.
- Discover Docling plugin entry points during freezing; refuse diagnostic bundles in historical client packages.
- Add frozen native/OCR/restart checks, reproducible E0 tool-schema checks and a synthetic host probe server.
- Register the exact document-instruction case and clarify helper, timing and citation-checker handoffs.
- Keep native installation, helper signing, supported page limits and paid studies pending.

- Revise the assistant proposal to revision 4 after design review, with mode-specific ChatGPT acceptance and a concrete helper-app setup candidate.
- Correct frozen-task references and specify versioned settings, citation capture/checking, startup budgets, a bounded frozen-build spike, and isolated Codex trials.
- Preserve executable behavior, corpus hashes, historical locks, and existing probe manifests.

- Propose ProductSpec revision 3 for Claude Desktop and ChatGPT desktop with one local Docling runtime.
- Define shared setup, client compatibility checks, provider-specific measurement, and explicit CLI/server preservation gates.
- Preserve historical binaries, locks, and probe contracts; native client execution and additional measurement drivers remain unbuilt.

- Add the frozen Docling corpus, exact-citation retrieval gate, and MCP restart check.
- Pin the candidate to core v0.3 provenance and versioned dehyphenated retrieval.
- Add an unscored nine-trial Docling probe with frozen source identity, usable baseline recipes, and explicit account approval.
- Let the ordinary-tools arm save extracted text for Grep and ranged Read instead of only ingesting whole documents.
- Report probe directions only for human-approved answers, and charge budget at the larger of SDK and frozen-price estimates.
- Bind restart evidence to its retrieval report, verify resumed trial usage against raw events, and accept exact current model identifiers.

## Docling feasibility

- Add an isolated, immutable core/dependency candidate for revision 2 feasibility.
- Add a network-denied engine matrix with synthetic inputs and explicit failure checks.
- Require per-page markers, no unexpected projection warnings, locked installed identity, and an observed network-denial canary in each matrix cell.
- Audit the candidate lock in `make audit`.
- Preserve revision 1 runtime and study pins until their separate migrations pass.

## [Unreleased]

- Refresh core with delivered retrieval-scope instructions and register a focused-question native check.

- Pack complete-document replies by bytes through the refreshed core pin. Match retrieval scope to the request and require a separate native continuation check.

### Changed

- ProductSpec revision 2 replaces the proposed distributed PyMuPDF profile with Docling, ONNX layout, PDFium, and setup-only Tesseract.
- The revised design adds measured timing and memory gates, a signing fallback, explicit coding-client grants, offline retrieval checks, and an M0 probe before further packaging.
- Existing executable behavior remains the revision 1 prototype; no Docling migration, installation, or paid experiment runs in this design pass.

### Fixed

- Measurement permissions distinguish search text from filename filters and reject outside symlink targets.
- Baseline extraction recipes reach every arm, with frozen utility verification and pre-query extraction checks.
- Constrained baselines cannot support savings claims or C/A ratios; unrun rows retain known document categories.
- Runtime startup rejects unsupported hosts and source execution; notices retain the full build-environment inventory.

### Added

- Repository instructions, contribution and security policies, GitHub templates, and offline documentation checks.
- A ProductSpec, engineering design, token experiment design, and implementation plan for a local document proof.

- A frozen macOS arm64 runtime consuming an immutable core revision, with complete file integrity checks and dependency notices.
- Claude Desktop MCPB, Claude Code, and Codex package assembly with explicit directory grants and a shared retrieval skill.
- Synthetic token experiments, frozen manifests, resumable budget accounting, and offline report regeneration.
- Offline runtime and measurement tests with enforced coverage floors.

No public binary or token reduction result is released.
