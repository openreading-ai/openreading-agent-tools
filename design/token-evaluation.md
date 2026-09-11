# Token evaluation for the local document proof

**Status:** the revision 2 unscored M0 driver is implemented; calibration, primary, follow-up, and human grading remain proposed.
The [measurement guide](../measurement/README.md) documents M0 and the historical revision 1 driver.
The expanded full-study contracts below remain unimplemented beyond that explicitly bounded probe.
**ProductSpec:** [revision 4](../product/specs/local-document-proof.product-spec.md), AC-15 through AC-17.
**Execution:** requires a separately approved live manifest and account.

The question is whether OpenReading reduces token consumption per correctly completed document task in a named assistant workflow.
Sections 1 through 11 specify the Claude study; the final section defines the proposed provider extension.
Existing revision 2 probe manifests and their implementation remain unchanged.
The experiment must also reveal retrieval failures and cases where an ordinary assistant is already efficient.
Installation success is evaluated separately through the [runtime design](local-document-proof.md).

## 1. What the proof may establish

The primary claim concerns one pinned Claude Code environment, one named model, and a frozen task set.
It measures the whole task, including prompts, tool definitions, retries, retrieval calls, and the final answer.
It does not measure only the bytes in the final tool response.

A passing result can support a statement about the evaluated tasks.
It cannot establish universal savings, subscription quota savings, Desktop billing changes, or thousand-page support.
An installation demo in Claude Desktop is not itself token evidence.

## 2. Three comparison arms

| Arm | Document workflow | What the comparison isolates |
| --- | --- | --- |
| A: ordinary tools | Claude Code uses its normal permitted document tools with OpenReading disabled. | Whether the new workflow improves on the real alternative. |
| B: full extraction | A local extraction is provided as complete clean text with page markers. | Whether preprocessing helps before selective retrieval. |
| C: selective evidence | The proposed plugin imports locally, then the assistant searches and reads bounded passages. | Whether keeping most extraction outside context reduces total consumption. |

The primary comparison is C against A.
C against B explains the contribution of selective retrieval.
B against A is a diagnostic comparison, not the main marketing baseline.
C/A can combine differences in PDF representation and selective retrieval; C/B isolates retrieval from the same extracted text.
Do not attribute all C/A savings to retrieval.
Verify the pinned host's PDF page-range behavior, image/text representation, and provider token accounting before freezing expectations.
The review's recalled page costs and fixed per-turn overhead are hypotheses, not measured constants.

Do not instruct A to read every page when ordinary tools could search or select pages.
Do not disable A's existing local utilities to make the plugin look better.
Record the actual installed tools and allowed operations before choosing the corpus.
Extra network installs or new paid parsers are unavailable in every arm.

Arm B receives the same core extraction that C searches, projected to one clean text representation.
Do not include duplicated text, markdown, raw backend JSON, and table encodings together.
Page markers preserve physical source page references for the same citation task.
Verify that this full projection fits the chosen model and host limits before including a task.
If it does not fit, mark B inapplicable and revise the registered corpus before live trials.

Arm C's instructions identify the OpenReading procedure.
That added instruction and its tool definitions count as treatment overhead.
The agent does not get ground-truth page locations, preferred search phrases, or hidden answer hints.
Record tool calls by host-qualified name and classify document access as plugin, ordinary tools, or mixed.
Report the fraction of C trials using only plugin document access without excluding mixed or nonadherent trials.
Low adherence is a workflow finding, not grounds to discard unfavorable results.
The manifest records effective SDK plugin configuration and differences from the installed client package.
A plain MCP server plus appended instructions is a developer-harness treatment, not proof of the packaged plugin.
The study measures the configured workflow, not spontaneous plugin discovery.
Discovery and installation are measured in the separate user pilot.

## 3. Task set

Use candidate synthetic documents with 24, 48, and 80 physical PDF pages.
For scored packaged studies, revise and refreeze a corpus that exceeds the measured engine/host limits before paid execution.
The separate diagnostic M0 retains its frozen developer safeguards and does not establish release-cap support.
Never mark an over-limit registered trial as successful or drop it after observing outcomes.
Each contains meaningful distractors and repeated terminology.
Do not create a thousand pages of filler and advertise the result as a realistic long-document benchmark.
Freeze document hashes, generator revision, questions, answer rubric, and supporting locations before any scored trial.

The initial full study has twelve question tasks:

| Document | Four required task categories |
| --- | --- |
| Agreement, 24 pages | One factual clause; a cross-page exception; a missing fact; a comparison of two related clauses. |
| Manual, 48 pages | One procedure; a repeated-term distractor; a version or precedence condition; a missing fact. |
| Report, 80 pages | A simple numeric table value; its footnote; a cross-page comparison; an unreported metric. |

The dataset records `document_category` separately from a shared `task_kind`.
The four shared kinds are single_fact, cross_page, missing_fact, and comparison, with one of each per document.
Map repeated-term and procedure questions explicitly into that common vocabulary before freezing the questions.
The no-regression condition applies both by document category and by shared task kind.

Ground truth identifies accepted answers, required qualifiers, and physical supporting pages.
An answer requiring a table footnote is incorrect when it omits a material qualifier.
An absent-fact answer succeeds only when it accurately states the evidence limitation.
It must not convert a failed keyword search into a universal assertion about the document.

The primary token cohort uses OCR disabled and supported text-bearing PDFs with the same Docling extraction for B and C.
OCR-enabled scans belong to a separately registered functional/quality cohort, not an implicit change to the token task set.
Keep corrupted, encrypted, and over-limit inputs in the functional refusal suite.
They are not silently counted as successful selective answers in the token dataset.

The synthetic generator, questions, answer rubric, retrieval queries, expected hashes, and generation recipe belong in this repository.
Pin the generation toolchain and fix document IDs, dates, and producer metadata.
Two independent generations under the pinned toolchain must produce identical bytes and hashes.
Ground truth remains outside the model's granted input directory during execution even though the synthetic source rubric is public.
Add the extraction realism and top-five recall gate from the engineering design before paying for model trials.

Public test fixtures remain synthetic.
Private customer documents can support a later externally supplied dataset with its own reviewed disclosure terms.
They never enter this repository or a public CI artifact.

## 4. Pilot, full run, and follow-up

The implemented M0 driver and nine-trial schedule live in the [measurement guide](../measurement/README.md).
Its execution still requires an approved account, exact model, frozen manifest hash, and finite budget.
It is unscored and supports no public token-savings percentage or product acceptance criterion.
If C loses to B on every tested document under fifty pages, retain the installability-and-citations story and deprioritize the token headline.
A negative result does not invalidate that functional product goal.

Then run calibration: four tasks spanning documents and shared task kinds, plus one no-document null task, once per arm: fifteen trials.
The null task uses the same arm tool/configuration definitions and asks a question needing no file access.
Use its measured overhead as a diagnostic only; do not subtract it from the scored primary input totals.
Its purpose is to identify broken instrumentation, invalid baselines, and impossible budgets.
Do not combine pilot outcomes with the scored study.
If the pilot changes prompts or criteria, freeze a new manifest before the scored run.

The full study has twelve tasks, three repetitions, three arms: 108 independent trials.
One trial is one new single-input Claude Agent SDK query call.
All arms use the same model identifier, answer format, maximum turns, permissions policy, and document access rights.
An arm-specific tool inventory is the treatment difference and is included in the manifest.

Randomize arm order inside each task/repetition block using a recorded ordering seed.
Rotate document order between repetitions.
The seed controls scheduling, not model sampling.
Do not claim reproducible model randomness when the API does not offer that control.

Every scored trial starts with a new chat.
Record prompt-cache reads and writes as observed.
A new chat is not evidence of a cold provider cache.
Use the same cache settings and interleaved order across arms.
Keep cached tokens visible in every table.

Preregister a secondary follow-up study before the primary run, and execute it only after the primary report is fixed.
It has one fixed document with three sequential questions in the same chat per arm, including initial import in C.
Register the questions, order, session settings, continuation accounting method, and independent budget.
Report both incremental and cumulative usage, with no double-counting of cumulative SDK snapshots.
The secondary claim requires complete sessions, equal or better quality, supported citations, and lower cumulative C input against the named baseline.
Allowed wording: "Across these three consecutive questions, cumulative input was lower by the measured amount at the reported quality."
Do not use warm artifact reuse or cached follow-ups to label first-use performance.

## 5. Registered manifest

The proposed full-study contract is broader than the implemented `measurement/probe-manifest.schema.json`.
`measurement/manifest.schema.json` continues to describe historical revision 1 records.
Use closed objects with explicit required fields.
Paths are relative to the manifest's directory and must stay inside its approved evidence root.

| Field | Required value or meaning |
| --- | --- |
| schema_version | Literal "3" for the proposed expanded manifest and trial contracts; historical versions 1 and 2 remain unchanged. |
| experiment_id | Unique study identifier, not a customer name. |
| spec_revision | 4 for new expanded studies, checked against the implemented contracts; existing version 2 probes retain revision 2. |
| study_kind | probe, calibration, primary, or followup; each has a closed schedule definition. |
| dataset_manifest, dataset_sha256 | Exact task/ground-truth manifest and its hash. |
| model_id | Full provider model identifier; floating aliases are refused. |
| client_version, sdk_version | Exact Claude Code and Agent SDK versions. |
| runtime_kind | developer_harness for M0; frozen_bundle for packaged-client studies. Neither is misreported as the other. |
| core_commit, runtime_sha256 | Exact engine revision plus a verified source/environment digest for M0 or final signed runtime digest for packaged studies. |
| prompt_sha256, skill_sha256 | Common instructions and treatment workflow hashes. |
| environment_sha256 | Sanitized inventory of OS, architecture, installed tools, effective plugin configuration, permissions, and cache settings. |
| engine_profile_sha256, retriever_revision | Measured resource/extraction profile and exact lexical ranking identity. |
| pricing_sha256 | Dated, model-specific secondary price table and category semantics. |
| generation_manifest_sha256 | Public synthetic generation recipe and expected source hashes. |
| arms | Exactly A, B, and C, including complete tool inventories and input projections. |
| task_ids | Frozen ordered task identifiers. |
| repetitions, order_seed | Trial count and randomized schedule seed. |
| max_trials | 9 for M0; 15 for calibration including null controls; 108 for primary; 9 questions across three follow-up sessions. |
| max_turns_per_trial | 12. |
| timeout_seconds_per_trial | Explicit finite value accommodating the measured import profile and retrieval workflow; never inherit 180 seconds without checking. |
| max_estimated_usd_per_trial | Explicit approved per-arm ceilings informed by the pinned model and calibration observations. |
| max_estimated_usd_total | Separate approved study ceiling; M0 proposes at most 5.00, while primary derives its ceiling from calibrated costs with margin. |
| evidence_root | User-owned output directory outside this Git checkout. |
| account_label | Nonsecret label identifying the approved account. |

These dollar limits are proposed limits, not permission to spend.
The owner can approve lower limits, but an underfunded primary schedule must be marked exploratory and cannot support the registered claim.
A $100 total does not guarantee completion of 108 trials with $2 individual ceilings.
Use observed upper costs per arm and document with a preregistered margin, then compare against the sum of per-trial ceilings.
Disclose residual interruption risk whenever the approved total is lower than that worst-case sum.
Changing the task set, model, budget, prompt, or criterion produces a new manifest hash.
The runner refuses continuation under the old approval hash.

Before live execution, the driver performs a no-network validation and prints the schedule.
Live execution requires both `--live` and `--approved-manifest-sha256` matching the approved file.
The caller supplies credentials through the supported host configuration.
The driver never reads a key from the manifest or writes one to the evidence directory.

Start one trial at a time.
Pass the smaller of the remaining estimated study budget and per-trial ceiling to the SDK budget option.
Do not reset sessions to bypass that ceiling.
The runner stops launching new trials at any manifest limit.
Record an in-flight overrun or incomplete usage rather than claiming an absolute billing cap.
Provider billing can differ from the SDK's estimated price table.

## 6. Usage accounting

Use the final result's per-model modelUsage record for each independent SDK query call.
It includes nested agent work that the top-level usage field may omit.
Pin and fixture-test the actual SDK field semantics.
The reference version observed during design is @anthropic-ai/claude-agent-sdk 0.3.267.
Revalidate its contracts if the implementation chooses a later version.

Do not sum cumulative result snapshots within one query call.
Do not also add per-message counts to a final total.
One API response can produce several assistant messages with the same message ID.
Deduplicate those IDs when diagnosing per-step inputs.
Their interim output counts do not replace the final output total.

The primary runner avoids streaming multi-turn input and reset commands.
That makes one call's final whole-tree result the accounting unit.
An error result still consumes tokens and stays in the trial table.
A missing or zeroed crash result yields usage_status incomplete unless complete provider records resolve it.
Do not turn missing counts into zero.

Normalize each model row into disjoint categories:

~~~text
input_uncached
input_cache_write
input_cache_read
output
~~~

Verify the categories against the pinned SDK/provider contract with a synthetic fixture.
If an SDK field includes cached tokens, subtract only according to its documented semantics.
Never infer that behavior from the field name.

For a trial, sum each category across all model rows.
The primary volume measure is:

~~~text
input_total = input_uncached + input_cache_write + input_cache_read
all_tokens = input_total + output
~~~

Input_total measures total input tokens processed across the whole task, including cache reads.
It is not a measure of uncached spend.
All_tokens is secondary because input and output have different economic weights.
The report shows each category alongside these derived totals.

Capture model calls, tool calls, retries, subagent use, result payload bytes, and wall time.
Include helper work charged to the experiment even when it occurs outside the visible main loop.
If the selected host does not expose complete totals, mark the study incapable of proving a total-token claim.

Counter evidence comes from actual completed model calls.
Token-count endpoints and tokenizer estimates can diagnose payloads, but cannot replace usage from the completed workflow.
Register a secondary cost-weighted estimate using dated provider prices for each model and disjoint input/cache/output category.
Keep per-model counts so different model prices are never applied to an already aggregated total.
State cache-write TTL and applicable batch or long-context pricing tiers; unknown categories make the estimate incomplete.
The formula is the sum of each measured category count multiplied by its frozen per-token price.
Do not import remembered prices or silently update the price table after outcomes are visible.
SDK total_cost_usd is a separate estimate, retained for comparison rather than substituted for missing category counts.
An economic claim requires separate billing reconciliation and must identify coverage and unavailable charges.
Subscription usage limits are not inferred from either token totals or a list-price estimate.

## 7. Trial result contract

The expanded driver must add `measurement/manifest.v3.schema.json` and `measurement/trial.v3.schema.json`.
Validate each version 3 record before writing or resuming it; preserve historical schema files and dispatch by their actual version.
These expanded contracts are not implemented by the existing revision 2 probe.
The record has:

- Identity: experiment_id, manifest_sha256, task_id, repetition, arm, trial_id.
- Execution: started_at, ended_at, model IDs, client/SDK versions, status, failure_code.
- Usage: usage_status, per-model category counts, call_count, per-tool counts, document-access adherence, SDK estimated cost, and the separately calculated price-weighted estimate.
- Local work: extraction_ms, reused_artifact, artifact_bytes, retrieval_ms, result_payload_bytes, and peak_rss_bytes when measured.
- Quality: answer_correct, required_qualifiers_present, citation_resolution_rate, citation_support_pass, refusal_correct, document_category, task_kind, and grading-projection identity.
- Evidence: relative references to the private raw transcript and reviewer rubric.

Unknown numerical observations use null and an explicit completeness state.
They do not use zero.
The public report projection excludes source text, filenames, filesystem paths, prompts, credentials, and raw transcripts.
Its task IDs resolve only within an owner-reviewed evidence pack.

The trial driver produces the record even after timeout or failure.
Prepare a separate grading projection that resolves evidence identifiers to physical pages, removes tool-specific boilerplate, and randomizes anonymous answer IDs.
Preserve raw answers and the reversible mapping privately for audit.
Do not remove OCR labels or wording needed to judge the answer.
A grader sees normalized answers without arm labels; disclose residual clues as partial blinding rather than claiming complete blinding.
Automated citation checks resolve evidence identifiers and exact quotes.
Human review decides whether the cited evidence supports the material claim.
Identifier validity alone does not establish semantic support.

## 8. Quality and token decision rules

The primary report keeps all 108 registered rows, including unrun rows with their reason.
A trial passes quality only when its answer is correct, required qualifiers are present, and all material citations support it.
For missing-fact tasks, a correctly scoped refusal is a successful answer.
Refusing an answerable task is a failure.

Compute quality separately for all three arms using the same planned denominator.
For the token comparison, pair C with A by task_id and repetition.
Show the number of planned, completed, quality-passing, and usage-complete pairs.
Do not quietly reduce the denominator to favorable pairs.

A token-reduction claim requires all of the following:

1. All three arms have complete measured usage, and all planned A/C pairs have completed execution.
2. C passes quality on at least 90% of its planned trials.
3. C's total quality-pass count is at least A's, with no document category or shared task kind showing a lower pass count.
4. Every citation in a C quality-passing answer resolves correctly and supports its material claim.
5. Among jointly quality-passing pairs, median C/A input_total is at most 0.50.
6. Total C input_total across all planned pairs is lower than total A input_total.
7. The report discloses output tokens, cache categories, latency, failures, and any individual regressions.

The 50% threshold is a proposed proof target, not an observed result.
The stricter total-input condition prevents cheap failures from carrying the headline.
The quality conditions prevent a retrieval system that reads too little from appearing efficient.

For each comparable pair:

~~~text
reduction_fraction = 1 - C.input_total / A.input_total
~~~

If A.input_total is zero or unknown, the fraction is unavailable.
Do not replace it with 100%.
The report shows median paired ratios, totals, ranges, and per-task rows.
With this small synthetic set, avoid population-wide significance claims.

Interpret outcomes explicitly:

| Outcome | Allowed statement |
| --- | --- |
| Installation passes, measurements absent | Local installation and cited retrieval work on the tested host. |
| Quality passes, reduction target fails | OpenReading provides local document processing with verifiable page citations; this study does not establish token savings. |
| C saves against A but not B | This study supports preprocessing benefits over the tested ordinary-tools workflow; it does not establish an additional selective-retrieval saving over full extraction. |
| C saves tokens against B but not A | Selective retrieval improves on full-text ingestion, but ordinary tools remain competitive. |
| C saves tokens and meets every rule | On this named task set and environment, measured input tokens fell by the reported amount at the reported quality. |
| A cannot complete an input | The workflow expands accessible work in that case; no savings percentage is computed for it. |
| Usage is incomplete | The study reports partial observations and makes no total-token claim. |

## 9. Offline accounting fixtures

These fixtures belong in public tests and contain no real conversation.

| Fixture | Required result |
| --- | --- |
| Two assistant records share message ID m1 | Diagnostic input totals count m1 once. |
| Two cumulative result snapshots contain 100 then 150 input tokens | One query call contributes 150, not 250. |
| Main loop uses 100 and a child uses 50 input tokens | Whole-tree count is 150 without adding the child a second time. |
| A successful call uses 40 uncached, 10 cache-write, 50 cache-read, and 8 output tokens | input_total is 100 and all_tokens is 108. |
| A failed call has a valid final per-model usage record | Usage counts toward the experiment and quality fails. |
| A crash emits a zeroed result after nonzero activity | usage_status is incomplete, not a zero-cost success. |
| An arm has missing usage on one registered trial | The report refuses the total-token claim. |
| C has lower usage but omits a required exception | Quality fails and that row cannot support the paired headline. |
| Dataset or prompt changes after approval | Live runner refuses the stale manifest hash. |

## 10. Proof report and public handoff

The private evidence pack contains the frozen manifest, dataset hashes, raw SDK logs, local execution observations,
quality reviews, normalized trial records, and the generated report.
Reviewers can trace a reported total back to the measured calls.
No report numbers are copied manually into a badge.

The public artifact is a reviewed projection stating:

- Tested model, SDK, client, OS, architecture, runtime digest, and date.
- Task-set construction, size, quality rubric, and baseline tool inventory.
- Complete counts, paired results, cache/output totals, latency, and failures.
- Installation steps actually tested and the number of observed pilot users.
- Exact claim supported, unsupported claims, and access to public synthetic reproduction material.

Publishing is a separate owner decision.
The implementation agent stops after producing reviewable artifacts and a passing verification record.

## 11. Accounting references

Checked on 2026-09-10:

- [Claude Agent SDK usage accounting](https://code.claude.com/docs/en/agent-sdk/cost-tracking) defines final totals, cache fields, nested work, and incomplete crash accounting.
- [Claude Agent SDK TypeScript reference](https://code.claude.com/docs/en/agent-sdk/typescript) is the field-level reference to pin alongside fixtures.
- [Anthropic token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting) describes estimates before a completed request.
- [Anthropic PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support) explains why native PDF input and clean text are different representations.

## Baseline availability carried into revision 2

Keep the ordinary-tools baseline usable before any paid trial, including the M0 probe.
Every arm receives the same compact extraction recipes for its document, counted in actual input usage.
The recipes include saving the extraction as a working-directory file, so ordinary Grep and ranged Read can search it.
Freeze the utility executable hash and absolute command paths with the environment and manifest.
Preflight extraction before querying and require new preparation when the machine or utility changes.
Retain exact command matching instead of introducing a general shell-command parser.
Record tool calls and permission denials; a baseline Bash denial makes the C/A savings outcome ineligible.
A model choosing Read without a denial remains a valid baseline choice.
The revision 1 runner implements these protections, but its records do not establish revision 2 evidence.

## 12. Provider extension under revision 4

This section specifies future revision 4 intent, not the implemented revision 2 Claude M0 driver.
Preserve both historical manifest families and their validators without relabeling prior trials.
Any new provider driver uses a new closed version 3 manifest and trial schema.
The broader Claude study described above also adopts version 3 when implemented, instead of creating another incompatible version 2 family.

The first provider adapter remains the existing Claude Agent SDK workflow.
The next adapter should target a named OpenAI execution surface whose complete usage and tool access can be verified.
Evaluate instrumented Codex first because it supplies an ordinary coding-agent baseline.
An OpenAI Responses harness is an explicit alternative if its full local tool loop and usage semantics are proven.
It must be labeled an API harness and cannot stand in for ChatGPT desktop behavior.
Choosing that alternative changes the registered baseline and requires review before paid calls.

Keep shared preparation, scheduling, quality review, evidence validation, and reporting independent of provider SDKs.
Each adapter must implement environment validation, trial execution, raw-event capture, usage normalization, and supported cancellation/budget controls.
SDK imports and model identifier rules belong inside their adapter, not the document runtime or core.
Provider-specific raw events remain authoritative for replay; a shared summary never replaces them.

The proposed version 3 manifest adds `provider_id`, `execution_surface`, `adapter_revision`, and `usage_contract_revision`.
It records exact model, SDK and client versions, engine identity, tool inventory, account label, prices, and approved finite limits.
No unrestricted provider string or generic model regex silently selects an untested adapter.
Runtime/source identity, raw-event resume checks, and explicit approval remain at least as strict as the existing M0 driver.
A provider without complete accounting remains functional-only and cannot pass token acceptance.

Run A, B, and C within the same provider, model, execution surface, and policy.
A gets usable ordinary search and page access; B and C share the identical extraction and page projection.
Maintain the reviewed file-output baseline recipe and equivalent citation information across arms.
Do not inherit an unavailable Claude tool name into an OpenAI baseline or compare different permissions as if they were equivalent.
Report physical pages and actual extracted characters; provider-token sizes require that provider's verified tokenizer or usage records.
Page counts alone do not represent document size.

Validate each provider's counters from official documentation and pinned SDK fixtures before defining normalization.
Fixtures must cover cache inclusion, reasoning/output overlap, cumulative snapshots, retries, failures, nested work, and missing totals.
Do not assume another provider uses Claude's disjoint cache counters or final-result accounting unit.
Deduplicate by verified request identity and preserve model-specific rows.
Missing usage is unknown, not zero, and no fabricated counter may complete a trial.
Report input volume, output volume, cached usage, cost estimates, and latency separately.

Keep frozen-price checks independent of an SDK's cost estimate and stop on an unpriced model.
Where the provider cannot enforce an in-flight monetary limit, disclose that limitation and bound request/turn/output limits before execution.
A local estimate is not an absolute billing guarantee; observed overruns stop subsequent work.
Approval binds the exact provider manifest and never transfers a Claude budget to an OpenAI run.

Human review must pass both compared answers before reporting any favorable direction.
Retain failed, limited, incomplete, mixed-access, and unrun trials with their reasons.
Report C adherence and quality against the full preregistered denominator.
Do not pool provider token counts or savings ratios into a universal “works with any assistant” claim.
Native-chat quotas, hidden orchestration, and billing remain unmeasured unless that exact surface exposes complete evidence.

### Codex isolation, authentication, and limits

Before implementing a Codex study adapter, complete E6 in the [native probe plan](native-probes.md).
A writable workspace restriction does not establish a read restriction.
The trial must be unable to read ground truth, other arms' extractions, earlier events, personal instructions, or unrelated MCP registrations.
Place those files outside the trial's readable boundary and verify denial with planted sentinels.
If the selected sandbox permits their reads, use verified OS-level isolation or stop the study.
Do not disable ordinary search, pipes, or local utilities inside the allowed workspace to make Arm A less capable.

Give each trial a fresh state directory using the pinned CLI's supported `CODEX_HOME` mechanism in that child process only.
Keep the parent agent's environment and the user's shared configuration untouched.
Use a task-specific path variable in the harness; never repurpose the user's home directory.
An isolated state directory alone does not prove isolation from ancestor `AGENTS.md`, project configuration, skills, or managed settings.
Start outside repository instruction hierarchies and record the effective inherited configuration and instruction sources.
A planted global/project instruction or unrelated MCP server must not reach the trial.
The workspace contains the granted synthetic source and writable scratch, with each arm's intended tools supplied explicitly.
Run OpenReading through a separately controlled process with evidence access; the model receives only bounded tool responses.
Verify that the model cannot read the privileged process's store or log through its own tools.
Record the effective sandbox, approval settings, runtime permissions, and authenticated model endpoint.

The first Codex measurement adapter requires explicit API-key authentication for a named account and exact model.
It refuses silent fallback to an existing ChatGPT login or subscription quota.
Bind the account using the existing salted per-study fingerprint convention without retaining the key.
If the pinned CLI cannot demonstrate that authentication path, the paid Codex driver remains blocked.
Quota-based studies require a separately reviewed contract and cannot inherit this dollar-budget interpretation.

Do not assume the CLI exposes dollar, turn, or output ceilings because another SDK does.
Require a finite external wall-clock watchdog, owned-process cleanup, maximum scheduled trials, and frozen-price estimates from verified usage.
Use any additional turn/output/request caps only after the pinned interface and a regression fixture prove they work.
Stop subsequent trials on an overrun, missing usage, unexpected model, or unpriced category.
Termination may not cancel a provider request already accepted; a watchdog does not guarantee a monetary ceiling.
Before approval, display the verified controls, missing in-flight controls, and residual billing risk alongside the finite estimated study budget.
If that risk exceeds the owner's authorization, do not launch the trial or silently use quota authentication.

The existing Claude M0 remains a diagnostic developer study under its frozen 300-second engine safeguards and its own trial limits.
Its registered document sizes need not fit a later native release cap.
Report over-cap documents as diagnostic-only and never transfer that result into a packaged-client support claim.
Scored native or packaged studies must use a corpus that fits their reviewed profile and host limits before approval.
