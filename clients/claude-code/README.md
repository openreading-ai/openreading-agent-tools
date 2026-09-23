# Claude Code release candidate

OpenReading Agent Tools `0.2.0-rc.1` supplies a local Claude Code marketplace.
It contains the full bundled Docling runtime and the optional owner-operated
OpenReading Core server destination. It does not need Python, Node, uv, or a
Core checkout after you unpack the release.

## Platform

This release candidate supports macOS on Apple Silicon only. Intel macOS,
Linux, and Windows packages are pending. It is unsigned, and native
installation, update, removal, and clean-machine acceptance remain separate
release checks.

## Install

Unpack `OpenReading-Claude-Code-0.2.0-rc.1.zip`, then run:

~~~sh
claude plugin marketplace add /absolute/path/to/claude-code
claude plugin install openreading-local-documents@openreading-development
claude mcp list
~~~

Start a new Claude Code session and ask it to choose a document. The default
path opens OpenReading's local picker and processes selected documents with
bundled Docling. OpenReading retains its selected copies and artifacts locally.
Requested document content enters the assistant context.

## Optional Core server

The default remains bundled Docling. To send selected copies to an operator-run
Core server, open `OpenReading Settings.app` inside the installed plugin, choose
**Your OpenReading Core server**, test the destination, save it, and restart
Claude Code. Loopback servers can use HTTP. Other destinations require valid
HTTPS. The picker asks for confirmation before an upload.

Switching back to **Bundled Docling** affects the next import. It does not
delete retained files or alter already started jobs.

## Limits

This package is a release candidate, not a claim that Claude Code support is
complete. Record host version, package hash, worker hash, Core commit, tool
discovery, citations, cancellation, update, removal, and reinstall results for
native acceptance. No token-savings or parsing-accuracy claim follows from a
successful installation.
