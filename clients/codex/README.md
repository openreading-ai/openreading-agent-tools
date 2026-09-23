# OpenReading for Codex

Select documents and use retained results through your separately running OpenReading Core server.
This Apple Silicon development package includes the connector runtime, file picker, settings and document tools.
It includes no parser, model download, Core server, adapter catalog or server manager.

Core setup is documented in the [separate server guide](../full-core/README.md#run-core-for-the-connector).
Only macOS Apple Silicon binaries are available for this preview. Other platforms remain pending.

## Install and test

Extract `OpenReading-Codex-Plugin.zip` into a permanent folder, such as `~/Downloads/OpenReading-Codex-alpha21`.
Install through Codex's native marketplace commands:

```sh
codex plugin marketplace add "$HOME/Downloads/OpenReading-Codex-alpha21"
codex plugin add openreading@openreading
```

Start a new local Codex thread to load the installed plugin.
Ask to open OpenReading settings, then enter your Core server URL, test the connection and save.
Start Core separately. Localhost permits HTTP; remote destinations require HTTPS.
Quit and reopen Codex after saving settings, then ask to open OpenReading and select a document.
Choose Process when the assistant reports the selection is ready, or Add more to extend it.
Ask a question and verify the returned evidence against the document.

The plugin provides `openreading` and `openreading-settings` skills, nine document tools and one settings opener.
The host may display qualified skill names such as `openreading:openreading-settings`.
Codex owns tool permissions. OpenReading's native chooser and confirmation select which files go to the configured server.
Server failure never switches to a local parser or automatically resubmits a document.
After a stopped selection, choose and confirm the remaining files again before retrying.

## State, updates and removal

The launcher fixes its client label to `codex`. Settings and retained files survive plugin replacement or removal.
Codex preferences live under `~/Library/Application Support/OpenReading/agent-tools/codex`.
The default retained-data partition is `~/.openreading/clients/codex/v2`; Storage settings can select another location.
Claude's settings and data partitions are separate. Installing this package does not register the ChatGPT Work client.

Keep the extracted marketplace folder available for reinstalling or upgrading.
Install a newer package through the same host commands and start a new thread.
Remove this plugin with `codex plugin remove openreading@openreading`.
That command removes the installed plugin, not your OpenReading settings, selected copies or retained results.

## Build and verification

Reuse the verified server-only runtime matching the package version:

```sh
python -m runtime.build_server --runtime /path/to/verified-runtime --client codex --output /path/to/new-build
```

The output contains `package/.agents/plugins/marketplace.json`, `package/plugins/openreading`,
`package/OpenReading-Codex-Plugin.zip` and `package/build.json` with archive and worker hashes.
The ZIP contains the complete marketplace. No manual MCP configuration or separately installed Python is required.

Historical alpha.19 evidence: Codex CLI 0.155.1 installs this package through its native marketplace flow in an isolated configuration.
Its app server discovers both skills, nine document tools and the settings opener from the installed cache.
The installed worker passes synthetic localhost processing, retained retrieval, export hashing and job recovery checks.
Stopping Core fails. The old selection stays refused after Core restarts, and a new selection succeeds.
Those checks inject the chooser and native confirmation. No model turn or personal document is used.
Manual native settings, chooser, document answers and lifecycle acceptance remain separate checks.
Remote HTTPS, clean-machine prerequisites, signing and notarization remain pending.
