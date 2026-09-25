# OpenReading for Claude Code

Install the Apple Silicon connector through Claude Code's GitHub marketplace support.
The plugin includes its interpreter, two skills, nine document tools and one Settings opener.
It includes no parser, model, Core server or runtime downloader. Other platforms remain pending.
Start [OpenReading Core separately](https://github.com/openreading-ai/openreading-agent-tools/blob/main/clients/full-core/README.md#run-core-for-the-connector).

## Install from GitHub

These instructions target `0.2.0-alpha.24`, the replacement Apple Silicon preview.
Use them after the alpha.24 catalog PR is merged. Earlier previews do not satisfy this build's acceptance checks.
Register the main marketplace:

~~~sh
claude plugin marketplace add openreading-ai/openreading-agent-tools
claude plugin install openreading@openreading
~~~

The repository is public. Reading its marketplace and package source requires no private-repository credentials or credential-helper change.
The host fetches a complete plugin from an immutable Git commit. It uses no archive credential helper or runtime downloader.
Do not extract a ZIP, keep a checkout, or copy binaries. Choose OpenReading, not the separate Cowork entry.

If an older local marketplace named openreading is registered, inspect `claude plugin marketplace list` first.
Replace only that marketplace registration through the host's marketplace controls. Removal may uninstall its plugins.
Reinstall from GitHub afterward. OpenReading preferences and retained documents remain separate from the plugin cache.
Do not remove unrelated marketplaces or reset the client's configuration.

Start a new session and run `/mcp`. Both OpenReading connectors should connect.
Run `/openreading-settings`, save and test your Core URL, then exit and restart Claude Code.
Run `/openreading`, select a synthetic document, choose Process, and verify an answer against the source.
The host may qualify the commands as `/openreading:openreading` and `/openreading:openreading-settings`.
Selection queues documents without uploading. Add more extends that queue. Server failure never invokes a local parser.

## Updates and removal

~~~sh
claude plugin marketplace update openreading
claude plugin update openreading@openreading
~~~

Restart Claude Code after updating. Preview registrations follow their selected branch, not main.
After merge, replace the preview registration with the repository's main registration before the review branch is removed.
Uninstall only this plugin with `claude plugin uninstall openreading@openreading --scope user`.

The launcher retains the `claude-code` client label. Preferences live under `~/Library/Application Support/OpenReading/agent-tools/claude-code`.
Retained data defaults to `~/.openreading/clients/claude-code/v2`; Storage can select another folder.
Updates and removal preserve those settings and results. Cancel unwanted background jobs before removal.
Follow [Remove retained data](../../SECURITY.md#remove-retained-data) to remove this client's copies and settings safely.

## Verification boundaries

The [build guide](https://github.com/openreading-ai/openreading-agent-tools/blob/main/runtime/server_client/README.md) explains the Git distribution and exact worker identity.
GitHub install/update, cached tool discovery and synthetic processing require version-specific host checks.
Native Settings, selection, answer quality, remote HTTPS and clean-machine installation remain independent acceptance gates.
The [unsigned preview policy](https://github.com/openreading-ai/openreading-agent-tools/blob/main/SECURITY.md#unsigned-preview-policy) discloses ad-hoc signing and requires no Developer ID or notarization for this candidate.
The files in historical/ belong to the old prototype assembler, not this installation route.
