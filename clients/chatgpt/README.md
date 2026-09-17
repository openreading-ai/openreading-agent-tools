# ChatGPT desktop integration

Launch scope: [OSS product v1](../../design/oss-launch.md) exposes the full implemented MCP catalog of its pinned core through the slim Docling runtime. Managed product v2 comes after launch; only a static “Coming soon” visual is planned. Historical profile/settings version 2 does not mean managed processing.

**Status:** owner-operated Work tests passed through manual STDIO registration on September 17, 2026. Packaged installation and ordinary Chat acceptance remain pending.
The [client matrix](../README.md) separates documented routes from tested behavior.

## Connection candidate

[OpenAI's MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) describes adding a local STDIO server through ChatGPT desktop settings.
It also describes configuration shared with Codex clients on the same host.
Check the installed application and execution mode before following that route.
A shared registration can expose the same OpenReading internal intake grant to multiple local clients.
That grant limits only OpenReading; it does not restrict the assistant's other file or shell tools.
The route must execute locally and cannot set `experimental_environment = "remote"`.

The desired target is a local Chat conversation, with Work and Codex local threads checked separately in [E1](../../design/native-probes.md).
A Codex-thread pass does not establish support for Chat conversations.
The proposed signed setup helper shows an argument-free executable path for host registration.
Public document selection uses A1's chat-invoked local picker and returns the selected reference automatically.
The proposed helper does not edit shared TOML. The owner tested a native STDIO form with separate arguments and an existing development worker.
Argument-free setup, paths containing spaces or Unicode, and the complete shared-configuration delta remain unverified.
Public setup asks for neither a document directory nor an OCR decision. Bundled OCR works automatically within its verified limits.
Pasting the executable path registers the host; it is not per-document reference copying.
E1 must establish the named Chat mode, E2 its deadlines, and A1 the native handoff before implementation acceptance.
The [assistant design](../../design/assistant-clients.md) owns the pending setup interface and grant rules.
No copy-and-paste installation command is provided until the corresponding artifact exists and its native launch is tested.

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
