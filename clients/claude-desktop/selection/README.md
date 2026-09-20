# OpenReading file-selection development candidate

Open **OpenReading Choose Document.app** from this candidate folder, then choose one local PDF.
Click **Copy reference**, paste into your assistant chat, and add your question.
The assistant imports the selected copy and retrieves cited evidence through OpenReading.
The picker does not upload the PDF or grant its containing folder.

The separate MCPB extension is **OpenReading Selected Documents (development)**.
Its only installation setting is optional OCR, off by default. It does not read your older directory-grant configuration.
Enable only the intended OpenReading connector in the test conversation to keep attribution clear.
Do not move the helper app away from its accompanying `server` directory; both belong to this development package.
This packaging layout still needs a signed installer and clean-machine usability checks before public distribution.

The picker copies selected files without fixed input or retained-byte quotas. Actual write failures refuse publication.
Source copies remain in the client's private `v2/selection/ready` directory; incomplete copies stay outside the input grant.
Cancelling the file dialog leaves the prior selection unchanged; cancelling an unfinished copy publishes nothing. A failed selection preserves any previously completed selection.
**Remove selected copy** removes only the current intake copy; already retained artifacts and delivered excerpts remain.
Copies from previous picker sessions persist. **Clear selected copies…** removes all intake copies after confirmation, including those from older sessions.
This invalidates their import references; original files and already retained evidence remain.
Force-killing the picker can leave private staging data. The next selection or cleanup operation reclaims it under the publisher lock.
Connector startup does not acquire that lock, so an ongoing copy cannot prevent tools from starting.
Artifact retention is separate from extension uninstall and selection cleanup.

Artifacts live in `~/Library/Application Support/OpenReading/agent-tools/claude-desktop/v2/artifacts/`.
That store is shared with other format-2 connectors using the `claude-desktop` client label, including the developer directory connector.
Import can therefore reuse an existing artifact; a reuse result does not establish a fresh conversion.

Retrieved excerpts enter the assistant context. OCR can misread letters and digits, so exact identifier search can miss evidence.
Citations identify extracted text and physical pages; they do not certify OCR transcription accuracy.
No provider API trials, automatic upload, managed fallback, or token-savings claim is included.
This is an unsigned development candidate. Native helper, assistant and clean-machine evidence must be recorded separately.

## Build and verify

Build a fresh runtime using the [P0 recipe](https://github.com/openreading-ai/openreading-agent-tools/blob/feat/local-document-proof/runtime/p0/README.md), then assemble this separate package:

~~~sh
uv run --frozen --project runtime --all-groups python -m runtime.package \
  --runtime /absolute/docling-runtime --output /absolute/selection-candidate \
  --docling-desktop --selected-documents
node_modules/.bin/mcpb validate /absolute/selection-candidate/manifest.json
node_modules/.bin/mcpb pack /absolute/selection-candidate /absolute/openreading-selection.mcpb
~~~

The packager requires inventoried picker sources and Tcl/Tk resources. Rebuild older runtimes before using this mode.
The official MCPB resolver is tested against both OCR values and paths containing spaces, Unicode and shell metacharacters.
Historical packages exclude this guide and helper; the directory candidate keeps its separate manifest.

## Development evidence and remaining work

The frozen picker opened the macOS file dialog, retained a selected synthetic document, and copied its reference.
Cancelling the next file-dialog selection preserved the earlier reference.
Direct frozen MCP imported the selected copy, searched renewal terms and read the exact physical-page-3 evidence.
Absolute source paths and traversal into staging were refused. No existing host configuration was changed.
This is helper and protocol evidence, not a complete native assistant conversation or installation pass.

The Tk prototype responds to keyboard navigation, but its controls were absent from the macOS accessibility tree during inspection.
Reliable pointer interaction, accessibility and the non-developer walkthrough remain public-release checks.
The co-located helper layout still needs installer integration, signing, dependency license review and a clean-machine run.
The pinned core import description still says “configured directory”; here that means the internal intake, not a folder the user must configure.
Neutral wording remains a core-owned follow-up. This package does not rewrite model-facing core descriptions.
ChatGPT mode support, host deadlines and supported document limits remain separate gates.

> **OpenReading Managed: Coming soon**
>
> Document processing on OpenReading's servers, without managing local compute.
> Planned after the public OSS launch.
