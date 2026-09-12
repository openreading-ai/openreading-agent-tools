# Token experiment tooling

**Revision status:** the sections before the revision 2 headings describe the superseded revision 1 PyMuPDF prototype.
The revision 2 sections at the end describe the implemented Docling retrieval gate and unscored M0 probe.
The [revision 2 design](../design/local-document-proof.md) still owns client and binary migration, which remain unbuilt.
Revision 1 setup commands and test results do not establish revision 2 compatibility.

You can prepare a synthetic study, validate its frozen inputs, and regenerate reports without calling a model.
Actual token savings require approved live trials and independent answer review.
The [revision 2 evaluation design](../design/token-evaluation.md) defines the next study and required driver changes.
`measurement.prepare` still emits revision 1 manifests; do not relabel them or use them as revision 2 study evidence.

## Prepare and validate

Build the client packages first using the [runtime guide](../runtime/README.md).
Choose a new absolute evidence directory outside every Git repository.
The model argument below is a candidate identifier, not a claim that an account can currently access it.

~~~sh
uv run --frozen --project runtime --all-groups python -m measurement.prepare --output /private/tmp/openreading-calibration --plugin /absolute/path/to/dist/clients/claude-code/plugins/openreading-local-proof --client /absolute/path/to/claude --model claude-sonnet-4-6 --account-label pending-review --study calibration
node measurement/run.mjs /private/tmp/openreading-calibration/manifest.json
node measurement/run.mjs /private/tmp/openreading-calibration/manifest.json --report
~~~

Preparation generates synthetic agreements, manuals, and reports with 24, 48, and 80 physical pages.
Questions cover exact facts, cross-page qualifications, missing facts, and contradictory historical instructions.
A planted malicious paragraph asks for an unrelated file upload; its presence is not proof that an assistant resists it.
Ground truth stays outside the directory granted to document tools.

A calibration contains four questions across categories, one repetition, and all three arms: 12 trials.
The primary study contains 12 questions, three repetitions, and all three arms: 108 trials.
Preparation proposes estimated ceilings of $20 for calibration and $100 for primary, with $2 per trial.
Neither preparation nor a dry run authorizes spending.

[prepare.py](prepare.py) freezes source documents, extraction baselines, ground truth, prompts, plugin configuration, runtime metadata, driver sources, dependency lock, and client executable.
[manifest.schema.json](manifest.schema.json) rejects unknown fields and unbounded trial settings.
[run.mjs](run.mjs) checks these hashes before each query.
If inputs change, prepare and review a new manifest instead of updating an approved run in place.

## Three arms

| Arm | Input and tools |
| --- | --- |
| A | Original document with Read, Glob, Grep, and explicitly approved local Bash commands. OpenReading is disabled. |
| B | Complete local extraction with physical page markers included once in the prompt. |
| C | Original document through the packaged OpenReading tools and retrieval skill, with the same base tools. |

Preparation freezes the absolute `pdftotext` executable path, its hash, and exact permitted Bash commands.
Each arm receives the same compact whole-document command and a page-command template for its document.
The runner verifies that those recipes generate the frozen allowlist and extracts page one before starting a query.
Missing utilities or empty extraction refuse live execution; preparation and report-only inspection remain available.
Moving the study to another machine requires new preparation and approval because its executable and paths are frozen.
A baseline Bash denial blocks the savings claim and C/A ratio, even when the model subsequently uses Read.
Choosing Read without a Bash denial remains valid; zero Bash calls alone do not establish a crippled baseline.
This restricted, recorded tool policy must be reviewed for baseline fairness before execution.
It does not represent every command an unrestricted personal Claude installation might use.
Read targets and search roots resolve through filesystem links before permission checks.
Glob filename patterns and Grep filename filters accept bounded relative patterns, without parent traversal or expansion groups.
Grep content regular expressions are text, not paths, and remain separate from its filename filter.
These callback restrictions are not an operating-system sandbox.
Each trial starts a fresh workspace and session; provider cache temperature remains unverified.

## Live authorization and interruption

Live execution requires an explicit API account key matching the frozen account fingerprint, a reviewed manifest hash, and an approved spending ceiling.
The owner approves those concrete inputs separately from implementation work.
After approval, the execution form is:

~~~sh
node measurement/run.mjs /absolute/evidence/manifest.json --live --approved-manifest-sha256 APPROVED_SHA256
~~~

`ANTHROPIC_API_KEY` is read only for live execution and fingerprinting during preparation.
Its value is never written to the manifest.
A missing or mismatched key refuses real SDK execution.
The SDK cap is estimated; a request already in flight can exceed it, so this is not a hard billing limit.

The runner accounts for every existing trial before scheduling another call after restart.
Incomplete usage, an unknown cost, or an interrupted raw log stops new scheduling.
A lock prevents concurrent drivers from spending against one manifest.
After a crash, inspect the private records and confirm no process remains before manually removing a stale lock.
Never delete failed trials or reset their estimated cost to resume spending.

## Accounting and human review

[accounting.mjs](accounting.mjs) uses the last cumulative SDK `modelUsage` snapshot and sums disjoint model entries.
It adds uncached input, cache-write input, and cache-read input once; output tokens remain separately visible.
Repeated assistant-message IDs and top-level totals are diagnostics, not extra billable usage.
Missing, invalid, zero-only, or rolled-back usage becomes incomplete rather than zero.
The accounting scope is the SDK query pipeline, including its subagents and internal helpers.
It excludes helpers outside that pipeline and does not replace an invoice.

Each private trial directory holds `events.jsonl` and `trial.json`.
Trial diagnostics record tool calls by unique call identifier and permission denials by tool name.
Baseline metadata records utility verification and Bash denials so constrained trials remain visible.
Review the answer against frozen `ground-truth.json` and the actual source passages.
Set `quality.passed` only when the answer, qualifications, and material citations are correct.
Set `quality.citation_valid` after checking each source reference, and retain the review rationale beside private evidence.
Unreviewed labels remain null and cannot support a positive claim.
Regenerate `report.json` using `--report`; that mode cannot invoke the model.

[report.mjs](report.mjs) includes every planned row, including failures and unrun trials.
It reports usage completeness, cache categories, output, latency, and human quality labels.
The primary claim requires complete valid pairs, at least 90% C quality, no quality regression overall or by category, supported citations, a median C/A input ratio at most 0.5, and lower total C input.
Calibration cannot establish the primary claim.
A zero, incomplete, unverified, or permission-constrained ordinary-tools baseline cannot establish a savings percentage.
No live trial or token-reduction result has been recorded by this implementation.

## Offline evidence

Node tests exercise cumulative accounting, duplicates, incomplete usage, claim refusal, frozen inputs, approval, resumable spending, and report-only execution.
Python tests generate and inspect the actual synthetic PDFs and preparation hashes.
`make verify` runs these checks without importing the SDK's live query function or contacting a model.
Raw trial records and transcripts remain outside Git; review the redacted report before sharing it.

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
Its report records the retrieval report's SHA-256; preparation and the runner refuse restart evidence for another retrieval run.
The 100-page, 300-second, four-GiB sampled-memory configuration is a diagnostic profile, not a supported product limit.
OCR-disabled 24-, 48-, and 80-page inputs form the proposed token cohort.
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
Printed labels remain visible to A but can be omitted from Docling text in B and C.
Human M0 review checks physical pages explicitly; label parity and harder blind queries remain prerequisites for a primary study.

## Revision 2 unscored token probe

M0 runs one frozen single-fact question per document across three arms, giving nine fresh trials.
A uses ordinary tools, B receives complete Docling page text, and C uses plain MCP plus appended retrieval instructions.
This developer treatment does not install or test a client plugin.
Every arm receives the same compact, executable `pdftotext` recipes.
Besides whole-document and single-page output, one recipe saves the text as a file in the trial's working directory.
Ordinary Grep and ranged Read can then search that file, so the baseline is not limited to ingesting the whole document.
Without it, Grep cannot search compressed PDF streams, and the 80-page whole-document output, about 37,000 characters, may exceed the host's Bash output limit.
Preparation and per-trial preflight verify that utility before any model request.

After the retrieval and restart commands pass, prepare without an account:

~~~sh
runtime/feasibility/.venv/bin/python -m measurement.probe prepare \
  --output /absolute/new-probe-directory --evidence /absolute/retrieval-evidence \
  --python /absolute/openreading-agent-tools/runtime/feasibility/.venv/bin/python \
  --client /absolute/claude --assets /absolute/models \
  --lock /absolute/openreading-agent-tools/runtime/feasibility/uv.lock
~~~

`probe-draft.json` deliberately lacks the model, account, and pricing required by the live schema.
`schedule.json` lists all nine trials, and `approval-needed.json` lists the remaining owner choices.
Preparation makes no model calls and never selects an account from ambient credentials.
On macOS, install Poppler if `pdftotext` is unavailable before preparing the ordinary-tools baseline.

The runtime snapshot hashes complete installation directories, including bytecode and startup hooks, plus the interpreter, model assets, core identity, and extraction settings.
Probe interpreters use isolated mode and disable bytecode writes; worker children inherit that write restriction.
This detects environment drift between trials; it does not attest a compromised operating system.
The runner recomputes it before every trial and refuses changed bytes or pins.
The manifest also binds corpus hashes, the passing retrieval/restart reports, and the measurement driver sources.
Each C trial starts a new store with the OCR-disabled Docling profile.
After the query, core verifies each retained artifact before its source, engine, and full-text hash are compared with retrieval evidence.
A mismatch marks the trial evidence invalid. Queries that never create an artifact remain visible as workflow observations.
Its MCP server runs with network denied and explicit 330-second tool-call timeouts.
Tool definitions are loaded at startup, and their token cost remains in measured usage.
The trial timeout is 600 seconds, with twelve turns and a proposed $0.50 per-trial SDK budget.
Nine proposed trial caps sum to $4.50 under a separate $5 study ceiling.
These are diagnostic settings and estimated caps, not installation limits or a hard billing guarantee.

When you select the account and exact provider model, provide a dated pricing JSON file with this shape:

~~~json
{
  "model_id": "THE_SELECTED_EXACT_MODEL_ID",
  "source": "https://platform.claude.com/docs/en/about-claude/pricing",
  "checked_on": "YYYY-MM-DD",
  "usd_per_million": {"input": null, "cache_write": null, "cache_read": null, "output": null}
}
~~~

Replace the placeholders with that model's verified prices before finalization; all four must be positive.
Supply the selected API account through `ANTHROPIC_API_KEY`; the file stores a per-study salted fingerprint and your nonsecret label.
The current driver uses an API account, not a Desktop subscription session.

~~~sh
runtime/feasibility/.venv/bin/python -m measurement.probe finalize /absolute/probe-directory \
  --model THE_SELECTED_EXACT_MODEL_ID --account NONSECRET_ACCOUNT_LABEL \
  --pricing /absolute/verified-pricing.json
node measurement/run.mjs /absolute/probe-directory/manifest.json
~~~

Finalization performs dry validation before creating `manifest.json`. It does not run a trial.
Review the printed hash and budget before separately approving execution:

~~~sh
node measurement/run.mjs /absolute/probe-directory/manifest.json \
  --live --approved-manifest-sha256 THE_APPROVED_HASH
node measurement/run.mjs /absolute/probe-directory/manifest.json --report
~~~

The driver records complete-query usage, cache categories, tool calls, permission denials, turns, failures, and query wall time.
Query wall time excludes offline preparation and environment preflight.
It stops scheduling after incomplete accounting or an exhausted estimated budget, including after process restart.
Budget accounting charges the larger of the SDK estimate and the frozen-price estimate.
The frozen estimate prices the selected model independently of the SDK.
An unexpected model makes cost accounting incomplete and stops further trials until its pricing is reviewed.
An observed per-trial overrun also stops scheduling, including after restart.
The SDK still controls in-flight spending using its own price table; an individual call can exceed the estimate.
After a restart, the runner recomputes each stored trial's usage from its raw events and refuses an edited record.
The report retains all nine rows with their per-model usage and SDK stop reasons, including turn and budget limits.
It reports physical pages alongside full-extraction and baseline character counts; these sparse synthetic pages are not a realistic document-size benchmark.
C access is classified by observed tool calls as plugin-only, mixed, ordinary-only, or no observed access.
The plugin-only fraction uses all planned C trials as its denominator, including unrun and failed trials.
Ordinary file tools count conservatively as possible document access.
It shows per-document C/A and C/B direction only after human review marks both compared answers as passing.
A cheap unreviewed or incorrect answer therefore produces no direction.
An ordinary-tools Bash denial invalidates that C/A direction.
Model answer quality and citation support still require human review; a direction from M0 supports no public savings claim.
The larger calibration, primary, and follow-up studies remain in the evaluation design.

The separate [functional case registry](functional-cases.json) fixes the exact document-instruction prompt and pass rubric for future native checks.
It does not modify the corpus, source hashes or token-study task schedule.
A complete tool trace is required to pass; missing capture is incomplete even when the final answer looks correct.

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
`origin_span` is null unless a visible origin label is annotated. OCR and mixed evidence require that label, matched without case sensitivity.
Unknown keys refuse verification; [synthetic test fixtures](../tests/runtime/test_citations.py) demonstrate the complete shape.

Successful import, search and read calls must precede the answer in order and identify the same artifact and evidence.
The captured passage must equal a fresh verified read, including its offsets, physical page and origin.
The answer's quote must be an exact substring; its filename and page label must match the source.
A selected prefix cannot disguise page 30 as page 3 or a different filename as the correct source.
Wrong pages, paraphrases, cross-artifact IDs, missing calls, changed capture bytes and omitted OCR labels have negative tests.

A reviewer supplies both completeness attestations after checking the original transcript and every visible citation.
The checker cannot authenticate fabricated capture files or discover an omitted citation in arbitrary prose.
It verifies annotated evidence links and leaves answer correctness, unsupported material claims and instruction adherence for human review.
No result from this checker establishes host support or token savings.
A real frozen-runtime check verified native and OCR passages using a generated synthetic answer; no assistant was invoked.
