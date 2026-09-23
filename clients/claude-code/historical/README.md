# Historical revision 1 Claude Code package

This developer package requires a format-1 worker and an explicit document directory.
It is not the current picker-based release candidate. It uses macOS Apple Silicon.
No optional Core server destination or Settings app is included.

Build it with the historical assembler in the [runtime guide](https://github.com/openreading-ai/openreading-agent-tools/blob/main/runtime/README.md).
Use absolute paths for the assembled marketplace and your synthetic document directory:

~~~sh
claude plugin marketplace add /absolute/path/to/dist/clients/claude-code
claude plugin install openreading-local-proof@openreading-local-review --config input_root=/absolute/path/to/documents
claude mcp list
~~~

The grant applies only to OpenReading. Retrieved excerpts enter your assistant context.
Retained copies live under `~/Library/Application Support/OpenReading/agent-tools/claude-code/v1/`.
Remove the plugin with `claude plugin uninstall openreading-local-proof@openreading-local-review`.
Stop the client before manually removing retained copies. Uninstall does not erase them.

The [client matrix](https://github.com/openreading-ai/openreading-agent-tools/blob/main/clients/README.md) separates historical observations from current acceptance.
Restoring these templates establishes no new native installation or clean-machine result.
