# Historical revision 1 Codex package

This developer package requires a format-1 worker and an explicit document directory.
It is not the current picker-based release candidate. It uses macOS Apple Silicon.
No optional Core server destination or Settings app is included.

Build it with the historical assembler in the [runtime guide](https://github.com/openreading-ai/openreading-agent-tools/blob/main/runtime/README.md).
Use absolute paths for the assembled marketplace and your synthetic document directory:

~~~sh
/absolute/path/to/dist/clients/codex/plugins/openreading-local-proof/server/openreading-worker --client codex --configure --input-root /absolute/path/to/documents
codex plugin marketplace add /absolute/path/to/dist/clients/codex
codex plugin add openreading-local-proof@openreading-local-review
~~~

The grant applies only to OpenReading. Retrieved excerpts enter your assistant context.
Settings live under `~/Library/Application Support/OpenReading/agent-tools/codex/config.json`.
Retained copies live in the adjacent `v1/` directory. Changing the grant does not erase them.
Remove the plugin with `codex plugin remove openreading-local-proof@openreading-local-review`.
Stop the client before manually removing retained copies. Uninstall does not erase them.

The [client matrix](https://github.com/openreading-ai/openreading-agent-tools/blob/main/clients/README.md) separates historical observations from current acceptance.
Restoring these templates establishes no new native installation or clean-machine result.
