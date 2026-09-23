# OpenReading for Claude Code

This macOS Apple Silicon candidate connects Claude Code to an OpenReading Core server you run separately.
The package includes Python and both local MCP connectors. It includes no bundled parser, models or runtime download.
Claude Code starts the tools as local processes. Desktop device activation is not part of this connection.

Core setup is documented in the [separate server guide](../full-core/README.md#run-core-for-the-connector).
Only macOS Apple Silicon binaries are available for this preview. Other platforms remain pending.

## Install

Install through Claude Code's plugin marketplace. For a first installation, use the commands below.
Extract `OpenReading-Claude-Code-Local-Marketplace.zip` into a permanent folder before installing this preview:

~~~text
/plugin marketplace add /absolute/path/to/extracted-marketplace
/plugin install openreading@openreading
/reload-plugins
~~~

Claude Code downloads the complete plugin and owns its cached installation. No folder copying or state reset is required.
This candidate supports macOS Apple Silicon and requires Claude Code 2.1.238 or later.
This local preview needs no GitHub download helper. The repository marketplace remains the historical alpha.19 checkpoint.
Do not use that remote marketplace to test alpha.21.

From a terminal, run `claude plugin marketplace add /absolute/path/to/extracted-marketplace`, then `claude plugin install openreading@openreading`.
If the historical marketplace is already registered, remove only its registration before adding this preview's location.
The plugin and marketplace are both named `openreading`.
For an upgrade from alpha.17, first run these commands in your terminal, then use the installation commands above:

~~~sh
claude plugin uninstall openreading-local-documents@openreading-local --scope user
claude plugin marketplace remove openreading-local
~~~

Claude Code otherwise reuses the old marketplace registration for the same repository and branch.
Removing these registrations preserves your Claude Code server settings and retained documents.
If that plugin is already installed, use `/plugin update openreading@openreading`, then `/reload-plugins`.
The development branch is not the public release channel. Signing and clean-machine acceptance remain pending.

Run `/mcp` inside Claude Code. The plugin supplies `openreading` and `openreading-settings`.
Run `/openreading-settings` to open the native Settings window.
Enter the URL of your running local Core server, test the connection, and save the destination.
For example, use `http://127.0.0.1:8787` when Core uses its default port.
Connections use only the URL. Servers requiring client authentication are not supported.
A connection check does not test document parsing.
Exit this Claude Code session and start `claude` again after saving configuration.

Run `/openreading`, select a test document, then choose Process.
These are the only two commands: `/openreading` and `/openreading-settings`.
Claude Code may display their qualified names, `/openreading:openreading` and `/openreading:openreading-settings`.
The explicit skill names also register the short forms unless another command owns that name.
Expect a `/v1/parse` request in your Core log and a completed import receipt.
Ask a question and verify the cited evidence. Selected files remain queued until you choose Process.
If the server is unavailable, start it and reselect the document before retrying processing.
No failed request falls back to a bundled parser.

## Optional fresh-state testing and removal

Ordinary installation preserves settings and documents. Backups below are only for an explicit fresh-state test.

First inspect `/mcp` in the project where you previously tested OpenReading.
Remove obsolete OpenReading registrations from their original scope. Leave unrelated servers and plugins intact.
The old marketplace plugin, when present, is `openreading-local-proof@openreading-local-review`.
Uninstall that entry before installing this candidate. No input directory configuration is required by the new package.

After exiting Claude Code, rename these Claude Code folders to unused backup names before a fresh-state test:

- `~/Library/Application Support/OpenReading/agent-tools/claude-code`
- `~/.openreading/clients/claude-code`

Skip absent folders. Preserve backups until testing finishes. A previously chosen custom storage folder needs its own backup.
Never rename the `claude-desktop` partitions. This package keeps Desktop settings and documents separate.

To uninstall this candidate:

~~~sh
claude plugin uninstall openreading@openreading --scope user
claude plugin marketplace remove openreading
~~~

Removal preserves retained data. Restore a backup only after exiting Claude Code and moving new test data aside.

## Build and acceptance

From the Agent Tools repository, reuse the verified server-only runtime:

~~~sh
python -m runtime.build_server --client claude-code --runtime /absolute/path/to/runtime --output /absolute/path/to/new-build
~~~

The generated `package` directory and `OpenReading-Claude-Code-Local-Marketplace.zip` contain the local preview marketplace. Its `build.json` records client, worker, Core and archive identities.
The repository marketplace installs `OpenReading-Claude-Code-Marketplace.zip` through Claude Code's native archive source.
For a new release, upload the ZIP to the private GitHub release and update the marketplace asset URL, digest and version together.
Keep both MCP definitions identical to the packaged `.mcp.json`. The archive includes all dependencies; its launcher downloads nothing.
The private download helper requires `strict: false`, so the marketplace explicitly declares the skills and both MCP connectors.
The marketplace archive omits both `plugin.json` and `.mcp.json`. Claude Code 2.1.278 treats even an identity-only manifest as a conflict.
The ordinary local marketplace and Desktop ZIP retain their manifests.
When distribution becomes public, use the public asset URL and remove the private download helper and headers.
The worker is shared with Desktop, but each host needs independent native workflow acceptance.
Native manual testing, clean-machine prerequisites, signing and notarization remain release gates.
The files in `historical/` are inputs to the old prototype assembler, not this install route.
