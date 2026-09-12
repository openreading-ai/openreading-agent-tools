# Desktop evidence and token-claim boundaries

**Status:** revision 5 Desktop-only proposal. Provider API studies are retired and prohibited.
**ProductSpec:** [revision 5](../product/specs/local-document-proof.product-spec.md), AC-15 through AC-17 and EVAL-2.
**Implementation:** [offline accounting, report readers and citation checker](../measurement/README.md).

## What remains to prove

OpenReading should make local documents usable in the owner's existing Claude and ChatGPT Desktop apps.
The first proof measures setup, document access, sourced answer quality, physical-page citations, and local resource costs.
Large-document support and token savings are distinct hypotheses.
Neither a successful parse nor a short tool response establishes total model-token savings.

Owner-operated testing in an existing Desktop account is allowed.
Provider API keys, separately metered trials, agent SDK execution, and API substitutes for native apps are prohibited.
This restriction does not remove core's independently configurable backends, CLI, Python API, or HTTP functionality.

## Native document-access comparison

Register a separate large synthetic document after resource measurements establish a useful local profile.
Record its byte hash, file size, physical page count, extracted character count, text density, scans, and answer rubric.
Keep the existing frozen citation corpus unchanged; sparse pages do not establish support for dense documents of the same page count.

Test the app's normal upload and document workflow on those exact source bytes.
Do not handicap its ordinary tools, infer its limits from an old help page, or force a failed baseline.
Retain its actual success, refusal, limit message, partial processing, elapsed time and unanswered questions.
Then use the connected OpenReading tools on the same document and registered question.
Record import, search, read, citations, warnings, missing evidence, elapsed time and local memory.

Claim access beyond a native limit only when that limit and OpenReading's successful sourced answer were both observed.
If both paths work, describe their observed differences without manufacturing a limit advantage.
Compare each app version and conversation mode separately. Claude results cannot establish ChatGPT compatibility.

## Citation and quality review

Preserve the host's complete captured calls and exact answer, with application version, mode, model when visible and runtime identity.
The implemented citation checker verifies evidence links, not semantic support or capture authenticity.
Human review checks the answer, material qualifications, all citations, instruction adherence and capture completeness.
An unverified origin must remain visibly unknown; it cannot be presented as native text.
Screenshots and pasted snippets remain partial observations until the missing native record exists.

## Optional Desktop usage investigation

Token reduction is untested, not falsified. It is not a packaging or release prerequisite.
First determine whether the actual Desktop app exposes complete, attributable usage for the whole task.
Do not substitute a provider API, coding-client SDK, tokenizer estimate, extracted characters, or tool-response bytes.
If the app does not expose sufficient counters, report token savings as unmeasured and continue functional work.

Before a future quantitative claim, register a Desktop-specific protocol covering:

- The exact app version, mode, model, source bytes, question, session state, ordinary workflow and OpenReading workflow.
- Counter semantics and completeness across prompts, tool definitions, cached input, calls, retries and answers.
- Matched quality review and source citations, keeping failed and incomplete tasks visible.
- Repetitions and cache/session controls that the actual app supports, with limitations stated explicitly.
- A claim threshold fixed before measurements, without implying monetary or subscription-quota savings from token counts.

This document supplies no counter implementation or permission to invoke another execution surface.
No provider API adapter is planned as a fallback.

## Retired API study record

The former M0/M1/M2 plan used provider execution SDKs, account keys, budgets and three API-driven comparison arms.
It is superseded by the owner's Desktop-only decision and cannot gate P1 or H1.
Its full historical text remains in [commit 1043aaf](https://github.com/openreading-ai/openreading-agent-tools/blob/1043aaf37429503f90e029bcd01354d45376fd53/design/token-evaluation.md).
Do not execute those historical instructions.

Preserve unrun prepared drafts with a separate supersession record outside Git; do not delete or relabel them as evidence.
Existing manifest schemas and offline accounting/report readers retain their historical meaning.
Any historical report is explicitly API-record replay, not a Desktop token measurement or authority to start new work.
The execution and preparation compatibility entry points refuse permanently, regardless of stored approval fields.
