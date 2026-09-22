# OpenReading for ChatGPT Work

Select local documents and process them through your separately running OpenReading Core server.
This Apple Silicon plugin includes the same alpha.19 connector worker tested with Claude and Codex.
It includes no parser, model download, Core server, adapter catalog or server manager.

## Install as a plugin

Open ChatGPT's **Plugins** view and its **New Plugin** upload dialog.
Choose `OpenReading-ChatGPT-Plugin.zip`, then select **Add plugin**.
Upload the ZIP directly. No extraction, Terminal command or marketplace registration is required by this workflow.
The archive places `.codex-plugin/plugin.json`, `.mcp.json`, skills and runtime at the plugin root.
The uploader accepts archives up to 100 MB. This build is approximately 21 MB.

The earlier marketplace-wrapped ZIP was rejected by the uploader.
This corrected archive's structure and extracted connectors are checked locally.
Acceptance by the upload service and tool availability in a Work conversation remain manual checks.

Start a new **Work** conversation on this Mac. Enable this plugin and ask to open its OpenReading settings.
Enter your Core URL, test the connection and save. Start Core separately.
Localhost permits HTTP; remote destinations require HTTPS.
After changing saved settings, quit and reopen ChatGPT, then start a new Work conversation.
Ask OpenReading to select a document, choose Process, and ask a question about the extracted content.

The two skills are `openreading` and `openreading-settings`, qualified by the `openreading-chatgpt` plugin name.
Its connectors are `openreading-chatgpt` and `openreading-chatgpt-settings`.
Use the installed plugin's settings tool directly. Opening a guessed standalone OpenReading application is unnecessary.

## Shared host configuration

ChatGPT and Codex can share installed plugins and enablement settings on this Mac.
This candidate uses a separate plugin identity so installation does not replace the working Codex package.
For an unambiguous test, enable only **OpenReading for ChatGPT** in the conversation, not both OpenReading variants.
If the host only offers a global toggle, disabling the Codex variant also affects future Codex sessions until you enable it again.
A plugin name does not enforce isolation between applications.

This launcher's fixed client label is `chatgpt`. Preferences live under `~/Library/Application Support/OpenReading/agent-tools/chatgpt`.
The default retained-data partition is `~/.openreading/clients/chatgpt/v2`. Storage settings can select another location.
The launcher does not migrate or overwrite Codex or Claude preferences.
Existing historical ChatGPT preferences remain readable. An old bundled-parser selection requires saving a Core server URL.

## Build and verification

Reuse the verified server-only runtime without rebuilding its executable:

```sh
python -m runtime.build_server --runtime /path/to/verified-runtime --client chatgpt --output /path/to/new-build
```

The output contains a development marketplace, plugin directory, standalone upload ZIP and `build.json` recording the worker and archive hashes.
Installation and protocol checks use isolated settings and synthetic documents, without model calls or personal files.
The native Work conversation, settings window, picker and answer workflow require owner-operated testing.
Ordinary Chat, web, cloud execution, clean-machine prerequisites, signing and notarization are not established by those checks.

## Removal

Remove **OpenReading for ChatGPT** through ChatGPT's plugin controls.

Removal deletes the installed package, not OpenReading preferences, copied documents, jobs or retained exports.
Keep the upload ZIP available for another manual installation.
