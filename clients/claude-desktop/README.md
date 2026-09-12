# Claude Desktop local preview

**Revision status:** this guide separates current Docling developer checks from the historical revision 1 PyMuPDF package.
The Docling developer harness is implemented; the [assistant migration](../../design/assistant-clients.md) and Docling client distribution remain proposed.
See the [client matrix](../README.md) for the limits of existing evidence.
Existing setup commands and test results below do not establish revision 2 compatibility.

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
