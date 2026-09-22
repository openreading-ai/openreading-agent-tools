# OpenReading for Claude Code

This macOS Apple Silicon candidate connects Claude Code to an OpenReading Core server you run separately.
The package includes Python and both local MCP connectors. It includes no bundled parser, models or runtime download.
Claude Code starts the tools as local processes. Desktop device activation is not part of this connection.

## Install

Keep the extracted marketplace directory in a stable location. Local marketplaces can load plugins from that directory.
Replace `/absolute/path/to/OpenReading-Claude-Code-alpha17` with your extracted directory before running these commands:

~~~sh
claude plugin marketplace add /absolute/path/to/OpenReading-Claude-Code-alpha17
claude plugin install openreading-local-documents@openreading-local --scope user
claude
~~~

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

## Clean testing and removal

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

The `package` directory is the local marketplace. Its `build.json` records client, worker, Core and archive identities.
The worker is shared with Desktop, but each host needs independent native workflow acceptance.
Native manual testing, clean-machine prerequisites, signing and notarization remain release gates.
The files in `historical/` are inputs to the old prototype assembler, not this install route.
