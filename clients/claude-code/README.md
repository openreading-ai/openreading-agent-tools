# OpenReading for Claude Code

This macOS Apple Silicon candidate connects Claude Code to an OpenReading Core server you run separately.
The package includes Python and both local MCP connectors. It includes no bundled parser, models or runtime download.
Claude Code starts the tools as local processes. Desktop device activation is not part of this connection.

## Install

Install through Claude Code's plugin marketplace. The development candidate currently lives on its feature branch:

~~~text
/plugin marketplace add openreading-ai/openreading-agent-tools@feat/server-only-plugin
/plugin install openreading-local-documents@openreading-local
/reload-plugins
~~~

Claude Code downloads the complete plugin and owns its cached installation. No folder copying or state reset is required.
This candidate supports macOS Apple Silicon and requires Claude Code 2.1.238 or later.
The repository is private. Use an existing GitHub CLI login with repository access, and have `gh` and `jq` on PATH.
Accept the installer prompt that retrieves GitHub authorization for the pinned private release download.
The helper sends authorization only to GitHub's API. Claude Code drops that header before following an off-origin asset redirect.
The marketplace pins the archive's SHA-256 digest. Installation refuses an altered archive.

The same installation from a terminal uses `claude plugin marketplace add` and `claude plugin install`.
The marketplace name remains `openreading-local`, so this replaces the former local marketplace source.
If that plugin is already installed, use `/plugin update openreading-local-documents@openreading-local`, then `/reload-plugins`.
The development branch is not the public release channel. Signing and clean-machine acceptance remain pending.

Run `/mcp` inside Claude Code. The plugin supplies `openreading` and `openreading-settings`.
Run `/openreading-local-documents:openreading-settings` to open the native Settings window.
Enter the URL of your running local Core server, test the connection, and save the destination.
For example, use `http://127.0.0.1:7777` only when Core listens on port 7777.
Enter a bearer token only if your server requires one. A connection check does not test document parsing.
Exit this Claude Code session and start `claude` again after saving configuration.

Ask to open the OpenReading file picker, select a test document, then choose Process.
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
Existing Keychain entries may remain. Fresh preferences do not reference them.

To uninstall this candidate:

~~~sh
claude plugin uninstall openreading-local-documents@openreading-local --scope user
claude plugin marketplace remove openreading-local
~~~

Removal preserves retained data. Restore a backup only after exiting Claude Code and moving new test data aside.

## Build and acceptance

From the Agent Tools repository, reuse the verified server-only runtime:

~~~sh
python -m runtime.build_server --client claude-code --runtime /absolute/path/to/runtime --output /absolute/path/to/new-build
~~~

The generated `package` directory remains a local development marketplace. Its `build.json` records client, worker, Core and archive identities.
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
