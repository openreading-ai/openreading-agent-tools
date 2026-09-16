# Chat document selection candidate

This unsigned development candidate opens an OS file chooser from a chat tool call.
The selected reference returns through MCP without copying a path or configuring a directory.
Automatic local OCR uses the bundled slim Docling pipeline and Tesseract assets.
Native focus, accessibility, installation and cancellation acceptance remain to be verified.

## Try the candidate

Ask: "Use OpenReading to choose a local document, then find its totals."
Approve the selection tool if your host asks. Choose one PDF in "OpenReading: Choose one PDF".
The assistant imports the reference, retrieves requested content, and reads exact passages for physical page citations.
Ordinary chat attachments still follow the host's upload path; this tool does not intercept them.

Use **Cancel** in the OS dialog for the cancellation check. Selection and copying have no local elapsed-time cutoff; the host can still cancel the request.
Another selection while that dialog is pending returns busy, without adopting another conversation's dialog.
If the chooser cannot be reached, restart Claude Desktop to reset selection. Background imports continue across that restart.
Claude Desktop's observed Stop action did not send MCP cancellation; it cannot be promised to dismiss this chooser.
Source tests verify child reaping on delivered cancellation.
In Claude Desktop 1.52386.3, one chooser returned `selection_cancelled` and its recorded child exited.
The dismissing action was not recorded, so this does not verify the Cancel button.
The intake stayed unchanged, but the owner reported an incorrectly positioned, immovable dialog.
The chooser now omits the hidden parent that makes Tk attach a macOS sheet.
Positioning, focus and successful file selection still require a native check of the rebuilt candidate.
Failed handoffs revoke their published copy without waiting for another publisher.
Deletion failures leave a private discarded copy for the next publisher sweep and preserve the original tool error.
Filesystem failures can prevent revocation; a fixed cleanup diagnostic reports that exception.

Copies stay under `claude-desktop/v2/selection/ready`, within OpenReading's application data.
Imported evidence stays in `claude-desktop/v2/artifacts`, shared with other v2 Claude Desktop connectors.
Removing an intake copy does not erase an imported artifact or excerpts already sent to the assistant.
The development helper can clear selected copies; a public retention interface remains unfinished.

OCR text can differ from printed text, and exact identifier search can miss evidence.
Rotated text and damaged native layers remain recorded limitations of the selective pipeline.
Verify important OCR quotes against the physical source page.
No setup decision changes historical directory grants, OCR switches or saved settings.

This candidate is not signed, notarized or accepted on a clean machine. Token savings remain unmeasured.

OpenReading Managed: Coming soon.

## Dependency privacy

The candidate disables ONNX Runtime telemetry before the document engine initializes.
Earlier development builds could create a device identifier and telemetry database under
`~/Library/Application Support/Microsoft/DeveloperTools/.onnxruntime`, outside OpenReading's artifact store.
The launcher now sets the pinned runtime's startup opt-out; it does not delete existing shared Microsoft data.
The frozen smoke checks a fresh home for unexpected persistence, with network access denied.
This check does not establish whether earlier builds transmitted events or prove installed-host network behavior.

The `25c15c4` candidate introduced `openreading_get_document` for the complete retained normalized result, excluding raw provider payloads.
Search remains optional. Requested document content enters the assistant context; full retrieval can include all extracted text.
The profile still controls available channels, including its table limitations.
Updated frozen and native checks remain separate from the historical observations above.

The September 14 frozen check at core `25c15c4` reconstructed the synthetic OCR-code result and preserved its exact page-2 citation.
The larger two-page synthetic 1040 required 66 replies and reconstructed all 549,055 bytes of retained normalized content.
Both page-2 amounts survived. This is direct MCP with staged intake, not a native chooser or Claude answer.
The repeated-call cost in native chat remains unmeasured. Complete transport is not complete host acceptance.

The earlier retrieval candidate pins core `e795234` and uses the byte packing introduced in `fab92ad`.
Its frozen 1040 check returns the same 549,055-byte content in 10 replies rather than 66.
The small OCR-code case still takes one reply and preserves its exact page-2 code and origin.
Both checks also compare all returned evidence, page origins and warnings with retained records.
Native acceptance needs both cases: the OCR answer and a multi-reply read through the final null cursor.
Record actual approval prompts separately from protocol reply counts.

The shared workflow matches retrieval to the request. Whole-document requests authorize full continuation;
focused questions can use search and exact reads. Counts of pages and passages are not token measurements.
`WORKFLOW.md` is a review copy, not proof that Claude receives those skill instructions.
Core now delivers this scope rule in its MCP initialization instructions. Protocol tests prove delivery, not model compliance.
A separately registered focused question complements the two explicit complete-read cases. Retrieval choice still needs native observation.

Background imports use `openreading_start_import`, `openreading_get_import`, and `openreading_cancel_import`.
The job survives a chat disconnect and exposes actual stage, elapsed time and its final artifact receipt.
Use explicit job cancellation to stop processing; host Stop alone does not cancel it.
Candidate core `4f4351a` adds `openreading_list_imports` for discovery after reconnecting.
Use the returned job ID for status or explicit cancellation. Earlier eight-tool installations require an update for discovery.
Before uninstalling, cancel unwanted jobs and wait for terminal status. Removing the extension does not automatically cancel detached work.
Reconnecting with the same intake and artifact locations preserves access to retained jobs.
This candidate removes prototype document-size, page-count, extraction-size, storage and elapsed-time caps.
No local memory cutoff stops processing. Large-document accuracy and native progress UI require separate checks.
The current retrieval verifier loads normalized content into server memory. Bounded replies do not bound server memory.
The verifier removes redundant response decoding and streams passage verification.
Complete frozen retrieval was measured on a retained large artifact, with every continuation matching stored content.
Memory still grows with the normalized document. This direct-protocol check does not establish native Claude delivery or document accuracy.
When a host reports a timeout, check whether its local MCP log recorded the request before attributing it to parser or retrieval performance.

## Complete delivery candidate

Complete-result requests use `openreading_get_document` with `delivery: "auto"`.
The optional advanced response budget defaults to 1000000 serialized MCP bytes, including escaping; it never limits parsing.
A fitting response contains intact normalized content, parser warnings, page origins and citation mappings.
The host can display it inline or save a tool-result file; existing host tools must establish actual access.
Oversized content is saved intact under `~/Downloads/OpenReading`, separated by the input grant, with a byte count and SHA-256.
A saved local path does not give Claude's cloud sandbox access. Attach that export, or use a mode with already-authorized local access.
Attaching the export sends its content to the assistant host. Cowork is optional; this connector adds no execution environment.
Exports remain until removed separately, including after artifact removal. Default runtime telemetry remains disabled.
Source checks and earlier synthetic host probes do not establish native acceptance of this rebuilt candidate.

The advanced budget accepts whole numbers of at least 4096. The manifest exposes that minimum;
the host's manifest format cannot enforce integers, so invalid values still fail launcher validation.
macOS may request Downloads permission, or deny exports if that permission is unavailable.
Native and clean-machine checks must record the prompt, its application attribution, and denial behavior.
Exports contain complete extracted text. Depending on system settings, indexing, backup or sync may include them.
The next export under the same grant removes abandoned temporary files created by this candidate.
Active writes and completed JSON exports are preserved. Older temporary names require manual cleanup after their writers exit.
The retrieval tool can write exports, so its write annotation also applies to inline and fragment requests.
Measure actual approval prompts for every route rather than assuming read-only approval behavior.

The candidate core pin retains provider-original list markers with their original page spans.
Reimport older documents to recover omitted list items; retained artifacts are not rewritten.
The bundled OCR engine remains Tesseract. Alternative OCR and table-stage experiments do not establish a new release default.

The candidate distinguishes provider text preserved in separate spans from text omitted for invalid provenance.
Search and exact reads retain document-level warning flags; they do not identify a fault in each quoted passage.
Old artifacts keep their recorded warnings. Reimport to obtain the current warning distinctions.

Background jobs can survive a chat or server disconnect. Reconnect with the same input grant,
list imports, cancel any active job, and wait for a terminal status before uninstalling.
Uninstalling the connector does not provide a core cancellation hook or remove retained documents and exports.
Native host cancellation, uninstall behavior and export permissions still require owner-operated checks.

Complete-delivery receipts summarize measured physical-page origins before the full content is opened.
They distinguish unmeasured origins from recorded unknown origins and preview pages with neither page nor block text.
Warning counts describe warning records, not affected pages or regions. Unlocated warnings remain unlocated.
A block can produce multiple evidence passages; those counts describe different units.
These metadata fields change no normalized text, geometry, citations or OCR output.

Background job status includes `page_progress` when Docling reports successful physical-page assembly.
For example, 12 assembled pages out of 251 is an observed count, not a percentage or time estimate.
Document-wide processing and artifact publication can remain after every page is assembled.
The job must still reach `succeeded` before retrieval. Cache reuse and older jobs have no new page observation.
Updates coalesce to avoid per-page disk writes. Reconnecting reads the latest persisted observation.
Native checks must record displayed counts during conversion and the separate terminal state.

## Multiple files and folder snapshots

The chat candidate opens one macOS panel for multiple PDFs or folders. Selected folders include nested PDFs.
Hidden entries, symlinks, macOS packages and unsupported files are skipped with encountered-entry counts.
Skipped directories are not inspected, so their counts do not describe all files inside them.
Copies form a per-file snapshot rather than an atomic filesystem snapshot. Later additions require another selection.
An unreadable or changing entry refuses the snapshot and rolls back its copies on ordinary failure or delivered cancellation.
Original files and older selections remain untouched. No fixed file-count, depth or byte cutoff is introduced.

Core returns paginated items with opaque references and basenames. Follow next_cursor with the same selection tool.
A continuation reads retained receipts without opening another dialog and survives server restart.
Import each item once with the existing background tools, retaining distinct job and artifact IDs.
Process the jobs sequentially and disclose any skipped or failed documents before claiming the selection was processed.
The native macOS chooser and clean-machine folder permissions still need owner-operated acceptance.
