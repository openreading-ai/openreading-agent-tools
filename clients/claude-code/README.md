# Claude Code local preview

**Revision status:** this guide describes the superseded revision 1 PyMuPDF prototype.
The [revision 2 design](../../design/local-document-proof.md) replaces the distributed engine with Docling and is not implemented yet.
Existing setup commands and test results below do not establish revision 2 compatibility.

The assembled marketplace installs a frozen worker and the shared evidence retrieval skill.
Build the packages from the [runtime guide](../../runtime/README.md), then use absolute paths below.

~~~sh
claude plugin marketplace add /absolute/path/to/dist/clients/claude-code
claude plugin install openreading-local-proof@openreading-local-review --config input_root=/absolute/path/to/documents
claude mcp list
~~~

Claude Code 2.1.266 installed the local marketplace and reported the OpenReading MCP server connected on macOS 15.1 arm64.
Plugin removal also succeeded in the isolated test configuration.
These checks did not send a model request or establish answer quality.
Start a fresh chat and ask: "Use OpenReading on agreement.pdf. Find the renewal notice period and cite the physical page."
The skill asks Claude to import once, search, read exact evidence, and cite the filename, page, and evidence identifier.

## Configuration and removal

Installation requires an explicit `input_root` directory.
The worker refuses missing or invalid grants and does not infer access from the current working directory.
Plugin configuration supplies arguments directly to the executable without a shell.

To remove the plugin, run:

~~~sh
claude plugin uninstall openreading-local-proof@openreading-local-review
~~~

Retained files remain under `~/Library/Application Support/OpenReading/agent-tools/claude-code/v1/`.
Stop the client before deleting that directory to erase retained copies.
The [runtime guide](../../runtime/README.md) describes limits and privacy boundaries.
Model walkthroughs, update lifecycle, and fresh-machine installation remain separate release checks.
