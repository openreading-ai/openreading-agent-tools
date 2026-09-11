# Revision 3 design review decisions

**Status:** design findings adjudicated in ProductSpec revision 4. Implementations and native experiments remain pending.
The reviewer assessed commit `1436bcb`; its full scratch report remains ignored under `docs/`.
This record owns decisions about unbuilt work, not descriptions of shipped code.
The [probe plan](native-probes.md) defines empirical checks without treating proposed experiments as results.

## Accepted findings and bounded corrections

| Finding | Decision and correction |
| --- | --- |
| H1: unnamed ChatGPT surface | Accept the mode ambiguity. Preserve AC-1 for Claude Desktop and add AC-26 for a named local ChatGPT mode. A Codex local thread cannot satisfy the Chat conversation goal. Bundle identity alone does not prove a merged-product history or mode capability. |
| H2: no nondeveloper setup | Accept the missing route. Select a small signed helper app with a folder picker and OCR toggle, followed by pasting an argument-free executable path into native Settings. No silent shared-TOML writes. Form limitations remain empirical, not proven absent from sparse docs. |
| H3: missing startup budgets | Accept. Measure startup, initial tool catalog, and import separately, including inventory verification on worker spawn. The documented 10/60 defaults imply 8/48 budgets at the chosen margin, but are configurable defaults rather than universal ceilings. |
| H4: corpus mismatch | Accept. EVAL-1 references `agreement-single_fact`, `agreement-missing_fact`, and the generated page-2 instruction case. Renewal uses physical page 3 and the full written-receipt rubric. Corpus and evidence hashes stay unchanged. |
| M1: unverifiable native citations | Accept. Capture each host's actual transcript/tool trace, with a diagnostic relay fallback, and add an offline checker through core's public read contract. Bind answer spans, pages, artifacts, and observed calls; human review handles semantic support. |
| M2: frozen build too late | Accept. Add bounded unsigned P0 on the development machine before native OpenReading checks. Preserve sources, metadata, lock, assets, and relocated OCR dependencies; no identity bypass or public distribution. |
| M3: Codex isolation | Accept. Require separate child-process state and effective instruction/configuration isolation, plus actual denial of evidence reads. A read-only sandbox or isolated settings directory alone is insufficient. |
| M4: Codex auth/budget | Accept. First additional adapter uses a verified API-key account, salted binding, and no quota fallback. Prove actual controls; use a finite watchdog and report residual in-flight billing risk. Unknown controls cannot become a promised hard cap. |
| M5: configuration collision | Accept. Use `<client>/v2/config.json`, `v2/artifacts/`, and per-invocation `v2/launch/`; do not read or modify the legacy configuration. Add coexistence tests. |
| M6: OCR form tokens | Accept. Specify lowercase on/true and off/false; missing or empty is off for explicit setup, other tokens fail. E5 verifies native substitution instead of assuming it. |
| M7: host cancellation | Accept with distinct evidence. Record notification, timeout, and process-stop paths separately; unsupported host cancellation remains `not_exposed`. Cleanup via quit never passes a protocol-cancellation claim. |
| M8: overstated grant/locality | Accept. State that the grant limits only OpenReading tools. Exclude remote-executor registration and require nonce-bearing local process evidence. |
| M9: M0 versus cap | Choose diagnostic independence. Existing M0 uses its frozen safeguards and may precede the release cap. Scored packaged studies must fit their actual measured profile before approval. |
| L1: tool-list evidence | Accept the reproducibility gap, not a claim that the observation never happened. Mark the gate pending and assign E0 to retain a tested list-tools assertion in the restart harness. |
| L2: app version | Preserve the original dated 1.52386.0 observation; a fresh read now confirms 1.52386.3. Neither inventory observation is native compatibility evidence. |
| L3: study execution missing | Accept. Add M2 for separately approved calibration, primary, and follow-up execution with prerequisites and explicit reporting limits. |
| L4: profile file/lock | Accept. Inventory the shipped dependency lock and write a unique mode-0600 profile in a private per-invocation launch directory. Preserve it until owned workers exit. |
| L5: import prompts | Accept. Observe real import approval behavior in E1. Keep core's non-read-only annotation and never suppress prompts to improve a demo or measurement. |

## Scope judgments

Claude Desktop can complete its own release gates while ChatGPT capability remains unresolved.
The broader ChatGPT objective stays open; it is not silently replaced by a developer-only Codex integration.
If only Codex mode can call local tools, its value is verified evidence and possible efficiency, not newly gained local-file access.
Work mode is eligible only after local execution is observed; remote/cloud-task probes are excluded from this local proof.
The existing Claude M0 remains the cheapest diagnostic and does not wait for a new provider adapter.
Instrumented Codex remains the next measurement candidate after E6; an API harness is a separately reviewed alternative.

## Verification and unresolved observations

Code inspection confirms strict revision 1 settings, the source-execution refusal, repeated release verification, and the PyMuPDF-specific build recipe.
The frozen corpus confirms the page-3 renewal rubric and jurisdiction question; the generator supplies the page-2 instruction.
[OpenAI's MCP guide](https://learn.chatgpt.com/docs/extend/mcp) documents shared host settings, configurable timeout defaults, optional-server catalog grace, approval modes, and remote-executor configuration.
It does not supply native evidence that every conversation mode invokes a local server.
[OpenAI's packaging guide](https://developers.openai.com/plugins/build/plugins) distinguishes local marketplace support from broader plugin distribution; it does not substitute for E1.

No native host configuration, frozen build, model call, or client installation was performed during this adjudication.
The ChatGPT computer-use restriction remains an observation from the earlier investigation, not evidence for or against capability.
Unverified behavior stays assigned to E0 through E6 rather than marked resolved by this document.
