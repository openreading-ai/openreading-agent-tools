# OpenReading for Codex

Install the Apple Silicon connector from GitHub through Codex's plugin manager.
The plugin includes its interpreter, two skills, nine document tools and one Settings opener.
It includes no parser, model, Core server or runtime downloader. Other platforms remain pending.
Start [OpenReading Core separately](https://github.com/openreading-ai/openreading-agent-tools/blob/main/clients/full-core/README.md#run-core-for-the-connector).

## Install from GitHub

This revision pins the alpha.23 security-review candidate. Independent review and exact-build native acceptance remain pending.
After that build's catalog PR is merged, register the main marketplace:

~~~sh
codex plugin marketplace add openreading-ai/openreading-agent-tools
codex plugin add openreading@openreading
~~~

The repository is private until publication approval. Your Git credentials must permit repository access.
If you already use GitHub CLI, `gh auth setup-git --hostname github.com` configures Git to use that login for private HTTPS fetches.
This changes the credential helper for GitHub, not only this repository. Skip it when your existing Git authentication works.
Public installation will not require repository credentials. The preview tests use isolated SSH authentication instead.
The host fetches the complete package and preserves its executable permissions. Do not extract a ZIP or copy a plugin folder.
The catalog pins a distribution commit, so fetching newer source does not silently select an unreviewed runtime.
Choose **OpenReading** for Codex, not **OpenReading for ChatGPT**. Shared host configuration can expose both entries.

Start a new local Codex thread. Open OpenReading settings, enter your Core URL, test and save.
Quit and reopen the client after saving. Select a synthetic document and choose Process when ready.
Selection queues files without submitting them. Add more extends the queue.
Verify a returned quote against the source document.

## Updates and removal

~~~sh
codex plugin marketplace upgrade openreading
codex plugin add openreading@openreading
~~~

Restart the app and start a new thread after updates. A preview registration follows its selected branch.
To move from the review branch to main, register the repository again with `--ref main` after merge.
Remove only this plugin with `codex plugin remove openreading@openreading`.

The fixed client label remains `codex`. Preferences live under `~/Library/Application Support/OpenReading/agent-tools/codex`.
Retained data defaults to `~/.openreading/clients/codex/v2`; Storage settings can select another folder.
Installation, updates and removal preserve those settings and retained documents. Cancel unwanted jobs before removal.
Follow [Remove retained data](../../SECURITY.md#remove-retained-data) to remove this client's copies and settings safely.
Server failure never invokes a local parser or automatically resubmits uncertain work.

## Verification boundaries

The [build guide](https://github.com/openreading-ai/openreading-agent-tools/blob/main/runtime/server_client/README.md) records the verified runtime and Git distribution workflow.
Native GitHub installation, cached tool discovery and synthetic processing require exact-build checks.
Owner-operated Settings, picker, answers and lifecycle checks remain independent of CLI installation.
Clean-machine prerequisites, remote HTTPS, signing and notarization remain release gates.
