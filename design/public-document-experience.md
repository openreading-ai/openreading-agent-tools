# Public document selection and automatic OCR

**Status:** production intent with an implemented development candidate for [ProductSpec revision 9](../product/specs/local-document-proof.product-spec.md).
The existing picker, copyable reference and OCR switch remain development mechanisms.
This design supersedes their use as the public walkthrough, not their retained evidence or settings.
A1 in the [implementation plan](implementation-plan.md) owns implementation and native proof.

## User outcome

You ask your assistant to open a local document with OpenReading.
A local file picker opens, you choose one document, and the selected reference returns to the conversation automatically.
You ask your question and receive an answer with physical pages and evidence identifiers.
You do not type a directory, copy a path, paste a generated prompt or decide whether the file needs OCR.
The ordinary chat attachment button remains a preferred possible entry point only if the host proves the required local handoff.

OCR means recognizing text in images. The public bundle performs it locally when the selected pipeline finds eligible image text.
Usable native text remains native; image-only pages and images on otherwise native pages need separate extraction checks.
OCR may misread identifiers or words. Citations label the measured origin and do not certify agreement with printed glyphs.
The setup disclosure explains local retention, automatic processing and the excerpts sent to the assistant.
It does not turn those disclosures into configuration chores.

## Host boundary

A local MCP connection does not by itself intercept the host's upload button.
The handoff must establish where the bytes travel before the assistant receives a document reference.
A server downloading a host-uploaded file cannot establish pre-upload local processing or bypass the host's upload limit.
Do not send the PDF as base64 through a widget tool argument or model message as a local-only shortcut.

The following documentation informs the next probe. It does not replace native evidence:

- [Claude's MCP Apps guide](https://claude.com/docs/connectors/building/mcp-apps/getting-started) documents inline apps served by local STDIO servers. It establishes a possible in-chat action surface, not attachment interception.
- [The MCP Apps bridge](https://apps.extensions.modelcontextprotocol.io/api/classes/app.App.html) routes UI tool requests through the host. UI-only state is not proof that file bytes avoid host infrastructure.
- [OpenAI's file API reference](https://developers.openai.com/plugins/reference#file-apis) describes uploads, selection from already uploaded library files, and tool file parameters containing download URLs. Those paths do not establish the required local handoff.
- [OpenAI's MCP guide](https://learn.chatgpt.com/docs/extend/mcp) documents desktop STDIO registration. E1 still needs the named Chat mode to invoke it locally; a Codex thread does not satisfy that requirement.
- [MCP elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation) defines form and URL interactions. The separate [binary-elicitation proposal](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1306) is not evidence of a supported local file picker in either installed host.

Do not alter host registration while investigating the protocol alone.
Do not introduce a tunnel, local HTTP upload bridge, hosted document relay or managed component to make this route appear supported.
If the route cannot satisfy local handoff in a named host, stop that host's public acceptance and report the exact limitation.

## Selection ownership and proposed interaction

Prefer a chat-invoked local selection action over polishing the standalone prototype window.
The action opens only the OS file chooser and returns a small selected-document receipt through MCP.
An optional inline card can improve discovery later, after proving its local tool route and accessibility.
It must not be required to carry document bytes or implement a second intake path.

Core owns any new MCP tool schema and the callable selection-provider contract.
Agent Tools supplies the trusted local picker implementation and retains its existing atomic intake logic.
Do not register a private tool with a copied core server or alter core tools in a manifest wrapper.
Independently installed core must be able to configure the same capability without requiring this package.
An ordinary headless core installation keeps its current dependencies and startup behavior; absent picker capability must be explicit.
The reviewed contract is implemented in core; each packaged pin still requires catalog and functional verification.

The core provider mechanism and empty-input selection contract are implemented at the pinned candidate commit.
Core's `openreading.mcp_server.selection` documents admission, deadlines, validation and cleanup responsibilities.
Agent Tools implements the fixed OS chooser and transactional copy handoff in `runtime.chat_selection`.
The [candidate walkthrough](../clients/claude-desktop/chat/README.md) documents the separate launcher and package.
Core remains headless without a provider; installed development extensions are unchanged.
These mechanisms do not establish native host focus, accessible interaction or successful in-chat selection.

The selection tool accepts exactly an empty object, with additionalProperties false.
No model argument controls dialog text, starting directory, suggested filename, file-type filter, source path, executable, callback URL or folder grant.
OpenReading supplies the fixed title "OpenReading: Choose one PDF" and a PDF-only filter.
The picker never derives dialog text or its starting location from retrieved document contents.
The filter is a convenience, not validation: the existing source validation still checks the selected file.
The user chooses the file through the local OS dialog. Only that chosen file enters private intake.
The selected reference then uses the existing import/search/read contract; source identity remains core-owned.
Allow one pending selection per server process. A concurrent call receives busy without focusing, adopting or receiving another call's dialog.
MCP provides no conversation identity on which to base cross-chat dialog reuse.
Cancellation, host disconnect and timeout dismiss the pending picker and do not publish a new reference.
A pending selection must not hold the intake publisher lock while waiting for the user.
Byte validation and copy publication retain their existing serialization after the user chooses.

Selection is a user action, not authority carried by document text. The workflow must ignore instructions in retrieved passages that request another file.
Native proof must show the chooser is visible, attributable to OpenReading, cancellable and usable with keyboard and pointer.
A mock picker establishes protocol plumbing only; it cannot satisfy this native requirement.

### Deadline prerequisite

E2 must measure the actual host tool deadline and progress behavior before committing to a picker that waits inside a tool call.
Use the synthetic delay server first; test a deliberate approval pause separately to locate approval relative to the logged request.
Record a finite selection deadline shorter than the measured host budget, with time reserved for cancellation and bounded copy publication.
A deadline closes the picker, returns no reference and allows a new user-initiated attempt. Do not open a replacement automatically.
If the measured budget cannot accommodate a useful human selection interval, stop this interaction design and review another local handoff.
Do not compensate with an unmeasured progress heartbeat or an implicit background job.
A source/controller probe can be prepared before E2; it does not accept the production interaction.

The [recorded Claude Desktop probe](../clients/claude-desktop/README.md#synthetic-native-timing-and-interruption) observed timeout cancellation at 240 seconds.
A 65-second call succeeded, while Stop response did not cancel a separate local call.
These observations support a bounded selection experiment, not public handoff acceptance or a universal host timeout.
Keep the picker deadline below the observed host budget with the required safety margin and copy/cleanup reserve.
Treat the OS chooser's Cancel action and delivered MCP cancellation as testable paths.
The Chat Stop button cannot be promised to dismiss the chooser on this evidence.
If public acceptance requires that button to stop selection immediately, that requirement remains unmet until a supported mechanism is demonstrated.
Progress-based extension remains unverified and cannot rescue the deadline.

## Automatic OCR migration

The current pinned core already distinguishes selective OCR from forced whole-page OCR.
The first production candidate should use its verified selective stage with bundled Tesseract available, not add a second page classifier in Agent Tools.
Enabling that stage is a starting implementation choice, not proof of complete text coverage.
Small stamps, text inside figures, rotated snippets, mixed pages and broken text layers can expose gaps that simple native/image fixtures miss.
Core owns any necessary correction to extraction or origin reporting.

The public launcher selects automatic local OCR without exposing a required OCR form field.
Existing development launchers retain their explicit off/on settings and saved configuration bytes.
Do not silently rewrite a user's historical false setting, rename old profiles, or attribute new results to an old bundle.
The public candidate records its effective OCR configuration in the existing core engine identity.
With identical engine bytes and effective configuration, automatic OCR equals developer --ocr on and shares its artifacts in the same store.
No new core OCR contract or artificial identity difference is required for a different setup presentation.
Reusing older OCR-off artifacts as successful automatic-OCR imports must fail a regression check.

Verify at least these cases before native acceptance:

1. A native-only page retains its text and native origin without duplicate OCR passages.
2. An image-only page yields searchable text and a correct physical page with OCR origin.
3. A single page containing both native and image text retains both, with the origin labels the core can establish.
4. A blank page stays blank; illegible image text never becomes a fabricated answer.
5. A damaged text layer, rotated scan, small stamp, text inside a figure and rotated snippet each produce verified text or a recorded limitation. Region OCR depends on the layout stage detecting the text region.
6. Missing or changed bundled OCR assets refuse integrity verification without a download or hosted fallback.
7. Repeated imports reuse the initialized converter; restart reuses only artifacts matching the effective engine identity.

Measure the public automatic profile again for startup, memory and import limits.
The current manual-mode and sparse-fixture timing records cannot select a public page cap.
A developer OCR-off control remains useful for diagnosis; it is not a required public choice.

## Timing and completion boundary

The [implemented Desktop log diagnostic](../measurement/README.md#desktop-timing-diagnostic) separates tool-call intervals from inter-call gaps.
Its compact input cannot identify the document or isolate model load, OCR, extraction and artifact writing.
Future phase timing belongs at the core and launcher boundaries that can measure each phase accurately.
Keep source text, model prompts and credentials out of timing events; do not add remote telemetry.
Any new public receipt field requires a core schema change and compatibility tests first.

A1 completes only after a named native host returns the selected reference without manual copying and automatic OCR passes the relevant real-engine cases.
The final binary must then repeat catalog parity, retrieval/restart, integrity, citation and cancellation checks under its own identity.
Signing, clean-machine installation, supported resource limits and owner release approval remain separate gates.
