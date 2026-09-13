# Historical revision 1 Desktop package

The package contains a native stdio MCP server, so you do not start an HTTP service or install Python.
This archive is the historical PyMuPDF prototype. It does not establish current release acceptance.
The manifest targets macOS on Apple Silicon and requires an explicit document directory.

## Proposed host walkthrough

This walkthrough still needs execution on a clean machine with a recorded Claude Desktop version.
Open Desktop settings, locate the extension installation interface, and select the generated `.mcpb` archive.
Choose a directory containing a synthetic PDF, then start a new chat with the extension enabled.
Ask: "Use OpenReading on agreement.pdf. What is the renewal notice period? Cite the physical page and evidence identifier."
Confirm that import, search, and read tools execute before accepting the answer as sourced.

The official MCPB validator and archive round-trip smoke pass locally.
Desktop GUI installation, quarantine behavior, and the cited-answer walkthrough remain unverified.
Do not distribute this unsigned local candidate before the license and signing gates pass.

The pinned MCPB 2.1.2 configuration resolver substitutes `${__dirname}` in `mcp_config.command`.
An offline test calls that resolver with this manifest and checks the executable path and Unicode directory argument.
The [MCPB manifest reference](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md) describes configuration substitution.
This resolves the library-level question without proving Desktop installation or launch.
Record the actual Desktop launch result, executable permissions, quarantine behavior, and startup time during the host check.
A packaging change requires an observed host failure, not a schema-validation assumption.

## Privacy and removal

The chosen folder grants access; it does not recursively import its contents.
Source copies and extracted evidence remain locally until removed.
Retrieved excerpts enter Claude's context and may be processed by its cloud model.

Desktop artifacts live under `~/Library/Application Support/OpenReading/agent-tools/claude-desktop/v1/`.
Disable or remove the extension in Desktop, stop its process, then delete that directory to remove retained copies.
The host's uninstall behavior must still be verified; retention is intentionally documented separately.
Read the import tool description for the configured document limits.
