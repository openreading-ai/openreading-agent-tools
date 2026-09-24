# OpenReading for Claude Desktop / Cowork

This Apple Silicon alpha.23 review candidate connects Cowork to a Core server you run separately.
It embeds the connector runtime and no parser, OCR executable, model or runtime downloader.
Install from GitHub through Claude's personal marketplace controls. Other platform binaries remain pending.

## Install from GitHub

1. Open Cowork, then Customize, Plugins, the Personal plugins plus button, and Add marketplace.
2. Choose Add from a repository and enter `https://github.com/openreading-ai/openreading-agent-tools`.
3. Sync the marketplace and install **openreading-cowork**, not the Claude Code entry named openreading.
4. Enable both connectors, start a fresh Cowork task, and run `/openreading-settings`.
5. Save and test your Core URL. Quit and reopen Claude, select a synthetic document, and choose Process.

This revision pins the alpha.23 security-review candidate. Independent review and exact-build native acceptance remain pending.
Use the main repository after the owner merges that build's catalog PR. Do not substitute a ZIP or local folder.
The repository remains private. Authorize the app's GitHub access if requested; never put a token in chat or the repository URL.
Review the requested repositories and permissions before authorizing. Record the exact scope for acceptance review.
If the prompt requests access you do not intend to grant, stop instead of broadening access for this test.
See [Claude's personal marketplace instructions](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).

The new desktop identity separates Cowork from Claude Code in the shared catalog.
Disable the older uploaded OpenReading plugin in Cowork before enabling this one, without deleting its data.
The launcher retains the `claude-desktop` storage partition, so saved settings and retained results remain available.
Refresh the GitHub marketplace and use the host's update control for later versions. Restart Claude after an update.

Claude may require connecting this computer before its local plugin tools become available.
The plugin includes the `openreading` and `openreading-settings` skills, nine document tools and a Settings opener.
The [Core setup guide](https://github.com/openreading-ai/openreading-agent-tools/blob/main/clients/full-core/README.md#run-core-for-the-connector) explains the separate server.
Localhost permits HTTP. Remote destinations require HTTPS. This connector sends no credentials.

Verify GitHub sync, installation, updates, exact cited evidence and background-job recovery before accepting this build.
Native Cowork acceptance and clean-machine installation remain pending for alpha.23.
Removing the plugin preserves preferences, selected copies and retained results in the Claude Desktop partition.
Cancel unwanted jobs before removal. Never remove another client's data to reset this one.
Follow [Remove retained data](../../SECURITY.md#remove-retained-data) for Cowork's `claude-desktop` partition and settings.

## Historical evidence below

These records identify older binaries and different installation routes.
They do not provide installation instructions or acceptance evidence for the current GitHub connector.

## Historical Claude Desktop local previews

Launch scope: [OSS product v1](../../design/oss-launch.md) exposes the full implemented MCP catalog of its pinned core through the slim Docling runtime. Managed product v2 comes after launch; only a static “Coming soon” visual is planned. Historical profile/settings version 2 does not mean managed processing.

**Revision status:** this guide separates current Docling developer checks from the historical revision 1 PyMuPDF package.
The Docling developer harness is implemented; the [assistant migration](../../design/assistant-clients.md) and Docling client distribution remain proposed.
See the [client matrix](../README.md) for the limits of existing evidence.
Existing setup commands and test results below do not establish revision 2 compatibility.

## File-selection candidate

The separate [file-selection guide](selection/README.md) uses **Choose document → Copy reference → Paste into chat**.
Its generated manifest has only the OCR setting; it does not request a directory or replace existing connector settings.
The frozen helper has been exercised with the native file dialog and direct MCP import/search/read on this development machine.
This does not establish an installed assistant integration or clean-machine acceptance for the new package.

## Docling installation candidate

The distinct `openreading-docling-local-preview` package uses the format-2 frozen runtime.
It requires a document directory and exposes a boolean **Read scanned text (OCR)** option, defaulting to off.
The historical manifest remains a separate PyMuPDF prototype.

OCR text can differ from the printed page, including letters and digits in identifiers.
Exact search may miss those identifiers; verify important OCR quotes against the source page.
Citation checks verify extracted text and provenance, not OCR transcription accuracy.

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

The current candidate pins core `3ff02d415ca5389093c2ea16b54e1ec65caa015c`, including the optional local selection tool.
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

The [historical package guide](historical/README.md) describes its setup and retention separately.
Only that guide ships with the revision 1 Desktop archive.

### Investigating a slow answer

Use the [Desktop timing diagnostic](../../measurement/README.md#desktop-timing-diagnostic) on this connector's existing compact log.
It distinguishes logged tool-call intervals from gaps between calls without exporting document payloads.
An interval is not pure parsing time, and a gap is not proof that the model was thinking.
Do not combine logs from the manual connector and the packaged extension.

### Synthetic native timing and interruption

A separate temporary probe ran in Claude Desktop 1.52386.3 Chat on 2026-09-13.
The installed MCPB used probe source from commit `d2e939d` and the developer virtual environment’s Python, not the frozen worker.
It loaded no document engine; its startup timing does not measure frozen runtime startup.
These single-machine observations do not establish another host's behavior or the public picker experience.

- A deliberately delayed **Allow once** click preceded both the compact-log tool request and the local server receipt. The two-second call interval excluded that approval pause.
- A 65-second call completed without progress. A requested 330-second call received MCP cancellation at approximately 240 seconds, and the UI reported a four-minute timeout.
- **Stop response** interrupted the chat but sent no MCP cancellation in a separate 120-second call. The local operation completed at 120 seconds, roughly 84 seconds after Stop.
- The prompt requested progress every five seconds, but the retained probe log omitted the received interval and token presence. No progress events were recorded. Deadline extension and absolute versus inactivity timeout remain unverified.
- A subsequent echo returned correctly. Uninstalling the temporary probe removed both observed probe processes and restored the original configuration and extension registry bytes.

The host timeout and the Stop button are distinct interruption paths.
A public picker still needs its own bounded lifetime and local cancellation action.
Do not claim that stopping a chat dismisses its picker or stops parsing without corresponding protocol evidence.
The Docling import cancellation, native picker focus and complete citation-capture checks remain separate.

A separate twelve-second native rerun used temporary probe package 0.0.2 with explicit interval and token-presence logging.
The server received seconds 12 and progress_every 2, with progress_token_present false, and completed without progress events.
This verifies absent token delivery for that call, not for every host invocation.
The probe was removed again, both processes exited, and the original configuration and extension registry bytes were restored.
The four-minute observation remains a no-progress limit; absolute versus inactivity timeout is unresolved.

## Chat-driven selection candidate

The [chat chooser](chat/README.md) uses a separate package name and no setup fields.
Build it with `runtime.package --docling-desktop --chat-documents` against the current candidate runtime.
It returns the selected reference through core's MCP tool and enables local OCR automatically.
Existing installed development extensions and native observations remain tied to their original binaries.

The `25c15c4` candidate introduced `openreading_get_document` for the complete retained normalized result, excluding raw provider payloads.
Search remains optional. Requested document content enters the assistant context; full retrieval can include all extracted text.
The profile still controls available channels, including its table limitations.
Updated frozen and native checks remain separate from the historical observations above.
