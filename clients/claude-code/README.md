# OpenReading for Claude Code

Install the Apple Silicon connector through Claude Code's GitHub marketplace support.
The plugin includes its interpreter, two skills, nine document tools and one Settings opener.
It includes no parser, model, Core server or runtime downloader. Other platforms remain pending.
Start [OpenReading Core separately](https://github.com/openreading-ai/openreading-agent-tools/blob/main/clients/full-core/README.md#run-core-for-the-connector).

## Install from GitHub

During PR review, use the preview branch explicitly:

~~~sh
claude plugin marketplace add openreading-ai/openreading-agent-tools@fix/github-marketplaces
claude plugin install openreading@openreading
~~~

After the owner merges that PR, new installations omit `@fix/github-marketplaces`.
Your Git credentials must permit access while the repository remains private.
Both the marketplace and its pinned plugin source need GitHub access. A successful catalog fetch alone does not prove HTTPS credentials work.
If you already use GitHub CLI, `gh auth setup-git --hostname github.com` configures Git to use that login for private HTTPS fetches.
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

## Verification boundaries

The [build guide](https://github.com/openreading-ai/openreading-agent-tools/blob/main/runtime/server_client/README.md) explains the Git distribution and exact worker identity.
GitHub install/update, cached tool discovery and synthetic processing require version-specific host checks.
Native Settings, selection, answer quality, clean-machine installation, signing and notarization remain independent release gates.
The files in historical/ belong to the old prototype assembler, not this installation route.
