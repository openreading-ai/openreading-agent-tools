# ChatGPT desktop integration

Launch scope: [OSS product v1](../../design/oss-launch.md) exposes the full implemented MCP catalog of its pinned core through the slim Docling runtime. Managed product v2 comes after launch; only a static “Coming soon” visual is planned. Historical profile/settings version 2 does not mean managed processing.

**Status:** owner-operated Work tests passed through manual STDIO registration on September 17, 2026.
The owner later reported an exact Markdown read after plugin reinstall; independent GUI startup capture and full packaged installation acceptance remain pending.
Ordinary Chat acceptance remains pending.
The [client matrix](../README.md) separates documented routes from tested behavior.

The `0.2.0-rc.1` package targets macOS on Apple Silicon only. Intel macOS,
Linux, and Windows packages are pending. It is unsigned and does not turn the
pending host acceptance into a support claim.

## Connection candidate

[OpenAI's MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) describes adding a local STDIO server through ChatGPT desktop settings.
It also describes configuration shared with Codex clients on the same host.
Check the installed application and execution mode before following that route.
A shared registration can expose the same OpenReading internal intake grant to multiple local clients.
That grant limits only OpenReading; it does not restrict the assistant's other file or shell tools.
The route must execute locally and cannot set `experimental_environment = "remote"`.

The desired target is a local Chat conversation, with Work and Codex local threads checked separately in [E1](../../design/native-probes.md).
A Codex-thread pass does not establish support for Chat conversations.
The development plugin bundles the same verified worker and shared workflow in a local marketplace.
Its [installation guide](plugin/README.md) describes the owner-operated native check without a pasted executable path.
ChatGPT 26.911.61220's bundled CLI resolved `cwd: "."` to the installed plugin directory, leaving `./server/openreading-worker` relative.
A separate network-denied MCP process launched from that resolved configuration and passed the nine-tool check.
Native GUI startup after reinstall has not been independently captured.
The legacy plugin MCP loader leaves `${PLUGIN_ROOT}` literal in commands, so this package does not use that placeholder.
Packaging writes only its output directory. It never registers a server or changes shared host configuration.
Public setup asks for neither a document directory nor an OCR decision. Bundled OCR works automatically within its verified limits.
The earlier manual registration remains valid development evidence, separately from plugin installation acceptance.
The [assistant design](../../design/assistant-clients.md) retains native, signing and clean-machine gates.

## Assemble the development plugin

Use a verified format-2 runtime with the current delivery, selection and pageless evidence contracts:

```sh
python -m runtime.package --chatgpt-plugin --runtime /path/to/verified-runtime --output /path/to/new-marketplace
```

The output contains `.agents/plugins/marketplace.json` and `plugins/openreading-local-documents`.
The plugin contains `.codex-plugin/plugin.json`, `.mcp.json`, the shared skill and the unchanged `server` runtime.
Its package record binds the manifest, launch configuration, workflow and README to the worker and core commit.
The compatibility manifest follows [OpenAI's supported plugin packaging layout](https://developers.openai.com/plugins/build/plugins).
It is a local development marketplace, not a public directory submission or an MCPB archive.
An existing output directory or incompatible runtime is refused before copying.
The template version identifies the host cache entry; the assembler does not increment it.
Bump that version before assembling changed plugin inputs, because reusing a version can reuse an installed cache entry.

Before native testing, disable the earlier manual test connection so the result identifies the installed plugin.
OpenAI clients can share plugin configuration. Record the affected applications rather than assuming application isolation.
Plugin removal does not delete OpenReading's retained data or exports.

## Required proof

Verify local startup and tool discovery first, then run the same synthetic cited-answer and refusal cases used for Claude Desktop.
Record exact quotes, physical pages, tool calls, restart, cancellation, permissions, and host timeouts.
The earlier investigation observed version 26.901.51231 with bundle identifier `com.openai.codex`; Computer Use could not inspect its UI.
The September 17 Work test observed installed version 26.903.61454 and used owner-operated Settings screenshots and host result reports.
The [Work acceptance record](../README.md#owner-operated-chatgpt-work-checks-september-17-2026) distinguishes these reports from independent retained-file checks and remaining gates.
Codex CLI results do not replace mode-specific ChatGPT acceptance.

ChatGPT web is outside this first local integration.
[OpenAI's plugin connection guide](https://developers.openai.com/plugins/deploy/connect-chatgpt) describes remote endpoint and tunnel testing paths.
Those would require a separate transport and data-access design; this proposal does not start a tunnel or expose a local service.

Local extraction keeps the retained document on the machine, while retrieved excerpts enter the calling assistant's context.
Functional success does not prove lower ChatGPT subscription usage or billing.
If the host does not expose complete task token counters, report functionality and quality without a token-savings percentage.
