# OpenReading Desktop development candidate

Choose a document directory during installation. Enable **Read scanned text (OCR)** only when you want local OCR.
The candidate uses bundled slim Docling and Tesseract; it does not require a user-managed Python installation.
That packaging property does not establish a clean-machine installation pass.

OCR text can differ from the printed page, including letters and digits in identifiers.
Exact search may miss those identifiers; verify important OCR quotes against the source page.
Citation checks verify extracted text and provenance, not OCR transcription accuracy.

This is a local development candidate, not a signed public release. Native installation and basic extraction have been observed; complete acceptance is still being tested.
The installer form must supply the selected directory and OCR value to the bundled executable as separate arguments.
The manifest's distinct name preserves the historical extension and the separate manually registered connector.
Avoid enabling both OpenReading connectors in the same test conversation, since that makes runtime attribution ambiguous.

Start a new Chat conversation with this extension enabled. Use a synthetic document in the selected directory.
Ask for an exact quote with its physical page, evidence ID and text origin, then inspect the import/search/read calls.
The MCP server supplies the current pinned core instructions during initialization.
WORKFLOW.md is an included review copy; its presence in the archive does not prove the model received a skill.

Changing the directory or OCR setting requires the host to restart the server. Start a new Chat and confirm the resulting import description before testing.
Source copies remain under the separate Claude Desktop v2 artifact directory until removed.
For an existing manual v2 connector using the same grant, this candidate uses that client's same artifact namespace; it does not delete or migrate those records.
The selected directory limits only OpenReading tools. Requested document content enters your assistant's context.

To remove this candidate, disable/uninstall its own extension entry and stop its worker.
Retained data is separate under `~/Library/Application Support/OpenReading/agent-tools/claude-desktop/v2/artifacts/`.
Do not delete that directory while another OpenReading Desktop connector uses it.

> **OpenReading Managed: Coming soon**
>
> Document processing on OpenReading's servers, without managing local compute.
> Planned after the public OSS launch.

This is static presentation only. No managed connection or signup flow is included.

The `25c15c4` candidate introduced `openreading_get_document` for the complete retained normalized result, excluding raw provider payloads.
Search remains optional. Requested document content enters the assistant context; full retrieval can include all extracted text.
The profile still controls available channels, including its table limitations.
Updated frozen and native checks remain separate from the historical observations above.

Background imports use `openreading_start_import`, `openreading_get_import`, and `openreading_cancel_import`.
The next manifest adds `openreading_list_imports` to recover IDs after reconnecting.
It requires a refreshed core pin and package; the existing built candidate does not expose it.
Cancel unwanted jobs and wait for terminal status before uninstalling; client removal does not stop detached work.
The job survives a chat disconnect and exposes actual stage, elapsed time and its final artifact receipt.
Use explicit job cancellation to stop processing; host Stop alone does not cancel it.
This candidate removes prototype document-size, page-count, extraction-size, storage and elapsed-time caps.
No local memory cutoff stops processing. Large-document accuracy and native progress UI require separate checks.
