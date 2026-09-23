# Codex local preview

Launch scope: [OSS product v1](../../design/oss-launch.md) exposes the full implemented MCP catalog of its pinned core through the slim Docling runtime. Managed product v2 comes after launch; only a static “Coming soon” visual is planned. Historical profile/settings version 2 does not mean managed processing.

**Revision status:** this guide describes the superseded revision 1 PyMuPDF prototype.
The Docling developer harness is implemented; the [assistant migration](../../design/assistant-clients.md) and Docling client distribution remain proposed.
See the [client matrix](../README.md) for the limits of existing evidence.
The legacy setup commands below do not establish revision 2 compatibility and must not be
used as server-client setup.
The [client matrix](../README.md#owner-operated-candidate-checks-september-16-2026) records later owner-operated Docling checks through separate session-specific registrations.
Those checks do not validate this historical marketplace package or its installation commands.

The historical package uses the portable Agent Plugins manifest and its PyMuPDF worker.
No current Codex server-client package is assembled. The matrix records that cell as blocked.
Build the historical package only for its retained prototype checks.

~~~sh
/absolute/path/to/dist/clients/codex/plugins/openreading-local-proof/server/openreading-worker --client codex --configure --input-root /absolute/path/to/documents
codex plugin marketplace add /absolute/path/to/dist/clients/codex
codex plugin add openreading-local-proof@openreading-local-review
~~~

Codex CLI 0.153.4 accepted the local marketplace and installed the package on macOS 15.1 arm64.
The installed cache's frozen worker also passed the MCP import/search/read/restart smoke, and plugin removal succeeded.
These checks do not establish that a Codex model invoked the tools or produced correct citations.
Restart the client, enable the plugin when required, and ask it to use OpenReading on one synthetic PDF.
Confirm import, search, and read tool calls before accepting the cited answer.

## Grants and removal

Without `--configure`, startup refuses access instead of choosing a default source directory.
Run the configuration command again to change the grant.
The worker stores configuration under `~/Library/Application Support/OpenReading/agent-tools/codex/config.json`.
Retained source copies and passages live in the adjacent `v1/` directory.
Changing the grant restricts access to older artifacts but does not erase them.

Run `codex plugin remove openreading-local-proof@openreading-local-review`, then stop the client before removing retained files.
Deleting the complete `codex/` application-data directory clears the saved grant and retained evidence.
Actual model invocation, update/removal lifecycle, and fresh-machine behavior remain release checks.
