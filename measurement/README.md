# Local Desktop evidence tooling

The active proof uses OpenReading through existing Claude and ChatGPT Desktop apps.
Provider API trials are prohibited. Existing Desktop account walkthroughs remain allowed.
The [Desktop evidence design](../design/token-evaluation.md) separates document usability, citation accuracy and unmeasured token savings.
The Docling retrieval gate and citation checker below are active; historical API study execution is retired.

## Historical offline accounting and reports

`measurement.prepare.prepare`, `measurement.probe.prepare`, `measurement.probe.finalize` and `runTrial` refuse unconditionally.
The `--live` CLI flag refuses before manifest access, regardless of historical approval flags or supplied keys.
No provider execution SDK is installed. These entry points do not read account credentials or launch models.
Historical manifest schemas preserve their original fields; an account or budget in a file is no longer execution authority.

`accounting.mjs` still normalizes retained synthetic or historical SDK event records, including cached tokens, cumulative snapshots and incomplete usage.
`report.mjs` still evaluates historical report rules without running models or treating unavailable usage as zero.
The command below rebuilds a historical report; it cannot start a trial:

~~~sh
node measurement/run.mjs /absolute/historical-evidence/manifest.json --report
~~~

Report replay verifies captured input hashes and raw events without starting the historical interpreter or requiring the old SDK installation.
Current executable, dependency and driver hashes are not revalidated in report mode; the result proves record consistency only.
Dry validation without `--report` can still inspect the local historical runtime, but cannot invoke a model.
Raw events must agree with stored usage and the bound manifest. Failures and unrun rows stay visible.
Historical reports are labeled as API-record replay and cannot establish Desktop usage, savings, billing or quota changes.
Direct module accounting is available for archived events without recreating a provider runtime.
The unrun M0 directories remain preserved with supersession records outside Git. Do not finalize or relabel them.
The old study plan remains in Git history, referenced from the [Desktop evidence design](../design/token-evaluation.md#retired-api-study-record).

## Revision 2 offline retrieval gate

The Docling corpus uses ReportLab 4.4.10, its bundled Vera font, and [frozen synthetic scan pixels](fixtures/README.md).
The [public recipe](corpus.json) freezes twelve questions, supporting physical pages, required qualifiers, diagnostic queries, and expected PDF hashes.
`corpus.py` generates identical bytes in independent offline tests and keeps ground truth outside `documents/`.
Historical revision 1 preparation and binaries keep their original pins.
The ordinary test environment adds ReportLab only as a development dependency.

Install the separate candidate with `uv sync --frozen --project runtime/feasibility`.
With the pinned layout assets and your Tesseract paths, run on macOS:

~~~sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  runtime/feasibility/.venv/bin/python scripts/retrieval_check.py \
  --assets /absolute/models --output /absolute/new-evidence-directory \
  --lock runtime/feasibility/uv.lock \
  --tesseract /absolute/tesseract --tessdata /absolute/tessdata
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  runtime/feasibility/.venv/bin/python scripts/retrieval_restart.py \
  --assets /absolute/models --output /absolute/new-evidence-directory \
  --lock runtime/feasibility/uv.lock
~~~

The first command verifies the installed core commit and dependencies, and observes network denial through a connection attempt.
Every answerable task must retrieve every supporting physical page within the top five hits of its frozen queries.
Each query records its own recall. Exact reads must match verified retained spans and include every required qualifier.
Missing-fact answers remain untested scoped-refusal tasks, separate from positive recall.
The document instruction on page two is inert adversarial data; no model adherence result is claimed.
The full-text files contain the same Docling page text that selective retrieval uses, without duplicated block encodings.

The second command starts two fresh MCP processes against the retained store.
It verifies reused artifact identities, every recorded exact quote, and refusal outside the input grant.
It also requires the three selected tools, records negotiated protocol/server identity, and compares sorted tool-schema hashes across restarts.
Its report records the retrieval report's SHA-256; the retained record binds restart evidence to its retrieval run.
The 100-page, 300-second, four-GiB sampled-memory configuration is a diagnostic profile, not a supported product limit.
OCR-disabled 24-, 48-, and 80-page inputs are frozen diagnostic fixtures, not a native large-document support claim.
A separate six-page PDF exercises scans, mixed origins, blank pages, columns, ligatures, and line-break hyphens with OCR on and off.
Printed labels differ from physical pages, and the report table has a qualifier on the following physical page.
The cross-page questions need separate items from multiple pages; they do not prove native multi-page item provenance.

On 2026-09-11, core `7d97b75b6ef9c65349fd044775087997205c72e2` passed all nine answerable tasks and both functional modes after a fresh import.
This run uses Docling integration v5; earlier retained artifacts are not relabeled as current evidence.
Two fresh MCP processes each verified 51 exact reads and refused the outside-grant request.
The three missing-fact tasks and document-instruction behavior still require model and human review.
This is local engine evidence, not an installation result or a token-saving claim.
Frozen retrieval queries deliberately test whether the engine can find supporting pages with known good terms.
Recall uses the union of those queries; it does not establish that a model will choose effective queries.
Printed labels may differ from physical pages and can be omitted from extracted text.
Native review checks physical pages explicitly and records the actual source visible through each app workflow.

## Citation evidence checker

`citations.py` verifies annotated quotations against captured calls and the frozen runtime's public MCP read tool.
Run it from the ordinary test environment, with the same client store and input grant used for the capture:

~~~sh
runtime/.venv/bin/python -m measurement.citations \
  --capture /absolute/capture.json --review /absolute/citation-review.json \
  --runtime /absolute/frozen-runtime --client codex \
  --input-root /absolute/document-grant --ocr on
~~~

The command verifies the bundle before launch and calls only `openreading_read` during checking.
It never imports the historical revision 1 core API or inspects private artifact files.
The explicit client selects the existing artifact namespace; it does not establish native client compatibility.
No settings file is changed. The launcher may create its normal private profile and artifact directories.
Exit zero means the annotated citation evidence passed. Invalid input, missing evidence, or transport failure returns one with a sanitized reason type.
The report binds both input files by SHA-256 and records the selected core and worker identities.

Capture format 1 contains `host` (`application`, `version`, `mode`), a `complete` flag, a `tools` map and ordered `events`.
The map gives the exact captured names for `import`, `search` and `read`, including host qualification when present.
A request event has `kind="request"`, a nonempty string `id`, `name` and `arguments`.
Its response has `kind="response"`, the same `id` and the complete MCP `result` object.
The final event has `kind="answer"` and the exact rendered answer `text`.
Missing responses, duplicate IDs, ambiguous payloads and events after the answer refuse verification.
Native adapters still need to establish and preserve their actual capture source; this format is not a native log exporter.

Review format 1 contains `capture_sha256`, `citations_complete=true` and a nonempty `citations` list.
Each annotation names `artifact_id`, `evidence_id`, `page`, `text_origin` and the corresponding `import_call`, `search_call` and `read_call` IDs.
`quote_span`, `filename_span` and `page_span` are half-open Unicode code-point offsets into the captured answer, not byte or UTF-16 offsets.
The page label must read `physical PDF page N`; unsupported presentation formats remain unverified.
`origin_span` is null unless a visible origin label is annotated. OCR, mixed and unknown evidence require that label, matched without case sensitivity.
Unknown keys refuse verification; [synthetic test fixtures](../tests/runtime/test_citations.py) demonstrate the complete shape.

Successful import, search and read calls must precede the answer in order and identify the same artifact and evidence.
The captured passage must equal a fresh verified read, including its offsets, physical page and origin.
The answer's quote must be an exact substring containing at least two Unicode letters or digits.
Whitespace, punctuation and one-character selections refuse verification; include surrounding context for a single-character value.
This is a minimum content check, not proof that a quote supports the answer.
A valid quote may lie outside the search excerpt when the captured read supplies it.
Filename, physical-page and optional origin labels must follow the quote in that order on the line where it ends.
They must precede the next annotated quote and cannot skip an earlier matching label.
For example, labels repeated in a later aside cannot replace the labels following the quote.
These placement rules remain unchanged for review format 1. Human review still checks semantic association and material support.
A selected prefix cannot disguise page 30 as page 3 or a different filename as the correct source.
Wrong pages, paraphrases, cross-artifact IDs, missing calls, changed capture bytes and omitted OCR labels have negative tests.

Review format 2 keeps the same fields and adds `presentation_span` to every citation annotation.
Capture format stays at 1. Each presentation span covers the entire source header and quote, or the entire quote and source list.
Spans must be disjoint and contain the quote and every annotated label without overlapping fields.
The checker consumes the whole span using two closed rendered-text layouts:

~~~text
From agreement.pdf, physical page 3, evidence p0003-b0001-s0000 (native text):

"Provide 60 days notice."

Quote: "invoices are payable within 45 days."
• Physical page: 2
• Text origin: ocr
• Evidence ID: p0002-b0001-s0000
• Document: functional.pdf
~~~

The source-header layout requires balanced parentheses and also accepts `Exact quote (filename, physical page N, evidence ID identifier, native text):` before the quote.
The source list optionally includes `(returned by search, not built)` after the identifier and `, artifact FULL_ID` after the filename.
Identifiers must match the checked calls; abbreviated artifact identifiers remain unsupported.
Review 2 also accepts `physical PDF page N`; its list uses `Physical page: N`.
Unicode whitespace and straight or curly quote delimiters are accepted without changing the captured quote.
Intervening prose, unrelated asides, conflicting source labels, overlapping citation blocks and unrecognized layouts refuse verification.
Select spans in the original rendered text. Do not rewrite a host answer to fit the checker or fabricate missing calls.
A human still attests which complete block belongs to the claim; grammar alone cannot establish semantic support.

A reviewer supplies both completeness attestations after checking the original transcript and every visible citation.
The checker cannot authenticate fabricated capture files or discover an omitted citation in arbitrary prose.
It verifies annotated evidence links and leaves answer correctness, unsupported material claims and instruction adherence for human review.
No result from this checker establishes host support or token savings.
A real frozen-runtime check verified native and OCR passages using a generated synthetic answer; no assistant was invoked.

Retain CLI stdout unchanged as the machine result, such as `citation-cli-report.json`.
Store wrapper annotations and run context separately; added context is not a field emitted by the checker.
The earlier `citation-report.json` development record includes a `scope` field added by the synthetic wrapper.
Its corresponding `citation-cli-report.json` is the unedited CLI output; neither is a native assistant result.

## Desktop timing diagnostic

`desktop_timing.py` reads one existing Claude Desktop compact MCP log without starting a server or calling a model.
It prints request/response durations, initialization intervals and gaps between completed calls.
The report excludes connector names, document payloads and input paths, and binds the input bytes with SHA-256.

~~~sh
runtime/.venv/bin/python -m measurement.desktop_timing --log /absolute/connector.log
~~~

Exit 0 means the observed tool calls and initializations have paired endpoints, not that the tools succeeded.
Exit 1 reports incomplete pairing; missing durations stay null. Exit 2 refuses invalid input or incompatible message syntax.
The supported format contains `Message from client: method="tools/call" id=N params` and `Message from server: id=N`.
Use one connector log; concatenated or interleaved process logs cannot establish reliable sessions.
Repeated IDs without initialization and backwards timestamps refuse. Notifications and unrelated log lines are ignored.

A 12-second interval includes transport and server work. It does not establish 12 seconds of PDF parsing.
The compact host log does not identify the document or separate model loading, OCR, extraction and artifact writing.
A gap between calls may include model work, tool approval, user interaction or separate questions.
The diagnostic therefore leaves document identity, parser time and complete answer time unknown, with token savings unmeasured.
It does not enable verbose logging, change host settings or collect telemetry.
