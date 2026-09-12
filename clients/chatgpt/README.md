# ChatGPT desktop integration

Launch scope: [OSS product v1](../../design/oss-launch.md) exposes the full implemented MCP catalog of its pinned core through the slim Docling runtime. Managed product v2 comes after launch; only a static “Coming soon” visual is planned. Historical profile/settings version 2 does not mean managed processing.

**Status:** proposed in ProductSpec revision 4. No Docling package or native ChatGPT walkthrough is verified yet.
The [client matrix](../README.md) separates documented routes from tested behavior.

## Connection candidate

[OpenAI's MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) describes adding a local STDIO server through ChatGPT desktop settings.
It also describes configuration shared with Codex clients on the same host.
Check the installed application and execution mode before following that route.
A shared registration can expose the same OpenReading directory grant to multiple local clients.
That grant limits only OpenReading; it does not restrict the assistant's other file or shell tools.
The route must execute locally and cannot set `experimental_environment = "remote"`.

The desired target is a local Chat conversation, with Work and Codex local threads checked separately in [E1](../../design/native-probes.md).
A Codex-thread pass does not establish support for Chat conversations.
The proposed signed helper app supplies a folder picker, saves OpenReading settings, and shows an argument-free executable path to paste into the host form.
It does not edit shared TOML. The native form and its path handling remain unverified.
Setup requires an explicit document directory and offers OCR disabled by default.
The [assistant design](../../design/assistant-clients.md) owns the pending setup interface and grant rules.
No copy-and-paste installation command is provided until the corresponding artifact exists and its native launch is tested.

## Required proof

Verify local startup and tool discovery first, then run the same synthetic cited-answer and refusal cases used for Claude Desktop.
Record exact quotes, physical pages, tool calls, restart, cancellation, permissions, and host timeouts.
The installed developer app is version 26.901.51231 with bundle identifier `com.openai.codex`.
The computer-use tool refused access to that app during the connection investigation; these native checks remain pending.
Codex CLI results cannot fill in those missing ChatGPT results.

ChatGPT web is outside this first local integration.
[OpenAI's plugin connection guide](https://developers.openai.com/plugins/deploy/connect-chatgpt) describes remote endpoint and tunnel testing paths.
Those would require a separate transport and data-access design; this proposal does not start a tunnel or expose a local service.

Local extraction keeps the retained document on the machine, while retrieved excerpts enter the calling assistant's context.
Functional success does not prove lower ChatGPT subscription usage or billing.
If the host does not expose complete task token counters, report functionality and quality without a token-savings percentage.
