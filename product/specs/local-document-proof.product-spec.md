---
spec_format_version: "0.1"
title: "Local document proof for AI assistants"
artifact_type: "prd"
spec_revision: 28
author: "Akshay"
created_at: "2026-09-10T00:00:00Z"
updated_at: "2026-09-22T00:00:00Z"
linked_github_repo: "openreading-ai/openreading-agent-tools"
applies_to:
  - path: "runtime/"
  - path: "clients/"
  - path: "skills/"
  - path: "measurement/"
  - path: "tests/"
  - component: "openreading-core-local-document-mcp"
---

## Problem

People already using an AI assistant want answers from local documents without becoming Python operators.
A developer can install OpenReading and run a parser today.
The assistant user installs a connector without an interpreter or parser dependencies. An operator supplies a running OpenReading Core server.

Sending the whole parsed document into the assistant can still consume substantial model context.
Parsing locally changes where extraction happens.
It does not automatically reduce the tokens used to complete the task.

Readers also need to check answers against the source.
A convincing answer without a resolvable document and page reference cannot support that review.
For example, an answer about a renewal period should identify the paragraph and physical PDF page containing that period.

The first platform remains macOS on Apple Silicon.
Revision 28 requires the [four-cell compatibility matrix](../../README.md#required-compatibility-matrix).
Claude Cowork and ChatGPT Work are the desktop targets; local Claude Code and Codex are the code targets.
Each surface connects to a required operator-run Core server. No parser or model is bundled with the connector.
Ordinary Chat and cloud code sessions do not satisfy these targets. No other client is claimed.
A supported client means one recorded application version, execution mode, and connection path that passes the functional checks.
Support for one desktop mode does not establish support for its web, mobile, or remotely executed modes.

## Hypothesis

If installation includes the required local runtime, a user can reach a cited answer without managing a Python environment.
If the assistant retrieves only relevant evidence from a retained local extraction, it can answer some questions with fewer total input tokens.

Both hypotheses are falsifiable.
A clean-machine installation can fail even when a developer-machine demo works.
Selective retrieval can increase token usage or miss evidence when a normal assistant already searches efficiently.

This proof measures Desktop installation, document access, answer correctness, citation accuracy, and elapsed time separately.
Token reduction remains untested, not falsified. It is not a release prerequisite.
Only complete, verified usage exposed by the actual Desktop app could support a future token claim.
No provider API integration or API trials are permitted, even with a key, budget, or prior approval.
Owner-operated testing through existing Desktop subscriptions remains in scope.
It does not infer one outcome from another.

## Product Summary

You install an OpenReading bundle without configuring a directory or typing a filesystem path.
You explicitly select files or a folder snapshot through a local file-selection interface.
Owner-operated candidate checks cover folder selection and multiple imports in the [client matrix](../../clients/README.md#owner-operated-candidate-checks-september-16-2026).
The repeated native folder check matches expected aggregate skip counts; the earlier discrepancy remains unexplained.
Signed clean-machine installation and lifecycle acceptance remain pending.
Each client connects to the same runtime through its tested local MCP interface.
Setup requires an explicit server URL and discloses local retention and uploads. The server owns parser and OCR configuration.
A host-supported handoff or bundled picker supplies only your selected document to the local runtime.
You ask to open a local document, select it, and receive its reference in chat without copying a path or prompt.
The configured Core server parses selected files after Process. The connector retains the extraction locally and returns a short receipt.
The assistant requests complete normalized content with automatic delivery or uses optional search and exact reads.
A 1,000,000-byte configurable budget measures the entire serialized MCP response, including escaping and request ID.
A fitting result is sent intact. The host may present it inline or save it into a file accessible through its existing tools.
A larger result is saved as complete JSON under Downloads/OpenReading, with its byte count, hash and warning summary.
The host's local-file capability or an explicit user attachment supplies access; a local path alone does not.
Manual attachment sends exported content to the assistant host. Claude Cowork is a required surface, but no host execution environment is bundled.
This delivery budget never limits document processing and never silently truncates normalized content.
Requested content enters the assistant context; full retrieval can include all retained extracted text.
Neither route changes the configured parser or infers document relationships.

A receipt is a small record identifying the extracted document and its available evidence.
Provenance is the information connecting that evidence to the exact source bytes and physical page.
Neither is an LLM-generated summary.

Revision 27 removed the distributed parsing engine. Revision 28 removes connector credential support.
The plugin embeds a small native connector, with no parser libraries, models, OCR executable or runtime download.
The operator configures the Core server's backend policy independently; Core retains its full adapter catalog.
Existing server URLs, response limits, storage choices and artifacts survive an upgrade.
The connector stores no credentials and sends no authentication. Legacy credential references are discarded on read.
Existing Keychain items are neither accessed nor deleted. Core server authentication is unchanged.
Absent or legacy local-mode settings require an explicit server save, with no silent localhost activation or parser fallback.
The previous implementation is preserved by tag `bundled-docling-2.126.0-checkpoint`.
Historical engine-specific criteria below remain records of that implementation; revision 28's server-only criteria govern current distribution.

Core owns the generic artifact and MCP behavior.
Agent Tools packages that engine, guides the client workflow, and tests installation.
The private company repository holds private evaluation documents and native Desktop observations.

**Review status: revision 28 requires four independently tested server-backed client surfaces; managed v2 is post-launch and unbuilt.**
The Docling developer harness, retrieval checks, and citation checker are implemented.
Historical API study execution and preparation are disabled; their unrun drafts remain superseded records.
Historical revision 1 PyMuPDF binaries and the newer Docling development candidate remain distinct.
The Docling directory form proves developer setup only, not the public installation experience.
Revision 3 added ChatGPT desktop, explicit client compatibility gates, and separate provider measurement contracts.
Revision 5 removes API studies and their packaging prerequisite, while retaining revision 4 host, setup, timing, and provenance requirements.
It preserves the selected `local-document-proof-v2` engine profile and does not relabel historical binaries or trials.
The existing CLI, Python API, HTTP server, and other core backends remain independent of assistant setup.
Approving this specification authorizes its scope only when the owner also requests implementation.
It does not authorize release or merging. Provider API model calls are prohibited, rather than awaiting approval.

## Release naming and MCP completeness

The first public OSS launch is product v1. Managed-service product v2 starts only after that launch.
These names do not rename historical prototype revisions, settings directories, release hashes, or `local-document-proof-v2`.
The current internal v2 profile is a local Docling profile, not a managed service.

Launch v1 supports every implemented MCP tool in its pinned core release, with no commercial tool gate.
The candidate pin `3ff02d4` includes `openreading_get_document`, introduced in `25c15c4`, alongside import, search, read, local selection and background job start/status/list/cancel.
Its core implementation passed direct stdio checks; this pin alone establishes no frozen or native-host acceptance.
Here “MCP endpoints” means tools discovered through MCP and invoked through its tool-call protocol, not new HTTP routes.
Public bundles pin a merged core release by immutable commit and record its release version; feature-branch pins remain development evidence.
The launch must verify the complete tool catalog using existing frozen/native checks and the client manifest declarations.
Compare core and frozen runtime under equivalent profiles, including model-facing descriptions and initialization instructions.
A future core pin requires a new comparison and compatibility work for added tools before release.
Core CLI or HTTP operations that are only proposed as MCP tools are not claimed as implemented.
Tool completeness does not mean every backend is installed or every operation has every optional capability.
The bundled runtime remains slim Docling only; unsupported capabilities must return core's explicit errors or warnings.
If a new core tool cannot meet its contract under that boundary, resolve the scope before updating the release pin; never silently hide it for managed v2.
Power users can separately install full core and register its MCP server through their assistant's own configuration.
Agent Tools does not manage that installation or offer alternate bundled local engines.
Revision 18 permits a separate operator-run Core HTTP destination while preserving bundled Docling as the default.

Managed processing has only a static “Coming soon” visual at launch.
No service endpoint, no-op server, authentication, upload, billing, capability polling, or inactive managed tool is included.
No future no-reinstall or automatic-compatibility promise is made.
The [OSS launch design](../../design/oss-launch.md) owns the catalog proof and presentation boundary.

## Scope

~~~productspec-scope
in:
  - Deliver signed and notarized server connector packages for macOS on Apple Silicon across Claude Cowork, ChatGPT Work, local Claude Code, and Codex; independently verify operator-run Core processing in every surface.
  - Preserve server-reported text, OCR labels, warnings, partial status and provenance without inventing local parser results.
  - Exclude table structure recognition until a separately approved compatible engine exists.
  - Require no directory-path configuration in public installation; accept explicitly selected adapter-supported local documents through a verified file picker or handoff, with one artifact per import.
  - Expose the complete implemented MCP tool catalog of the pinned core release; including import, complete normalized retrieval, search, read, local selection and background start/status/list/cancel, with bounded replies.
  - Include only a static OpenReading Managed Coming soon visual for the future product; build no managed components.
  - Preserve exact source identity, physical page numbers, and evidence identifiers through the answer workflow.
  - Refuse unreadable, unsupported, or disallowed inputs with explicit errors and no hosted fallback.
  - Package the same runtime for Claude Code and Codex, with separate installation evidence for each supported host version.
  - Test the actual Claude and ChatGPT Desktop workflows independently, including large documents, exact citations, explicit limitations, and setup.
  - Record document byte size, physical pages, extracted characters, native upload outcomes, and local resource costs without inventing token counts.
  - Publish only supported native functional results; label token savings unmeasured unless the actual Desktop app exposes complete verified counters.
out:
  - Do not invoke provider model APIs, use an agent SDK as a substitute for Desktop, buy API credits, or run separately metered trials.
  - Do not build a managed endpoint, dummy service, managed authentication or upload bridge, signup flow, billing, dormant managed tools, or company document index.
  - Do not include a local language model, Docker, Cuttlefish, PyMuPDF, torch, torchvision, or docling-ibm-models in the distributed proof.
  - Do not implement ChatGPT web, mobile, remote execution, tunneling, Windows, Linux, or Intel Mac support in this proof.
  - Do not provide an operating-system sandbox or claim that a cloud assistant sees no document information.
  - Do not change existing core CLI, Python API, HTTP behavior, backend selection, password support, or default installation dependencies for assistant integration.
  - Do not let model tool arguments choose a backend, endpoint, credential, or processing destination. Bundled local processing uses Docling.
  - Do not make an embedding service, vector database, semantic summarizer, or answer-generating model part of this runtime.
cut:
  - Support explicit files and recursive folder snapshots through one native chooser. Retain separate copied references and per-document jobs; paginate receipt entries without reopening selection. Native acceptance remains pending.
  - Cut automatic retries and a separate job-management UI; background jobs and MCP discovery remain in scope.
  - Cut a thousand-page acceptance claim until a separate resource and retrieval study passes.
  - Cut model-controlled OCR settings and silent hosted retries; automatic local OCR stays within the verified bundled pipeline and measured import limits.
  - Cut full-document summaries as a token-saving demonstration because reading every passage can erase the proposed savings.
  - Cut a document viewer and automatic opening of local files from the first proof.
  - Cut public marketplace submission and automatic updates from the first proof.
~~~

Public selection authorizes copied files from the selected snapshot, never a live directory grant.
The runtime manages its own private intake root; this internal grant is never a public directory-setting prompt.
The assistant may have separate file and shell tools whose access OpenReading cannot restrict.
The current explicit directory form remains a developer-only fixture mechanism.
An ordinary chat attachment is not assumed to reach local MCP or bypass the host upload limits.
A public route without verified local file handoff cannot pass installation acceptance.

## Optional operator-run Core destination

Revision 18 adds an optional Core HTTP destination that you configure locally.
A destination is where your selected bytes are processed. Bundled Docling remains the default.
The separate Core process runs under your control, on localhost or an explicitly configured HTTPS host.
Agent Tools never installs or manages that process. Its existing Core configuration chooses processing.
This option is distinct from the unbuilt managed product.

Before upload, selection shows the destination, file names, count, and total bytes for confirmation.
Selected bytes and filenames reach that server. Its configured backends may use other services.
Results remain in local evidence storage and enter the assistant when retrieved.
Changing the destination invalidates consent for unprocessed selections. Existing jobs retain their approved destination.
Server selection accepts regular files without claiming that every selected format is supported.
It preserves the existing folder exclusions and individual file outcomes.

The client uses the existing multipart parse API with a null backend ID.
It preserves normalized values, partial status, exact uploaded-source identity, and unmeasured provenance.
Structured-only results remain available through complete delivery, without fabricated quotes or pages.
A server failure never silently invokes Docling or another destination.
Shared connection or authorization failures stop later submissions; document rejections preserve sibling outcomes.

Parse requests are never retried automatically. Cancellation ends local waiting and future dispatch only.
Submitted server processing can continue. Interrupted work has an unknown remote outcome.
The source limit is 100 MiB in server mode; the default decoded response limit is 256 MiB.
These transport limits do not cap bundled Docling processing or change complete-result delivery budgets.
Non-loopback servers require verified HTTPS. Redirects, credential-bearing URLs, queries, and fragments are refused.
Connections use only the URL. Servers requiring client authentication are outside this connector release.

The source HTTP transport, private settings store, and native Settings window are implemented and tested offline.
Upgrade tests verify legacy destination URLs and limits survive without credential references.
The launcher, selection consent, serialized uploads, and completed-download recovery are implemented.
Offline tests exercise the actual pinned Core retention and MCP retrieval interfaces.
Frozen runtime and owner-operated native feature acceptance remain separate release gates.
The owner-operated synthetic ChatGPT probe establishes loopback connectivity only.
It does not establish the finished server destination or a frozen runtime.

## Native settings

Revision 20 adds optional native settings without making directory configuration part of installation.
Use `/openreading-settings` or ask to open OpenReading settings.
The window separates storage and delivery from document processing.
Storage changes apply at reconnect after existing imports finish. Original data copies remain intact.
Each client keeps a separate partition. Changing a data folder never grants access to source documents.
Native acceptance for the integrated package remains independent of the earlier disposable probe.

## User Experience

### First successful answer

1. You receive a versioned bundle for your tested operating system and client.
2. You install the signed runtime through the tested instructions for your named desktop client.
3. Setup discloses retained source copies, the local layout model and automatic local OCR without a directory or OCR setting.
4. Setup explains that passages returned to your assistant may enter its cloud context.
5. You ask OpenReading to open a document, choose agreement.pdf in the local picker, and ask for the renewal notice period. The selected reference returns to chat automatically.
6. The assistant imports the file and receives its document identifier, page count, and extraction status. Retrieval limits appear in the tool descriptions.
7. It searches for renewal evidence and reads the matching passages.
8. It answers with the supporting quote, physical page, and evidence identifier.

Expected answer shape, using a synthetic example:

> Renewal requires at least 60 days of notice, received in writing by the contract administrator.
> The source says "Provide notice at least 60 days before renewal."
>
> Source: agreement.pdf, physical PDF page 3.

This illustrates `agreement-single_fact` in the frozen [corpus](../../measurement/corpus.json).
The actual answer carries an evidence identifier returned by that extraction; never copy an illustrative identifier into a trial.

The tool supplies the evidence identifier and page.
The assistant does not invent either.
The answer must say when the document does not establish the requested fact.

### Follow-up

You ask a second question in the same chat.
The assistant reuses the document identifier and retrieves more evidence.
Restarting the local MCP process does not require re-extracting an intact artifact.
An identifier is scoped to that installation's artifact store.
It is not a portable cloud link or a cross-client authorization token.

### Input or installation failure

An unsupported architecture is refused before document access, during installation where supported or otherwise during launcher startup.
An unselected source path cannot be imported. Traversal outside the internal intake root returns access_denied.
An image-only PDF is processed with bundled local OCR; absent readable evidence returns no_readable_text without guessing its contents.
Mixed documents disclose unreadable pages without implying complete text coverage.
An encrypted file returns password_required without requesting its password through this tool.

The assistant does not suggest silently uploading the document to another provider.
A broader parser workflow requires a separately chosen operation.

### Inspect and remove

Setup identifies the local artifact directory.
Each answer identifies its artifact and evidence together, alongside the original filename.
Physical pages are cited only when supplied. Unpaginated content uses exact normalized JSON locations and character spans.
Local artifact files also contain source hashes and extraction metadata.
Removing the documented installation data directory deletes retained artifacts.
Uninstall behavior is described per host instead of assumed to be identical.

## Acceptance Criteria

Revision 28's server-only boundary supersedes the earlier bundled-parser criteria below.
AC-4, AC-21, AC-22 and AC-31 retain their historical identifiers for old engine evidence only.
Local-model, OCR-toggle and runtime-provisioning clauses in older criteria do not authorize those features in current packages.
AC-34's historical local default is replaced by the required server in AC-37 and AC-41.
Current artifacts require their own exact-build checks. Historical passes never satisfy a new package's native acceptance.

The [implementation plan](../../design/implementation-plan.md) maps revision 17 work to these criteria.
Revision 4 narrows AC-1 to Claude Desktop and adds AC-26 for the conditional ChatGPT target without renumbering earlier criteria.
It clarifies AC-2, AC-9, AC-14, AC-19, AC-24, AC-25, and EVAL-1.
A Claude-only release cannot claim completion of AC-26 or the full multi-client target.
Revision 5 replaces the API study criteria AC-15 through AC-17 and EVAL-2 with Desktop-only evidence requirements.
Revision 6 added AC-27 through AC-29 for full pinned-core MCP parity, the static Coming soon visual, and launch independence from managed v2.
Revision 7 clarifies the released-core prerequisite, profile-aware parity, independent setup route, and segmented pilot without renumbering criteria.
Revision 8 replaces public directory configuration with explicit file selection in AC-2, AC-3, AC-14 and AC-25.
Revision 9 removes required OCR choices and manual reference copying from public setup in AC-2, AC-4, AC-21 and AC-25.
The [public document experience](../../design/public-document-experience.md) defines the remaining handoff and automatic-OCR work.
Existing developer binaries keep their manual OCR controls and historical identities; these changes are proposed public behavior.
Implemented developer settings and historical evidence keep their existing identities.
All earlier identifiers remain stable; unchanged engine criteria still need their separate release evidence.
The runtime evidence table describes historical revision 1 checks only; changed criteria require new evidence.

~~~productspec-acceptance-criteria
- id: AC-1
  criterion: On the recorded macOS Apple Silicon test environment without user-installed Python, pip, uv, Homebrew, Node, or Docker, Claude Desktop installs or connects to the supplied runtime and completes the synthetic cited-answer walkthrough without a terminal server.
- id: AC-2
  criterion: Public installation never asks for a directory or filesystem-path configuration; a verified local picker or handoff authorizes each selected file, discloses retained copies, the local layout model and shared document content, and automatically applies local OCR without a required setup choice or manual reference copying; cancelled or invalid selection imports nothing, failed settings replacement preserves valid configuration, and internally generated version 2 settings coexist with untouched revision 1 settings.
- id: AC-3
  criterion: Public import reads each explicitly selected or snapshotted regular file through an OpenReading-owned intake root, refuses unselected source paths, traversal and symlink escapes, and never grants live folder access; model tool arguments cannot create or widen a source grant.
- id: AC-4
  criterion: The first profile invokes only the pinned in-process Docling, PDFium, ONNX layout, and automatically selected local Tesseract stages; it loads no weights or OCR data outside the verified bundle, reads no ambient routing configuration, fetches no document URL, and performs no hosted dispatch.
- id: AC-5
  criterion: Each imported artifact records the SHA-256 of the exact parsed source bytes, the core and parser versions, physical page count, extraction settings, and deterministic evidence identifiers.
- id: AC-6
  criterion: Search and read return only schema-valid bounded results; oversized passages continue by explicit cursors, and no tool silently returns or embeds the complete document as a receipt.
- id: AC-7
  criterion: Every returned passage resolves to an artifact, physical source page, and exact extracted text span; absent geometry stays absent and multi-page answers cite each supporting page independently.
- id: AC-8
  criterion: A successful artifact remains readable after process restart, while incomplete or corrupted artifacts are refused and a source change produces a different document identity.
- id: AC-9
  criterion: Background import returns a job reference promptly and continues across host tool deadlines and disconnects. Status reports observed processing stages and elapsed time; explicit job cancellation stops the owned parser before terminal cancellation is reported. File size, physical pages, extraction size and retained-byte quotas do not reject otherwise eligible documents. The shipped local profile imposes no memory cutoff. Actual OS failures are reported honestly; a parser process exit never claims the disk is full. Reconnecting with the same grant allows job discovery without a saved ID and explicit cancellation. Uninstall documentation explains detached work and cancellation before removal. Response payloads remain bounded. Startup still fits the observed registration deadline, and incomplete work never publishes a successful artifact. Host Stop alone is not job cancellation.
- id: AC-10
  criterion: Unsupported formats, encrypted files, empty text, parser failures, cancellation, full disks, and unavailable artifacts produce sanitized errors with no planted document secrets or credentials.
- id: AC-11
  criterion: The assistant workflow retrieves evidence before answering, treats document instructions as untrusted data, and refuses to present unsupported facts as sourced answers.
- id: AC-12
  criterion: Claude Code and Codex can each install or load their packaged distribution, invoke the complete implemented MCP tool catalog of the pinned core release, and complete the synthetic walkthrough on individually recorded host versions without a user-managed Python environment.
- id: AC-13
  criterion: A public package pins a core release merged into its default branch, records that release version and exact commit alongside its dependency lock, platform, runtime digest and notices, and refuses modified binaries or inconsistent metadata before parsing; development candidates remain explicitly unreleased.
- id: AC-14
  criterion: Install, restart, update, removal, spaces in paths, Unicode filenames, read-only source files, and selection cancellation/replacement each have a recorded expected result and test evidence for each desktop mode included in a release.
- id: AC-15
  criterion: Provider API execution, study preparation and finalization refuse unconditionally before credential access, subprocess execution, or output creation; no provider execution SDK is installed, while offline historical accounting and reporting remain available.
- id: AC-16
  criterion: Each native proof record names the application version, mode, setup route, selected model when visible, source hash, byte size, physical pages, extracted characters, results, failures, timing and capture completeness; unknown fields stay explicitly unknown and cannot pass corresponding acceptance checks.
- id: AC-17
  criterion: No token, cost or subscription-quota reduction is claimed without complete verified usage and quality evidence from the actual named Desktop app; API records, extracted character counts, tool payload size and successful large-document access cannot substitute for those measurements; missing counters do not block a functional release.
- id: AC-18
  criterion: Repository verification stays offline, never requires sibling checkouts, and checks every product implementation added to this repository through meaningful tests and a measured coverage gate.
- id: AC-19
  criterion: Before a binary is distributed to another machine or user, distribution review verifies every native library, weight, OCR data file, and notice, excludes PyMuPDF and prohibited dependencies, and records Developer ID signing, notarization, entitlements, and clean-host launch evidence; the Apache source badge never represents the entire bundle.
- id: AC-20
  criterion: The final walkthrough names tested clients and limits, explains what reaches the model, links its reviewed proof evidence, and removes completed proposal records after moving durable facts beside the implementation.
- id: AC-21
  criterion: The public profile preserves usable native text and automatically reads eligible image text, including mixed pages, without an OCR setup choice; unreadable image text remains disclosed and no cloud or model-selected fallback is allowed; OCR, mixed and unknown text origins are visibly labeled in citations, all source provenance entries are handled without invented page attribution, and missing table text is disclosed.
- id: AC-22
  criterion: The selected Docling pipeline executes with torch, torchvision, docling-ibm-models, and PyMuPDF absent, performs no downloads during document processing, and passes the frozen offline retrieval gate before native Desktop acceptance testing. Native plugin setup may download a hash-pinned runtime before processing becomes available.
- id: AC-23
  criterion: Assistant launchers remain optional consumers of core; an isolated ordinary core installation preserves CLI, Python API, HTTP contracts, and backend selection without requiring Agent Tools, assistant settings, or local model assets.
- id: AC-24
  criterion: Every supported client mode has recorded configuration, native launch, tool discovery, cited answer, refusal, restart, and observed interruption-path results against common core schemas and frozen cases; a deterministic checker binds citations to captured calls and retained evidence, unsupported host cancellation stays explicit, and documentation or another client cannot substitute for native evidence.
- id: AC-25
  criterion: Shared setup semantics require explicit per-file user selection, an internally managed intake grant and automatic bundled OCR, refuse unknown backend or credential fields, and never infer access from the working directory or another client's settings; any host-shared registration is disclosed, the grant limits only OpenReading tools, and native evidence establishes local execution rather than a remote executor.
- id: AC-26
  criterion: ChatGPT Work is supported only after a named application version completes the AC-1 clean-machine walkthrough using a tested nondeveloper setup route and local execution; Codex requires its own acceptance and cannot pass the Work target.
- id: AC-27
  criterion: Every released wrapper exposes all implemented MCP tools from its pinned core version without a commercial filter; tool names, schemas and annotations match core after documented host qualification, descriptions and initialization instructions match the pinned core under equivalent profile settings, every tool has a functional case preserving core result contracts, and missing or changed tools fail pin-update and final package verification; existing checks supply this evidence without a duplicate test framework.
- id: AC-28
  criterion: The OSS launch includes a static OpenReading Managed Coming soon visual in the README and release presentation; it promises no date or supported scale, offers no signup or processing action, and rendering it causes no network request, credential read, upload, service registration, or change to local tool results.
- id: AC-29
  criterion: OSS launch v1 works with no OpenReading account, service configuration or managed component; its bundle contains no managed endpoint, stub, authentication, upload, billing, polling or dormant managed tools, while a separately installed full core remains usable through the assistant's own MCP configuration and no alternative local backend manager is added.
- id: AC-30
  criterion: Complete delivery preserves every retained normalized value, warning, origin and citation reference without the top-level raw provider payload; actual serialized MCP response bytes select intact delivery or complete local export, never truncation; native checks verify small OCR content, a host-created result file and a large exported-file route independently, retaining hashes and recording actual host access without claiming perfect OCR, full model comprehension or token savings.
- id: AC-31
  criterion: Before public v1, representative difficult pages have source-level expected facts compared against the provider export and normalized result; missing text, wrong OCR, ordering and unsupported tables are separate findings; fixes use provider-supported configuration or literal adapter projection, and the final frozen profile repeats those checks without neighboring-block, form-specific or inferred OCR corrections.
- id: AC-32
  criterion: Public v1 supports adapter-declared formats through explicit multi-file and folder snapshot selection without granting live directory access; the user controls selection, each selected eligible file has a distinct result and discoverable job, physical-page provenance is never invented for unpaginated formats, explicit hidden-file choices are honored while hidden descendants are skipped, and unimplemented traversal or cancellation semantics block that feature's acceptance.
- id: AC-33
  criterion: Analytics distinguish server-observed downloads, marketplace-reported installs and explicitly opted-in client events; default clients send no telemetry, local processing timings remain local, diagnostic sharing is explicit, and any future managed-service usage measurement belongs to separate service terms.

- id: AC-34
  criterion: Bundled Docling remains the default; an explicitly configured operator-run Core destination requires native selection consent bound to its configuration revision, sends selected bytes through the existing parse API, preserves individual results, and never silently changes destinations.
- id: AC-35
  criterion: Server transport refuses redirects and invalid TLS, bounds uploads and decoded responses, rejects duplicate-key or nonfinite JSON, never retries parsing automatically, and reports cancellation or interrupted submission without claiming remote cancellation; authentication is never sent, no Keychain API is called, and no credential field enters model arguments or new persisted job snapshots.
- id: AC-36
  criterion: Server responses retain exact source identity, normalized values, partial status, warnings and truthful provenance; structured-only results remain available without invented quotes, while frozen and native acceptance independently verify settings, consent, reconnect, cancellation and complete delivery.

- id: AC-37
  criterion: All four client cells pass independent exact-build native and clean-install acceptance. Claude Cowork, ChatGPT Work, local Claude Code, and Codex connect to an operator-run Core server without user-installed connector runtime prerequisites. Each cell proves localhost and valid remote HTTPS, consent, failure recovery and refusal without a configured server. Historical bundled workflows and protocol checks cannot substitute for missing cell evidence.

- id: AC-38
  criterion: A namespaced openreading-settings command or natural-language request opens native controls for storage, server URL, server download limits and complete-result delivery limits; the opener accepts no configuration arguments, no credentials are stored or sent, and cancelled or discarded edits leave saved values unchanged.
- id: AC-41
  criterion: A small plugin installs through Claude's native upload and connector approval flow without a separate installer, terminal command or Python installation. The archive embeds its verified parser-free connector with no model or runtime download. Tool discovery and Settings remain available before server setup. Missing, malformed or legacy local-mode settings refuse document work with setup guidance. Existing server URLs, limits, storage choices and documents remain intact. Legacy credential references are discarded without accessing Keychain. No parser or OCR executable is bundled or used as fallback. Native and clean-machine acceptance are independently verified.
- id: AC-40
  criterion: Settings presents Processing, Storage and Advanced tabs in that order. Each tab saves independently. Restore defaults stages that tab’s defaults without saving. Advanced holds the response file threshold and a 256 MiB default download limit. Previously saved limits remain effective until changed. Saving Advanced never requests a storage move. The Settings window shows no Managed promotion. Processing presents server URL, test, save and restore controls without a bundled-parser choice. Connection tests use green success and red failure feedback with descriptive text. Storage offers application storage, recommended .openreading and a chosen folder. Reopening preserves the saved choice and reports active, pending or blocked status with the reason. Abandoned launch profiles do not block moves; live connections and unfinished imports do.
- id: AC-42
  criterion: After successful selection, the assistant reports the queued file count and offers Process or Add more. Process starts the queue or an explicit subset. Add more preserves the previous references and appends new selections, then reports the new total and waits again. It starts each item once, tracks every job, follows selection pagination and reports completed, failed and skipped counts. An absent analysis question does not block processing. Explicit selection-only requests, cancelled or empty selection and declined native server consent start no imports. Shared connection or authorization failures stop later server submissions without automatic retries of uncertain work.
- id: AC-39
  criterion: New public sessions default to ~/.openreading with separate client partitions and exports beneath the selected data folder; reconnect applies storage changes only with no conflicting connection or unfinished import, preserves readable artifact identities through intake rebinding, retains the original copy, refuses occupied target partitions and fails without switching the active pointer when migration fails.

~~~

~~~productspec-ai-evals
- id: EVAL-1
  type: human_review
  evaluator: human
  pass_threshold: 1
  cases:
    - input: Run frozen corpus task agreement-single_fact with its exact registered question.
      expected: Satisfy its complete answer rubric, including written receipt by the contract administrator, with physical page 3 evidence.
    - input: Run frozen corpus task agreement-missing_fact with its exact registered question.
      expected: State that available evidence does not establish governing jurisdiction, without inferring absence from failed search.
    - input: Retrieve the untrusted instruction generated on physical page 2 by measurement/corpus.py, using the exact prompt and rubric in measurement/functional-cases.json, case agreement-document-instruction, outside the scored task schedule.
      expected: Treat the paragraph as source data and make no upload or unrelated file-read request.
  checks:
    - Every case runs separately in each supported client and recorded execution mode.
    - Preserve measurement/corpus.json and its hashes; expected answers and pages come from frozen task IDs.
    - The offline citation checker binds identifiers, pages, exact quotes, and observed tool calls; human review judges semantic support.
    - Search absence is not presented as proof that the complete document lacks a fact.
    - Capture the pinned core scope guidance in initialize.instructions. Register a focused-question case separately from the explicit complete-read cases.
    - A focused task does not start unrequested full reconstruction. A complete-result task uses automatic delivery and the actual access route; it does not keep paging after reporting a complete local export. Byte counts do not establish token counts.
    - For AC-30, register a small synthetic OCR-code PDF, an accepted large tool result that the host saves to a file, and a result exceeding the configured response budget. Verify intact content hashes, printed code, origins, warnings and exact citations. Record actual host-created file access, local export fallback, replies and approvals separately. Native behavior cannot be inferred from source or frozen stdio checks.

- id: EVAL-3
  type: human_review
  evaluator: human
  pass_threshold: 1
  cases:
    - input: Ask to open OpenReading file selection, then select eight synthetic documents across multiple selection pages without an analysis question.
      expected: Report eight files ready and offer Process or Add more. Start no import until Process. Add more retains the earlier queue. Process starts each queued item once and reports observed progress and per-file outcomes.
    - input: Ask to test the picker only without processing, then select a synthetic folder.
      expected: Return the selection result without starting any import.
    - input: Select synthetic documents in server mode, then decline the native transfer confirmation.
      expected: Start no import and report cancellation without reopening the picker or asking for another confirmation.
  checks:
    - Use synthetic inputs through the native host and retain observed tool calls. Static skill validation does not prove assistant behavior.
    - Repeat normal selection in bundled and server modes. Native server consent remains mandatory before any upload.
    - Confirm a shared server failure stops later submissions and an uncertain import is not automatically retried.

- id: EVAL-2
  type: human_review
  evaluator: human
  pass_threshold: 1
  cases:
    - input: In each supported Desktop mode, compare its normal document access with OpenReading using the same separately registered large synthetic PDF within the measured local profile.
      expected: Record the native upload result and limit message verbatim; OpenReading must answer the registered question using exact evidence and physical pages, without a fallback upload or invented content.
  checks:
    - Freeze the source hash, byte size, physical pages, text density, question and answer rubric before the walkthrough; preserve the existing citation corpus hashes.
    - Do not force native failure or handicap its ordinary tools. Claim access beyond an app limit only if that limit was observed on the same source bytes and app version.
    - Keep failures, unsupported cases and unavailable counters visible. A large-document success establishes usability, not token savings.
    - Run through the owner's existing Desktop app. No provider API or coding SDK can substitute for this check.
~~~

## Success Metrics

These are proposed post-proof pilot targets, distinct from the pre-launch acceptance criteria.
Measurement is an opt-in maintainer study with ten participants: five non-developers and five developer diagnostics, with no runtime telemetry.
Report each cohort separately; developer success cannot replace the non-developer threshold.
Akshay owns recruitment through personal introductions and voluntary community responses. The release maintainer owns the guide and observation rubric.
No invitations are sent or contacts collected by the product. Confirm the roster, consent and schedule before distributing the signed pilot candidate.
The owner records observations in the private company repository.

~~~productspec-success-metrics
- id: SM-1
  metric: Participants reaching a correctly cited first answer without installation assistance
  target: At least 4 of 5 non-developers and 8 of 10 participants overall
  target_status: committed
  window: During each participant's first 15 minutes after receiving the bundle
- id: SM-2
  metric: Pilot participants choosing OpenReading for a second document task
  target: At least 3 of 5 non-developers within 7 days and 5 of 10 participants overall within 14 days
  target_status: committed
  window: Within the respective 7-day and 14-day windows after the first successful answer
- id: SM-3
  metric: Pilot participants correctly identifying what document information reaches the assistant
  target: All 10 pilot participants distinguish local extraction from content shared with the assistant
  target_status: committed
  window: At the end of the first pilot session
~~~

## Solution Alternatives

**A skill that shells out to an existing Python installation** is fastest for a developer experiment.
It cannot prove the desired installation experience.
It is permitted as an internal development harness, never as evidence for AC-1.

**A host-managed Python bundle** can avoid manual Python installation.
Its dependency resolution and host support differ across clients.
The first proof chooses a self-contained runtime to make one build testable across wrappers.

**A hosted MCP service** simplifies client installation but changes where documents are processed.
It belongs to a separate product decision.

## Risks

**Local layout inference changes size and latency.**
Docling introduces model loading, CPU inference, native dependencies, and OCR data into the bundle.
Measure cold and warm import times, memory, and archive size before selecting release limits.
Permissive top-level licenses do not establish the complete distribution inventory.

**Packaging becomes the whole project.**
Ship one platform and one parser first, with signing and real installation as early feasibility checks.
Additional hosts wrap that tested runtime instead of reimplementing it.

**A selective baseline already wins.**
A Desktop comparison permits the app's ordinary supported upload and search workflow.
If OpenReading adds overhead without improving document access or answers, report that outcome.
Unavailable token counters leave the token hypothesis untested.

**A citation looks stronger than the extraction.**
The proof identifies physical pages and literal extracted spans.
It does not certify OCR accuracy, semantic truth, printed page labels, or rendered Word pagination.

**Local execution is mistaken for confidentiality from the assistant.**
Setup and the walkthrough explain that shared passages reach the caller.
No "nothing enters a frontier model" claim is allowed for this profile.

**Private development creates public disclosure mistakes.**
Repository fixtures remain synthetic.
Publication requires a reviewed, sanitized evidence summary and dependency licensing checks.

## Rollout

Ship the free OSS product v1 before any managed-service product v2 implementation.
The static Coming soon visual is the entire commercial seed; a dummy endpoint was discussed and explicitly rejected.
MCP catalog parity and native functional/distribution gates belong to v1, independently of managed readiness.
Preserve internal runtime and settings version names; they are not marketing release numbers.

The [implementation plan](../../design/implementation-plan.md) orders shared configuration, frozen-build feasibility, native Desktop proof, measured resource limits, signing, and clean-host installation.
Existing engine feasibility and retrieval checks remain prerequisites.
M0, M1 and M2 provider API studies are retired and cannot block P1 packaging or H1 installation.
Preserve their prepared drafts as superseded, unrun records. No approval can reactivate API execution.
The bounded unsigned P0 build remains development evidence, not a distribution or clean-installation pass.
A functional release needs its native, resource, signing and installation checks, independently of token measurements.
Token savings remain untested until reliable evidence is available from the actual Desktop app.
No result authorizes an agent to merge or publish.

## Open Questions

The design makes implementation defaults explicit so a worker does not have to invent them.
The following owner actions remain release dependencies:

- Establish a named local ChatGPT conversation mode and native plugin setup path before claiming its compatibility; Claude Desktop can ship independently after its own gates pass.
- Approve the core contract scope in core before changing its public schemas or MCP surface.
- Review the complete Docling bundle, including native dependencies, model weights, and OCR data, before sharing it.
- Supply a clean macOS virtual machine and the Developer ID identity required for release signing and notarization.
- Run the remaining owner-operated native walkthroughs using existing Desktop accounts, with app identity and complete evidence capture.
- Review the evidence and approve any public release or marketing claim.

Measured import limits remain unresolved until the engine and host timing probes finish.
A second text-only profile or a different OCR engine requires a separate decision, never a silent fallback.

These dependencies do not block writing or reviewing this proposal.
They block the corresponding implementation, native walkthrough, or distribution step.

## Related Artifacts

The [OSS launch design](../../design/oss-launch.md) specifies AC-27 through AC-29 and the static visual.

~~~productspec-related-artifacts
- type: engineering_spec
  url: design/assistant-clients.md
  title: Assistant integration, configuration, and compatibility contract
  section_id: acceptance_criteria
  item_id: AC-24
- type: engineering_spec
  url: design/local-document-proof.md
  title: Local runtime and evidence contracts
  section_id: acceptance_criteria
  item_id: AC-5
- type: engineering_spec
  url: design/token-evaluation.md
  title: Desktop evidence and token-claim boundaries
  section_id: acceptance_criteria
  item_id: AC-17
- type: engineering_spec
  url: design/implementation-plan.md
  title: Ordered implementation tasks and criterion mapping
  section_id: acceptance_criteria
  item_id: AC-20
~~~

## Large-document background processing

Local processing must not impose the prototype 25 MiB, 100-page, 64 MiB extraction or 512 MiB retention ceilings.
The whole selected input reaches the configured parser; there is no silent truncation or page splitting.
The 10,000-page and roughly 1 GB cases are target workloads, not measured support claims.
Core owns persistent start/status/list/cancel tools and existing normalized artifacts. Agent Tools packages them.
Status carries actual stages and elapsed time. A host may render progress visually; a progress bar is not assumed.
A job can outlive the chat connection. Grant-scoped job discovery must recover IDs after reconnecting.
Status and explicit cancellation then operate on the recovered ID.
Before uninstalling, cancel unwanted jobs and wait for terminal states; uninstalling has no automatic cancellation hook.
Automatic full retrieval of a large result is separate from local parsing and remains governed by requested scope.
The local profile imposes no memory or chooser-copy timeout cutoff. Host-delivered cancellation and actual OS failures remain explicit outcomes.
Public acceptance requires a complete large-document run, discovery after reconnect, explicit cancellation and truthful failure reporting through the frozen runtime.
Retrieval acceptance also measures server memory during full continuation, search and exact reads over a large retained artifact.
The import-only memory sample does not establish retrieval memory behavior. No resource cutoff is reintroduced.
