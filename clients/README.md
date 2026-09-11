# Client compatibility

OpenReading has one proposed Docling runtime and separately tested client connections.
The [assistant design](../design/assistant-clients.md) defines the pending migration and its evidence requirements.
Historical revision 1 packages do not establish Docling compatibility.

## Documented routes

Checked on 2026-09-11. These are connection candidates, not a supported-client release list.

| Surface | Documented local route | Current Docling evidence |
| --- | --- | --- |
| Claude Desktop | Local MCP desktop extension. | Native Docling installation and invocation pending. |
| ChatGPT desktop on a local Codex host | STDIO MCP registration in desktop settings or shared host configuration. | Native UI, launch, and invocation pending. |
| Claude Code | Local STDIO registration; the existing prototype also has a plugin wrapper. | CLI syntax checked; native Docling invocation pending. |
| Codex CLI | Local STDIO registration; the existing prototype also has a plugin wrapper. | CLI syntax checked; native Docling invocation pending. |
| ChatGPT web or mobile | Outside this local proof. | No compatibility claim. |

[Anthropic's local MCP guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop) describes desktop extensions and their setup.
[Claude Code's MCP guide](https://code.claude.com/docs/en/mcp) documents local STDIO registration.
[OpenAI's MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) documents local processes in ChatGPT desktop and Codex, including shared host settings.
Its web path is distinct from local desktop configuration; do not infer web support from a desktop registration.

## What has been checked

The pinned Docling candidate completes an independent SDK STDIO initialization and tool-list probe.
It exposes `openreading_import`, `openreading_search`, and `openreading_read` and refuses an outside-directory import.
This check uses no native host and invokes no model.
The [measurement guide](../measurement/README.md) records the separate retrieval and restart checks.

The connection investigation found Claude Code 2.1.267 and Codex CLI 0.153.4 supporting local command registration in their installed help.
It found Claude Desktop 1.52386.0 and ChatGPT desktop 26.901.51231 installed on the developer machine.
App presence does not establish the required settings, permissions, launch, or tool use.
The computer-use tool refused inspection of ChatGPT desktop, so its UI check remains pending.
No host configuration was changed, package installed, or model trial executed during this investigation.

## Per-client guides

- [Claude Desktop](claude-desktop/README.md): historical package walkthrough and pending host checks.
- [ChatGPT desktop](chatgpt/README.md): documented connection candidate and remaining verification.
- [Claude Code](claude-code/README.md): historical marketplace and configuration evidence.
- [Codex](codex/README.md): historical package and configuration evidence.

Every future compatibility entry must name the tested runtime, application version, execution mode, and actual result.
API measurement, protocol smoke, and native installation remain separate evidence.
