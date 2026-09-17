# Client compatibility

Launch scope: [OSS product v1](../design/oss-launch.md) exposes the full implemented MCP catalog of its pinned core through the slim Docling runtime. Managed product v2 comes after launch; only a static “Coming soon” visual is planned. Historical profile/settings version 2 does not mean managed processing.

OpenReading has one proposed Docling runtime and separately tested client connections.
The [assistant design](../design/assistant-clients.md) defines the pending migration and its evidence requirements.
Historical revision 1 packages do not establish Docling compatibility.

## Documented routes

Checked on 2026-09-11. These are connection candidates, not a supported-client release list.

| Surface | Documented local route | Current Docling evidence |
| --- | --- | --- |
| Claude Desktop | Local MCP desktop extension. | Owner-reported folder, delivery, reconnect and active-cancellation checks passed on the development candidate (folder skips passed the aggregate retest; the original discrepancy remains unexplained). Same-version removal and reinstall preserved retained data. Version upgrades, clean-machine installation and complete host/prompt capture remain pending. |
| ChatGPT desktop Chat conversation | Local route must be established by E1. | No mode-specific local invocation evidence. |
| ChatGPT desktop Work conversation | Conditional on independently established local execution. | No mode-specific local invocation evidence. |
| Codex local thread in ChatGPT desktop | Candidate STDIO registration on a Codex host. | Native UI, launch, and invocation pending. |
| Claude Code | Local STDIO registration; the existing prototype also has a plugin wrapper. | Owner reports successful 2.1.272 candidate imports, citations and local exports. Clean-machine distribution and lifecycle acceptance remain pending. |
| Codex CLI | Local STDIO registration; the existing prototype also has a plugin wrapper. | Owner reports successful candidate imports, citations and local exports. Preparation used 0.154.0; session version and distribution acceptance remain unverified. |
| ChatGPT web or mobile | Outside this local proof. | No compatibility claim. |

[Anthropic's local MCP guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop) describes desktop extensions and their setup.
[Claude Code's MCP guide](https://code.claude.com/docs/en/mcp) documents local STDIO registration.
[OpenAI's MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) documents local processes in ChatGPT desktop and Codex, including shared host settings.
Its web path is distinct from local desktop configuration; do not infer web support from a desktop registration.

## What has been checked

An ad hoc SDK probe observed initialization, the three selected tools, and outside-directory refusal on 2026-09-11.
Its script and output were not retained as reviewable repository evidence, so it does not close the protocol gate.
[E0](../design/native-probes.md) adds a reproducible tool-list check to the existing restart harness.
That check still cannot establish native host launch or model invocation.
The [measurement guide](../measurement/README.md) records the separate retrieval and restart checks.

The connection investigation found Claude Code 2.1.267 and Codex CLI 0.153.4 supporting local command registration in their installed help.
The initial 2026-09-11 inventory observed Claude Desktop 1.52386.0 and ChatGPT desktop 26.901.51231.
A later inventory on the same date observed Claude Desktop 1.52386.3; these are distinct observations, not host test results.
App presence does not establish the required settings, permissions, launch, or tool use.
The computer-use tool refused inspection of ChatGPT desktop, so its UI check remains pending.
No host configuration was changed, package installed, or model trial executed during this investigation.

## Owner-operated candidate checks, September 16, 2026

Owner-supplied reports cover local STDIO sessions in Claude Code 2.1.272 and Codex CLI on the development Mac.
The Codex executable reported 0.154.0 during preparation; the model session did not establish its version.
Both used the candidate built from core `3ff02d4` and Agent Tools `78bda83`.
The worker SHA-256 is `1d29da80156da3859005913d186c38d47e2bcf0d4bd338bb62f1b002b9df19b5`.
These tests used session-specific registration of the common runtime, not the historical marketplace packages described below.

Both hosts reported six synthetic imports, complete automatic results, exact citations, distinct same-name documents and provider-reported table cells.
Both hosts reported reading a forced small export through existing local tools and verifying its original bytes and hash.
Each host reported completing a fresh 251-page import and reading its 21,593,816-byte automatic export without attachment or fragment reconstruction.
Each host reported matching three physical-page passages against exact MCP reads, with their OCR labels preserved.
Codex reported increasing page-assembly counts and waited for terminal success after every page was assembled.

Post-run checks verified fourteen terminal job records and their retained file hashes.
Both large exports and both small exports equal their complete retained response, evidence mappings, origins and warnings.
The private record `2026-09-16-native-acceptance` separates summarized owner reports from those independent disk checks.
Original host transcripts, human-visible approvals and exact cancel-to-response latency were not captured.
One successful chooser cancellation report does not explicitly identify its host, so neither host receives a separate cancellation pass.
Codex reported printing one complete synthetic result against the test instruction and reading a required skill outside the fixture scope.
Claude Code reported 21 MCP calls, but no transcript was acquired to reconcile that count; it is not an accepted measurement.

The earlier Desktop folder run imported seventeen files across two receipt pages but omitted three expected skip categories.
A later selection-only native retest returned seventeen files, 99,808 bytes and both receipt pages with all four expected skip categories.
Copied receipts corroborate hidden:1, package:1, unsupported:1 and symlink:1. These are entry counts, not per-entry identity proofs.
The retest passes its aggregate selection check. The earlier discrepancy remains unexplained; no production fix is claimed.
Separate diagnostic replays used matching source and installed archive bytecode; neither ran the frozen bootloader or native chooser.

Preparation removed only the completed document artifact to force a fresh import, preserving its manifest hash, original source, exports, jobs and selection copies.
The owner reports discovering that active import after restarting Claude Desktop and opening a new chat, then cancelling that job.
The retained status is cancelled at 14 of 251 pages, with no receipt.
Post-terminal inspection found the recorded job process gone, no OpenReading parser or Tesseract processes, and empty artifact, staging and worker directories.
The private record `2026-09-16-native-reconnect-cancel` preserves this result without claiming exact cancellation latency or teardown order.
Earlier owner messages reported a completed job and a separate session without the connector. These attempts lack retained evidence records and establish no acceptance result.
Owner-requested cache resets removed the earlier artifact stores after their metadata was preserved; prior hash checks remain historical observations.

The owner removed and reinstalled the same development extension, then retrieved the existing Markdown artifact without selecting or importing again.
Independent removal checks found the extension directory and settings absent, with no associated extension processes observed after removal.
This was a point-in-time inspection; no process stop event was captured.
The Desktop client's current post-reset `v2/artifacts` and `v2/selection` roots retained eighteen and four files respectively, all unchanged.
The 1,190-byte JSON export also remained unchanged; these comparisons exclude historical stores deleted during the earlier cache reset.
After reinstall, all 4,655 installed files matched the before-uninstall inventory, and those retained files and export remained unchanged.
The owner recovered the existing job, exact pointer-based citation and content hash through the native tools.
The private record `2026-09-16-lifecycle-preparation` separates owner reports from before-removal, after-removal and after-reinstall file checks.
Claude Desktop 2.110.0 was observed during lifecycle preparation; this does not establish versions for earlier reported sessions.
This is same-version reinstall evidence on the development Mac, not a version upgrade or clean-machine installation.
Specific human-visible uninstall and reinstall prompts were not recorded.

These observations establish the reported workflows, not clean-machine installation, signed distribution, general parsing accuracy or token savings.
The historical setup commands below retain their original scope.

## Per-client guides

- [Claude Desktop](claude-desktop/README.md): partial owner-run Docling checks, manual developer setup, and historical package walkthrough.
- [ChatGPT desktop](chatgpt/README.md): documented connection candidate and remaining verification.
- [Claude Code](claude-code/README.md): historical marketplace and configuration evidence.
- [Codex](codex/README.md): historical package and configuration evidence.

Every future compatibility entry must name the tested runtime, application version, execution mode, and actual result.
API measurement, protocol smoke, and native installation remain separate evidence.

## Independent core installation

Power users can follow the [standalone core connection guide](full-core/README.md).
Its release walkthrough remains R1 work; the current MCP profiles do not expose every CLI/HTTP backend.
