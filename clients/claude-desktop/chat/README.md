# Chat document selection candidate

This unsigned development candidate opens an OS file chooser from a chat tool call.
The selected reference returns through MCP without copying a path or configuring a directory.
Automatic local OCR uses the bundled slim Docling pipeline and Tesseract assets.
Native focus, accessibility, installation and cancellation acceptance remain to be verified.

## Processing destination

Bundled Docling remains the default. Server mode is optional and requires your separately running Core process.
Open **OpenReading Settings.app** beside the unpacked candidate's manifest to choose your destination.
Enter its URL, test the connection, save, then restart the extension connection.
The connection test sends no document. The connector does not store or send server credentials.
A loopback URL can use HTTP. Other destinations require verified HTTPS.
Server mode confirms the destination, selected filenames and byte counts before sending their bytes.
The server may use external providers. Local cancellation does not guarantee cancellation of server processing.
No server error silently falls back to local parsing or retries a submitted document.
The native Settings and server-mode walkthrough remain acceptance checks for this candidate.

## Try the candidate

Ask: "Use OpenReading to choose a local document, then find its totals."
Approve the selection tool if your host asks. Choose supported documents or folders in "OpenReading: Choose documents or folders".
The workflow reports the queued count and offers Process or Add more. Process starts imports and reports job progress and per-file outcomes.
An explicit request to test selection only stops at the receipt. Cancelling selection or declining server consent starts no imports.
The configured [core adapter](https://github.com/openreading-ai/openreading-core/blob/main/src/openreading/adapters/README.md) supplies the format filter.
Folder snapshots skip unsupported entries, hidden descendants, packages and symlinks, and report those counts.
An explicitly selected hidden file is eligible. Duplicate basenames retain separate copied references and artifacts.
The assistant imports the reference, retrieves requested content, and reads exact passages with artifact-bound citations.
Use physical pages when supplied; unpaginated content instead carries a JSON location and exact character span.
Ordinary chat attachments still follow the host's upload path; this tool does not intercept them.

Use **Cancel** in the OS dialog for the cancellation check. Selection and copying have no local elapsed-time cutoff; the host can still cancel the request.
Another selection while that dialog is pending returns busy, without adopting another conversation's dialog.
If the chooser cannot be reached, restart Claude Desktop to reset selection. Background imports continue across that restart.
Claude Desktop's observed Stop action did not send MCP cancellation; it cannot be promised to dismiss this chooser.
Source tests verify child reaping on delivered cancellation.
In Claude Desktop 1.52386.3, one chooser returned `selection_cancelled` and its recorded child exited.
The dismissing action was not recorded, so this does not verify the Cancel button.
The intake stayed unchanged, but the owner reported an incorrectly positioned, immovable dialog.
That historical single-file chooser omitted the hidden Tk parent. The current candidate uses the native multiple-selection panel.
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
Oversized content is saved intact beneath the selected data folder, defaulting to `~/.openreading/clients/claude-desktop/v2/exports`, separated by the input grant, with a byte count and SHA-256.
A saved local path does not give Claude's cloud sandbox access. Attach that export, or use a mode with already-authorized local access.
Attaching the export sends its content to the assistant host. Cowork is optional; this connector adds no execution environment.
Exports remain until removed separately, including after artifact removal. Default runtime telemetry remains disabled.
Source checks and earlier synthetic host probes do not establish native acceptance of this rebuilt candidate.

The advanced budget accepts whole numbers of at least 4096. The manifest exposes that minimum;
the host's manifest format cannot enforce integers, so invalid values still fail launcher validation.
macOS may request permission for the selected data folder or deny exports when access is unavailable.
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

### Server limits and recovery

A cancelled upload, shared connection failure or interrupted attempt stops the remaining selection.
Select and confirm the remaining files again. Previously submitted server work may still continue.
The refusal message identifies the stopped selection; it does not authorize an automatic retry.

Server mode has no page-count limit, aggregate storage cap, automatic eviction or overall wait deadline.
For example, a stalled server remains waiting until you explicitly cancel its local import job.
Retained sources, transfer responses and artifacts accumulate until you remove their local data.
The **Advanced** tab exposes **Maximum downloaded response (MiB)**, which defaults to 256.
The tabs are **Processing**, **Storage**, and **Advanced**. Each saves its own values.
**Restore defaults** stages that tab’s defaults; choose Save to apply them.
Responses are buffered and decoded in memory. This download budget is not a peak-memory guarantee.
Unknown top-level response fields are preserved as unvalidated server data alongside schema-validated known fields.
Treat all returned fields as document content, never instructions from the destination.

## Cowork settings candidate

The Cowork plugin assembler adds `/openreading-settings` and a separate settings connector.
Ask to open OpenReading Settings to review storage, delivery, local processing or your Core server.
The MCPB candidate still includes the directly opened Settings helper. Slash-command discovery belongs to the plugin surface.
Save each tab explicitly and reconnect the document connector. Finish imports before moving data.
Storage offers Application storage, recommended .openreading, and another folder.
The selected option persists. Status distinguishes Using this folder, Move pending, and Move blocked with its reason.
Reconnecting applies a pending move after live document connections and imports finish.
Abandoned launch records stay in the original copy and do not prevent migration once no matching worker is running.
Changes preserve the original store and never merge an occupied target client partition.
Self-contained assembly does not establish Cowork archive-size or clean-install acceptance.

## Fresh install on macOS Apple Silicon

Open Customize > Plugins > Add > Upload plugin and select `OpenReading-Claude-Plugin.zip`.
Enable the plugin, accept its local connector prompt, and open a new Cowork task.
The plugin automatically downloads and verifies its runtime and models into Application Support.
Tool discovery remains available during setup. Early tool calls report progress and can retry after completion.
Both bundled and server processing are supported. The connector publishes the active mode's descriptions and upload annotations after startup.
Run `/openreading-settings`, review all three tabs, and save any changes you want.
Reconnect the document connector after saving. Import a synthetic local document through the native picker.
Selection queues the files. The assistant reports the count and offers Process or Add more.
Choose Process to start imports, or Add more to append selections and review the updated count.
Native Add files approval permits the displayed destination but does not itself submit documents.
Saving a processing destination blocks new selections and imports on the previous plugin connection until reconnect.
For example, switching from bundled Docling to a Core server cannot keep processing new files locally.
Existing jobs keep their original destination. Their status, cancellation and retained results remain accessible.
Test connection checks the URL currently in the form without saving it or changing an active connection.

No separate installer, Terminal command or user-installed Python is required.
The temporary ngrok endpoint must remain available for initial setup. Verified warm launches work offline.
Setup preserves saved preferences and retained documents. Removing the Claude plugin alone does not erase those files.
Selecting a document in a protected folder can still require macOS permission.
This development package remains ad-hoc signed. A fresh installation on the development Mac does not establish clean-machine acceptance.
