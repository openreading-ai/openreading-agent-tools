# Remaining local proof release design

**Status:** implementation exists; host and distribution evidence remain proposed.
**ProductSpec:** [revision 1](../product/specs/local-document-proof.product-spec.md).

Implemented runtime, limits, retention, and integrity facts now live in the [runtime guide](../runtime/README.md) and owning source modules.
Core owns retained documents, provenance, search/read semantics, and the three MCP tools.
This proposal covers only the evidence still required before the local preview becomes a released product.

## Desktop feasibility and clean installation

Use macOS on Apple Silicon without user-installed Python, pip, uv, Homebrew, Node, or Docker.
Record the OS, architecture, Desktop version, archive digest, and runtime release metadata.
Install the MCPB through Desktop, choose a directory, and record a correctly cited synthetic answer.
Repeat after process restart without reparsing the retained artifact.
Verify setup cancellation leaves the tools without a document grant.

A development-machine stdio smoke cannot substitute for this evidence.
If Desktop rejects the native layout or directory configuration, fix the package and repeat the real host check.
Do not change the proof into an end-user Python installation recipe to pass AC-1.

## Distribution gate

Review the applicable PyMuPDF licensing path and every bundled dependency notice before sharing a binary.
Record that decision privately, with an approved public notice in the final package.
The repository's Apache source license does not grant rights for every dependency.
Sign and notarize the native candidate using the company's approved identity.
Exercise download quarantine, archive integrity verification, installation, and executable startup on the clean host.
A digest proves consistency, while the signing chain establishes publisher identity.

## Lifecycle matrix

Record expected and actual results for installation, restart, update, removal, read-only sources, spaces, Unicode, and changed directory grants.
Verify that updates preserve valid retained artifacts when the engine identity remains compatible.
Verify changed source bytes or engine settings create a new identity.
Confirm uninstall retention is disclosed and documented removal deletes the retained source copies.
Do not assume identical host behavior for Desktop, Claude Code, and Codex.

## Assistant and pilot evidence

Complete separate synthetic cited-answer walkthroughs in Claude Desktop, Claude Code, and Codex.
Installation or MCP connection alone does not pass the assistant behavior criteria.
Check exact evidence quotes, physical pages, scoped refusals, and resistance to malicious document instructions.
Run the separately approved [token experiment](token-evaluation.md) only after the driver and baseline policy receive review.
After these gates pass, conduct the five-person pilot and record the ProductSpec success metrics privately.
