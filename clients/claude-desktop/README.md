# Claude Desktop local preview

Launch scope: [OSS product v1](../../design/oss-launch.md) exposes the full implemented MCP catalog of its pinned core through the slim Docling runtime. Managed product v2 comes after launch; only a static “Coming soon” visual is planned. Historical profile/settings version 2 does not mean managed processing.

**Revision status:** this guide separates current Docling developer checks from the historical revision 1 PyMuPDF package.
The Docling developer harness is implemented; the [assistant migration](../../design/assistant-clients.md) and Docling client distribution remain proposed.
See the [client matrix](../README.md) for the limits of existing evidence.
Existing setup commands and test results below do not establish revision 2 compatibility.

## Docling installation candidate

The distinct `openreading-docling-local-preview` package uses the format-2 frozen runtime.
It requires a document directory and exposes a boolean **Read scanned text (OCR)** option, defaulting to off.
The historical manifest below remains a separate PyMuPDF prototype.

After building the runtime using the [P0 guide](../../runtime/p0/README.md), choose fresh output paths:

~~~sh
uv run --frozen --project runtime --all-groups python -m runtime.package \
  --runtime /absolute/docling-runtime --output /absolute/desktop-candidate --docling-desktop
node_modules/.bin/mcpb validate /absolute/desktop-candidate/manifest.json
node_modules/.bin/mcpb pack /absolute/desktop-candidate /absolute/openreading-docling-desktop.mcpb
~~~

The official MCPB 2.1.2 resolver preserves the chosen directory as one argument and renders the OCR boolean as `true` or `false`.
Tests include spaces, Unicode and shell metacharacters. The launcher interprets these as arguments, never a shell command.
The package records runtime identity plus manifest/workflow hashes and preserves the runtime's complete inventory.
`WORKFLOW.md` is a review copy; the pinned core supplies the actual MCP initialization instructions.
No skill-delivery claim follows from copying that file into an archive.

The refreshed candidate pins core `e12c2fd3d4761b2349051861e6d57da91aa0e7d1` for current bounded-evidence instructions.
Its dependency versions and Docling integration remain unchanged from the preceding candidate.
The packed/unpacked archive passes native/OCR imports, warm reuse, restart, exact citations and same-profile catalog/instruction comparison against direct core.
This is development-machine protocol evidence, not a Desktop conversation or clean-machine pass.

On Claude Desktop 1.52386.3, the owner installed and enabled the archive through the native installer.
The actual form saves a directory and boolean OCR setting. Claude launches the installed bundled executable and completes MCP initialization and tool discovery.
Native Chat checks retrieved the synthetic renewal quote on physical page 3 and the scanned payment quote on physical page 2 with an OCR label.
With OCR off, the payment search returned no evidence; enabling OCR produced a distinct artifact and readable payment evidence.
These are partial native observations. Complete transcript capture, the document-instruction read, native access refusal, cancellation and clean-machine acceptance remain unfinished.
The native tool viewer virtualizes long payloads; an incomplete UI capture cannot satisfy the deterministic citation check.
The declared document grant restricts OpenReading tools; it is not an operating-system sandbox around the extension.
This directory configuration belongs to the development candidate. It does not establish the public file-selection experience.

For the local check, open the archive in Claude Desktop and confirm installation only for your reviewed candidate.
Choose a synthetic document directory, keep OCR off for the initial native-text case, and enable this connector in a new Chat.
Keep the older manual OpenReading connector out of that test conversation to avoid ambiguous tool attribution.
Verify the import description names Docling and the selected OCR setting, then inspect a cited answer and an outside-grant refusal.
Repeat with OCR enabled and the raster fixture. Start a new Chat after configuration changes so previously loaded descriptions do not carry stale settings.
Preserve existing registrations and their retained data.
This candidate still requires distribution review and signing before sharing it with another user.

## Docling developer check

The owner manually registered the P0 Docling worker and supplied partial Chat-mode evidence on 2026-09-11.
The worker reported release `0.2.0-p0`, core `7d97b75`, and SHA-256 `a4cc0054cd57ddd77538c7cda3bdd220c1fe7a3cfa636e55f5a2e716bfca236b`.
This is an unsigned development-machine observation. The exact app version and process ancestry were not captured for these calls.
It does not establish extension installation, nondeveloper setup, a complete native acceptance pass, or token savings.

The manual registration uses one connector containing import, search, and read.
The owner edited `~/Library/Application Support/Claude/claude_desktop_config.json` through Settings, Developer, Edit Config.
Preserve existing entries and add a server using your verified candidate and synthetic document directory:

~~~json
{
  "mcpServers": {
    "openreading-docling-test": {
      "command": "/absolute/frozen-runtime/openreading-worker",
      "args": [
        "--client", "claude-desktop",
        "--input-root", "/absolute/synthetic-documents",
        "--ocr", "off"
      ]
    }
  }
}
~~~

The paths above are placeholders. Use the P0 build you verified, rather than the historical MCPB below.
Save, fully quit Desktop, reopen it, and enable the connector in a new Chat conversation.
Change the argument after `--ocr` to `on` and restart the app for the separate OCR-enabled check.
These manual JSON steps do not satisfy the planned nondeveloper setup criterion.

| Owner-supplied observation | Evidence limit |
| --- | --- |
| Agreement renewal quote matches physical page 3 and native origin. | Pasted read payload supports the main quote; complete call capture is unavailable. |
| Outside-directory import returns `access_denied`. | Raw error confirms the refusal; a full fallback-tool trace is unavailable. |
| Repeated read returns the same artifact, evidence and quote. | Full quit/reopen was requested but not separately attested or traced. |
| OCR off gives no readable page-2 invoice evidence; OCR on returns 45 days on page 2, labeled `ocr`. | The OCR-on raw read supports the quote and provenance; the search result was not pasted. |

The OCR-off answer guessed evidence IDs, which the tools refused.
The shared workflow and core MCP instructions now prohibit constructing those IDs.
The installed `7d97b75` worker retains its historical instructions until a new candidate is built.
A skill file in this repository is not evidence that Desktop received or followed it.
Repeat the behavior check after delivering updated instructions through the supported native channel.

The OCR-on answer suspected a truncated prefix. The source raster and retained development extraction preserve `Scanned evidence:` as a separate passage.
Its lowercase invoice block is complete; block-relative offset zero is not truncation evidence.
The detailed development response carries `unreadable_pages`, and the fixture includes a deliberately blank page.
The generic receipt does not expose the warning cause. Do not infer it from that receipt alone.
Search is literal; reformulation helps with synonyms but does not establish comprehensive recall.

Natural source headers and citation lists are supported by explicit review format 2 in the [citation checker](../../measurement/README.md#citation-evidence-checker).
The owner screenshots and pasted payloads remain partial evidence, not a fabricated complete checker capture.
Remaining native checks include exact host identity, complete capture, cross-page and missing-fact questions, document instructions, and interruption behavior.

## Historical revision 1 package

The package contains a native stdio MCP server, so you do not start an HTTP service or install Python.
Build the candidate using the [runtime guide](../../runtime/README.md).
The manifest targets macOS on Apple Silicon and requires an explicit document directory.

## Proposed host walkthrough

This walkthrough still needs execution on a clean machine with a recorded Claude Desktop version.
Open Desktop settings, locate the extension installation interface, and select the generated `.mcpb` archive.
Choose a directory containing a synthetic PDF, then start a new chat with the extension enabled.
Ask: "Use OpenReading on agreement.pdf. What is the renewal notice period? Cite the physical page and evidence identifier."
Confirm that import, search, and read tools execute before accepting the answer as sourced.

The official MCPB validator and archive round-trip smoke pass locally.
Desktop GUI installation, quarantine behavior, and the cited-answer walkthrough remain unverified.
Do not distribute this unsigned local candidate before the license and signing gates pass.

The pinned MCPB 2.1.2 configuration resolver substitutes `${__dirname}` in `mcp_config.command`.
An offline test calls that resolver with this manifest and checks the executable path and Unicode directory argument.
The [MCPB manifest reference](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md) describes configuration substitution.
This resolves the library-level question without proving Desktop installation or launch.
Record the actual Desktop launch result, executable permissions, quarantine behavior, and startup time during the host check.
A packaging change requires an observed host failure, not a schema-validation assumption.

## Privacy and removal

The chosen folder grants access; it does not recursively import its contents.
Source copies and extracted evidence remain locally until removed.
Retrieved excerpts enter Claude's context and may be processed by its cloud model.

Desktop artifacts live under `~/Library/Application Support/OpenReading/agent-tools/claude-desktop/v1/`.
Disable or remove the extension in Desktop, stop its process, then delete that directory to remove retained copies.
The host's uninstall behavior must still be verified; retention is intentionally documented separately.
See the [runtime limits](../../runtime/README.md) before selecting a document.
