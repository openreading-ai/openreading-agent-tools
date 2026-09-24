# OpenReading for ChatGPT Work

Install the Apple Silicon connector from a GitHub-backed personal marketplace.
It includes the connector interpreter, two skills, nine document tools and one Settings opener.
It includes no parser, model, Core server or runtime downloader. Other platforms remain pending.
Start [OpenReading Core separately](https://github.com/openreading-ai/openreading-agent-tools/blob/main/clients/full-core/README.md#run-core-for-the-connector).

## Personal-account installation

Register the GitHub marketplace once using Codex CLI. During PR review, select the preview branch:

~~~sh
codex plugin marketplace add openreading-ai/openreading-agent-tools --ref fix/github-marketplaces
~~~

After the owner merges that PR, new installations omit `--ref fix/github-marketplaces`.
Your Git credentials must permit access while the repository remains private.
Quit and reopen ChatGPT Desktop, open Plugins, select the OpenReading marketplace and install **OpenReading for ChatGPT**.
Its plugin identifier is `openreading-chatgpt@openreading`. Do not choose the Codex entry named OpenReading.
No workspace-admin import, manual clone, ZIP upload or extracted folder is part of this route.

OpenAI documents personal marketplaces in Work and GitHub registration through the CLI.
Exact-build visibility and installation in the personal-account desktop UI remain owner-operated acceptance checks.
CLI installation and tool discovery do not establish a successful Work conversation.
See [OpenAI's marketplace instructions](https://developers.openai.com/plugins/build/plugins).

Start a new local Work conversation and enable only the ChatGPT variant.
Ask to open OpenReading settings. Save and test your Core URL, then quit and reopen ChatGPT.
Select a synthetic document, choose Process and verify the answer against its evidence.
Use the plugin's Settings tool, not a guessed standalone application.

## Updates and removal

Run `codex plugin marketplace upgrade openreading`, then update the ChatGPT plugin through Plugins and restart ChatGPT.
The CLI can also install the selected package with `codex plugin add openreading-chatgpt@openreading`.
A preview registration follows its selected branch. Register with `--ref main` after the review branch is merged.
Remove **OpenReading for ChatGPT** through its plugin controls. Cancel unwanted background jobs first.

ChatGPT and Codex can share plugin configuration. A plugin name does not enforce application isolation.
The launcher keeps the `chatgpt` partition and does not migrate or overwrite another client's data.
Preferences live under `~/Library/Application Support/OpenReading/agent-tools/chatgpt`.
Retained data defaults to `~/.openreading/clients/chatgpt/v2`; Storage can select another folder.
Updates and removal preserve preferences and retained results.

## Verification boundaries

The [build guide](https://github.com/openreading-ai/openreading-agent-tools/blob/main/runtime/server_client/README.md) records the Git distribution and immutable runtime identity.
Native Work settings, chooser, answers, reconnect and update behavior require their own exact-build checks.
Ordinary Chat, web/mobile, cloud execution, clean-machine installation, signing and notarization are not established by CLI checks.
