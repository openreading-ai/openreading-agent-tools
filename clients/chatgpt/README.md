# OpenReading for ChatGPT Work

Select local documents and process them through your separately running OpenReading Core server.
This Apple Silicon plugin includes the same alpha.19 connector worker tested with Claude and Codex.
It includes no parser, model download, Core server, adapter catalog or server manager.

## Install as a plugin

Extract `OpenReading-ChatGPT-Plugin.zip` to `~/Downloads/OpenReading-ChatGPT-alpha19`.
Add its marketplace with the CLI bundled inside ChatGPT:

```sh
/Applications/ChatGPT.app/Contents/Resources/codex plugin marketplace add "$HOME/Downloads/OpenReading-ChatGPT-alpha19"
```

In ChatGPT's Plugins view, choose **OpenReading for ChatGPT** and install it.
If installing from Terminal, use the same native plugin manager:

```sh
/Applications/ChatGPT.app/Contents/Resources/codex plugin add openreading-chatgpt@openreading-chatgpt
```

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

The output contains a native marketplace, plugin directory, ZIP and `build.json` recording the worker and archive hashes.
Installation and protocol checks use isolated settings and synthetic documents, without model calls or personal files.
The native Work conversation, settings window, picker and answer workflow require owner-operated testing.
Ordinary Chat, web, cloud execution, clean-machine prerequisites, signing and notarization are not established by those checks.

## Removal

```sh
/Applications/ChatGPT.app/Contents/Resources/codex plugin remove openreading-chatgpt@openreading-chatgpt
```

Removal deletes the installed package, not OpenReading preferences, copied documents, jobs or retained exports.
Keep the extracted marketplace folder available for reinstalls and updates.
