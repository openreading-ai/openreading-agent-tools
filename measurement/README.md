# Token experiment tooling

You can prepare a synthetic study, validate its frozen inputs, and regenerate reports without calling a model.
Actual token savings require approved live trials and independent answer review.
The [evaluation design](../design/token-evaluation.md) defines the preregistered decision rules.

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

The manifest lists exact permitted Bash commands when `pdftotext` is available during preparation.
This restricted, recorded tool policy must be reviewed for baseline fairness before execution.
It does not represent every command an unrestricted personal Claude installation might use.
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
Review the answer against frozen `ground-truth.json` and the actual source passages.
Set `quality.passed` only when the answer, qualifications, and material citations are correct.
Set `quality.citation_valid` after checking each source reference, and retain the review rationale beside private evidence.
Unreviewed labels remain null and cannot support a positive claim.
Regenerate `report.json` using `--report`; that mode cannot invoke the model.

[report.mjs](report.mjs) includes every planned row, including failures and unrun trials.
It reports usage completeness, cache categories, output, latency, and human quality labels.
The primary claim requires complete valid pairs, at least 90% C quality, no quality regression overall or by category, supported citations, a median C/A input ratio at most 0.5, and lower total C input.
Calibration cannot establish the primary claim.
A zero or incomplete ordinary-tools baseline cannot establish a savings percentage.
No live trial or token-reduction result has been recorded by this implementation.

## Offline evidence

Node tests exercise cumulative accounting, duplicates, incomplete usage, claim refusal, frozen inputs, approval, resumable spending, and report-only execution.
Python tests generate and inspect the actual synthetic PDFs and preparation hashes.
`make verify` runs these checks without importing the SDK's live query function or contacting a model.
Raw trial records and transcripts remain outside Git; review the redacted report before sharing it.
