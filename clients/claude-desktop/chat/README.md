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

Use **Cancel** in the OS dialog for the cancellation check. Selection and copying have a 120-second deadline.
Another selection while that dialog is pending returns busy, without adopting another conversation's dialog.
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

The current candidate pins core `e795234` and uses the byte packing introduced in `fab92ad`.
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
