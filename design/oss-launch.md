# OSS launch v1 and the Coming soon boundary

Status: ProductSpec revision 15 proposal. The README includes static preview copy; release catalog parity, host presentation and distribution acceptance remain pending.
Contract: [ProductSpec](../product/specs/local-document-proof.product-spec.md), AC-27 through AC-30.
Execution order: A1, D0, C0 and N3 in the [implementation plan](implementation-plan.md).

## Product versions and ownership

Public product v1 is the free OSS launch. Managed product v2 starts after OSS launches.
Historical prototype revision 1, the local `local-document-proof-v2` profile, version 2 settings and P0 release identifiers keep their existing meanings.
This proposal changes no runtime pin, artifact identity, schema version or stored settings path.

Core stays free OSS, including its entire implemented MCP surface, ordinary APIs, adapters and strategies.
Agent Tools stays free OSS and bundles only the selected slim Docling local runtime.
It does not install, select or manage alternative local backends or someone else's core server.
Power users can independently install full core and configure their assistant to connect directly to that core MCP server.
No OpenReading company account or paid entitlement gates local tools.

## All implemented core MCP tools at launch

MCP tools are discovered with `tools/list` and invoked with `tools/call`.
“All endpoints” means the implemented tools of the immutable core version included in the release, not a new HTTP API or an unimplemented core roadmap.
The current candidate `4b67694` implements:

| Tool | Required behavior |
| --- | --- |
| `openreading_start_import` | Start a persistent local import and return a job ID promptly. |
| `openreading_get_import` | Report actual stage, elapsed time and a terminal artifact receipt or error. |
| `openreading_list_imports` | Discover grant-scoped retained jobs after reconnecting, without a saved job ID. |
| `openreading_cancel_import` | Cancel one pending import without deleting a completed artifact. |
| `openreading_import` | Retain the requested granted document, return a bounded receipt, and preserve explicit core refusals. |
| `openreading_get_document` | Return complete normalized content through measured automatic delivery or a local file export, excluding the raw provider envelope; retain explicit fragment compatibility. |
| `openreading_search` | Search retained evidence with the documented literal retrieval contract, exact excerpts and cursors. |
| `openreading_read` | Resolve returned evidence identifiers to bounded exact passages and source provenance. |
| `openreading_select_document` | Return a locally selected reference through a trusted provider, or explicitly refuse when absent. |

The candidate catalog is nine tools, including background start, status, cancellation and job discovery.
Pin changes require fresh same-profile catalog and frozen functional checks before installation.
A future pin must include every additional implemented core tool before that pin can ship in Agent Tools.
Do not advertise MCP parse, compare, strategy, folder operations merely because related CLI/HTTP operations exist.
Do not invent placeholder tools for operations core has not implemented.

The first distribution keeps its explicit local Docling profile, internal grants, bounded replies and no-hosted-dispatch rule.
The local Docling profile has no document-size, page, extraction, storage, processing-time or memory cutoff.
A1 owns public chat-driven file selection without directory configuration; the current developer form does not pass that launch requirement.
Exposing the full MCP interface does not install every backend or make unsupported extraction capabilities work.
Where core supports an operation only with absent optional capabilities, preserve its explicit refusal or warning.
If a core pin introduces a tool incompatible with these boundaries, resolve its safe local contract before accepting the pin.
Do not satisfy this rule by removing the tool from the expected list, hiding it behind managed v2, or returning fake success.
Future upstream changes can require a client/runtime update; no automatic compatibility or no-reinstall promise is made.

## Catalog parity evidence

C0 is a small pin-update and final-package check, integrated into E0, the existing P0 smoke and N2. It is not a separate verification framework or a prerequisite for starting native setup work.
The launcher delegates directly to core; there is no second runtime implementation to reconform.
Freezing can still select the wrong package or profile, and the Claude Desktop manifest repeats tool names and user-facing summaries.

For each pin update, obtain the reference catalog and initialization instructions from the pinned core package under the same effective Docling profile as the bundle.
Use identical page, byte, deadline, memory and OCR settings. Asset paths may differ between installations but must identify the intended assets.
Reuse the P0 real-stdio smoke for the frozen observation and N2 for host discovery/invocation. Add a focused check of any hand-maintained manifest catalog; wrappers that declare no catalog need no invented inventory.
Record the core release/commit, effective profile, runtime hash and comparison result.

Compare names, input/output schemas where declared, annotations and declared capabilities strictly after documented host name qualification.
Compare model-facing descriptions and initialization instructions against the pinned core's output for that same profile, including OCR off and on.
The current core changes import/read descriptions for Docling; selection-provider availability also changes descriptions and initialization instructions. Both fields still need capture to detect future regressions.
Do not compare default PyMuPDF prose against Docling prose, remove these fields from comparison, or blanket-allow all description differences.
Manifest installation summaries may differ in wording, but must agree on tools, engine, limits, OCR and data disclosure. They are not necessarily the descriptions sent to the model.
Any host-added prefix or instruction wrapper must be specifically recorded; the core instructions and shared workflow must still be delivered and agree with the selected configuration.

Reuse existing selection/import/full-document/search/read success, refusal and citation cases; add only missing coverage or cases for newly implemented core tools.
Use regression tests for missing manifest tools, changed contracts, wrong profile descriptions and missing initialization instructions within the existing coverage gate.
Do not require a sibling checkout or network access in the offline gate.
The final package still needs complete coverage before release. Calling this a pin-update gate does not exempt the first release or permit shipping a filtered catalog.
A moving branch name cannot replace immutable provenance: keep existing candidate hashes, then record the released tag/version and resolved commit separately when R0 completes.

D0 requires two native cases: the small image-only code check and a separately registered larger result that needs multiple replies at the shipped byte cap.
Record actual reply counts, completion through a null cursor, observed approval prompts and the final citations. A one-reply fixture cannot satisfy continuation acceptance.
Choose retrieval by task and observed scope. Full retrieval stays available without mandatory search; an explicitly requested complete read does not need repeated approval of that choice.
Page and passage counts are rough signals only. Tool calls, JSON bytes, host approvals and model tokens are different measurements.

## Static Coming soon visual

Use this copy:

> **OpenReading Managed: Coming soon**
>
> Document processing on OpenReading's servers, without managing local compute.
> Planned after the public OSS launch.

The title is “Coming soon”, not “Unavailable”. This is product presentation, not an operational service response.
Show the visual in the README and existing release description or setup/help presentation supported by the client.
If a host offers no suitable in-app surface, its distribution page and installation guide carry the visual; do not invent a host widget or inject advertisements into chat.
No new UI subsystem is needed for this static text.
Use ordinary accessible text rather than an image containing the only readable copy.

There is no action button, signup link, payment prompt, live endpoint, capability check or service registration behind the visual.
Do not put it into MCP tool outputs, retrieved passages, error messages or assistant instructions.
Local errors continue to explain the actual local failure, not advertise a hosted retry.
The visual states no launch date, supported page count, free allowance or token-savings percentage.
If it becomes obsolete, a normal reviewed release updates the copy; no remote configuration mechanism is required.

## No managed components in v1

Do not build or ship:

- A dummy or no-op managed server, endpoint, health route or hosted capability response.
- A managed transport client, configured company processing URL, remote tool registration or feature polling.
- Authentication, account setup, credential fields, upload bridge, billing, credits or spending authorization.
- Dormant managed tools, automatic fallback, signup prompts or model-driven upgrade suggestions.
- A new analytics, waitlist or remote feature-flag subsystem as a condition of this launch.

Inspect the package inventory, client configuration and dependencies for these exclusions.
Verify that displaying the visual and using local tools reads no managed credentials and initiates no managed-service traffic.
Test local operation offline after installation with the required assets present and no company account.
Scope network claims to OpenReading's runtime; the assistant may make its own model requests.
Installation downloads and an explicit user visit to documentation are distinct from document-time network activity.
The existing ban on provider model API trials remains unchanged.

## Launch acceptance and later work

C0 and N3 join the existing installation, license, signing, provenance, retrieval, resource and native-host gates.
They do not replace those gates or make a working development-machine demonstration a distribution pass.
Only explicitly verified application versions and modes receive support claims.
Token savings remain unmeasured unless complete actual-Desktop usage and quality evidence establishes them.

Managed v2 needs a separate product specification after launch, including its account, upload, billing and data-handling contracts.
A future service does not get access to existing local documents merely because this visual shipped.
The OSS launch creates awareness of future intent, not an installed managed-service protocol.
