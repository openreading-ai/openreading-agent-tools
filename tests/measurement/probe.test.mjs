import assert from "node:assert/strict";
import test from "node:test";
import { fixture } from "./fixture.mjs";
import {
  validateRun,
  plannedTrials,
  runTrial,
  main,
  digest,
  charge,
} from "../../measurement/run.mjs";
import { buildReport } from "../../measurement/report.mjs";
import { writeFileSync, readFileSync, chmodSync, existsSync } from "node:fs";
import { join } from "node:path";

function probeFixture(t) {
  const f = fixture(t);
  const put = (name, data) => {
    const text = typeof data === "string" ? data : JSON.stringify(data);
    writeFileSync(join(f.root, name), text);
    return digest(text);
  };
  const dataset = JSON.parse(readFileSync(join(f.root, "dataset.json")));
  dataset.tasks = dataset.tasks.slice(0, 3).map((task, i) => ({
    ...task,
    category: ["agreement", "manual", "report"][i],
    task_kind: "single_fact",
  }));
  f.manifest.dataset_sha256 = put("dataset.json", dataset);
  Object.assign(f.manifest, {
    schema_version: "2",
    spec_revision: 2,
    study_kind: "probe",
    runtime_kind: "developer_harness",
    task_ids: ["task0", "task1", "task2"],
    max_trials: 9,
    max_estimated_usd_total: 5,
    max_estimated_usd_per_trial: 0.5,
    timeout_seconds_per_trial: 600,
    retriever_revision: "lexical-v3-dehyphenated",
  });
  delete f.manifest.runtime_dir;
  delete f.manifest.plugin_dir;
  const runtime =
    JSON.stringify({
      environment: { core_commit: "a".repeat(40) },
      engine: { extraction_settings: { retriever: "lexical-v3-dehyphenated" } },
    }) + "\n";
  const executable = "#!/bin/sh\nprintf '%s' '" + runtime + "'\n";
  f.manifest.source_python = join(f.root, "python");
  f.manifest.source_python_sha256 = put("python", executable);
  chmodSync(f.manifest.source_python, 0o755);
  const contents = {
    runtime,
    profile: { docling: { ocr: false } },
    retrieval: {
      passed: true,
      environment: { core_commit: "a".repeat(40) },
      generation: {},
      documents: Object.fromEntries(
        ["agreement", "manual", "report"].map((name) => [
          name,
          {
            engine: {
              extraction_settings: { retriever: "lexical-v3-dehyphenated" },
            },
          },
        ]),
      ),
      tasks: Array.from({ length: 9 }, (_, i) => ({
        task_id: `positive${i}`,
        passed: true,
      })),
    },
    restart: { passed: true },
    lock: "lock",
    generation: {},
    pricing: {
      model_id: f.manifest.model_id,
      source: "https://platform.claude.com/docs/en/about-claude/pricing",
      checked_on: "2026-09-11",
      usd_per_million: { input: 1, cache_write: 1, cache_read: 1, output: 1 },
    },
  };
  for (const [name, content] of Object.entries(contents)) {
    if (name === "restart")
      content.retrieval_report_sha256 = f.manifest.retrieval_sha256;
    f.manifest[`${name}_file`] = `${name}.json`;
    f.manifest[`${name}_sha256`] = put(`${name}.json`, content);
  }
  f.save = () => writeFileSync(f.path, JSON.stringify(f.manifest));
  f.put = put;
  f.save();
  return f;
}

const result = {
  type: "result",
  subtype: "success",
  num_turns: 2,
  total_cost_usd: 0.1,
  modelUsage: {
    "claude-sonnet-4-6": {
      inputTokens: 10,
      cacheCreationInputTokens: 2,
      cacheReadInputTokens: 3,
      outputTokens: 4,
    },
  },
};

test("probe validates the source engine and has exactly nine frozen trials", (t) => {
  const f = probeFixture(t);
  const run = validateRun(f.path);
  assert.equal(plannedTrials(run).length, 9);
  assert.equal(run.manifest.runtime_kind, "developer_harness");
  const legacy = fixture(t);
  Object.assign(legacy.manifest, {
    schema_version: "2",
    spec_revision: 2,
    study_kind: "probe",
  });
  writeFileSync(legacy.path, JSON.stringify(legacy.manifest));
  assert.throws(() => validateRun(legacy.path), /schema/);
});

test("probe refuses interpreter, environment, pricing and task drift", (t) => {
  const f = probeFixture(t);
  const original = structuredClone(f.manifest);
  for (const mutation of [
    (m) => (m.source_python = "relative"),
    (m) => (m.source_python_sha256 = "f".repeat(64)),
    (m) => (m.core_commit = "b".repeat(40)),
  ]) {
    f.manifest = structuredClone(original);
    mutation(f.manifest);
    f.save();
    assert.throws(() => validateRun(f.path));
  }
  f.manifest = structuredClone(original);
  f.manifest.runtime_sha256 = f.put("runtime.json", "changed");
  f.save();
  assert.throws(() => validateRun(f.path), /environment changed/);
  f.manifest = structuredClone(original);
  f.put(
    "runtime.json",
    JSON.stringify({
      environment: { core_commit: "a".repeat(40) },
      engine: { extraction_settings: { retriever: "lexical-v3-dehyphenated" } },
    }) + "\n",
  );
  for (const prices of [
    { model_id: "wrong" },
    {
      model_id: f.manifest.model_id,
      source: "https://unverified.example",
      checked_on: "2026-09-11",
    },
    {
      model_id: f.manifest.model_id,
      source: "https://platform.claude.com/pricing",
      checked_on: "bad",
    },
    {
      model_id: f.manifest.model_id,
      source: "https://platform.claude.com/pricing",
      checked_on: "2026-09-11",
      usd_per_million: { input: -1 },
    },
  ]) {
    f.manifest.pricing_sha256 = f.put("pricing.json", prices);
    f.save();
    assert.throws(() => validateRun(f.path), /pricing/);
  }
  const good = probeFixture(t);
  const data = JSON.parse(readFileSync(join(good.root, "dataset.json")));
  data.tasks[2].category = "agreement";
  good.manifest.dataset_sha256 = good.put("dataset.json", data);
  good.save();
  assert.throws(() => validateRun(good.path), /single-fact/);
  data.tasks[2].category = "report";
  data.tasks[2].task_kind = "missing_fact";
  good.manifest.dataset_sha256 = good.put("dataset.json", data);
  good.save();
  assert.throws(() => validateRun(good.path), /single-fact/);
});

test("probe reports direction with all failed and unrun observations retained", (t) => {
  const f = probeFixture(t);
  const data = JSON.parse(readFileSync(join(f.root, "dataset.json")));
  const rows = ["A", "B", "C"].map((arm, i) => ({
    task_id: "task0",
    repetition: 0,
    arm,
    state: "completed",
    turns: 2,
    wall_ms: 3,
    usage: { complete: true, input_total: [100, 50, 25][i] },
    baseline: { utility_verified: true, bash_denials: 0 },
    quality: { passed: null, citation_valid: null },
  }));
  let report = buildReport(f.manifest, rows, data);
  // Unreviewed answers keep their usage visible but yield no direction.
  assert.equal(report.probe[0].c_over_a, null);
  assert.equal(report.probe[0].c_over_b, null);
  assert.equal(report.probe[0].observations[2].usage.input_total, 25);
  rows.forEach((row) => (row.quality.passed = true));
  rows[2].quality.passed = false;
  report = buildReport(f.manifest, rows, data);
  assert.equal(report.probe[0].c_over_a, null);
  rows[2].quality.passed = true;
  report = buildReport(f.manifest, rows, data);
  assert.equal(report.probe[0].c_over_a, 0.25);
  assert.equal(report.probe[0].c_over_b, 0.5);
  assert.equal(report.rows.length, 9);
  assert.equal(report.claim.supported, false);
  rows[0].baseline.bash_denials = 1;
  rows[1].usage.input_total = 0;
  report = buildReport(f.manifest, rows, data);
  assert.equal(report.probe[0].c_over_a, null);
  assert.equal(report.probe[0].c_over_b, null);
  rows[0].baseline.bash_denials = 0;
  rows[2].state = "failed";
  report = buildReport(f.manifest, rows, data);
  assert.equal(report.probe[0].c_over_a, null);
});

test("probe refuses a failed or changed retrieval prerequisite", (t) => {
  for (const change of ["failed", "ocr", "generation", "restart", "unbound"]) {
    const f = probeFixture(t);
    const key =
      change === "ocr"
        ? "profile"
        : change === "restart" || change === "unbound"
          ? "restart"
          : "retrieval";
    const value = JSON.parse(readFileSync(join(f.root, `${key}.json`)));
    if (change === "ocr") value.docling.ocr = true;
    else if (change === "generation") value.generation = { changed: true };
    else if (change === "unbound")
      value.retrieval_report_sha256 = "0".repeat(64);
    else value.passed = false;
    f.manifest[`${key}_sha256`] = f.put(`${key}.json`, value);
    f.save();
    assert.throws(() => validateRun(f.path), /retrieval gate/);
  }
});

test("probe ordering matches the frozen Python preparation schedule", (t) => {
  const f = probeFixture(t);
  f.manifest.order_seed = 20260911;
  assert.deepEqual(
    plannedTrials({ manifest: f.manifest }).map((t) => t.arm),
    ["C", "A", "B", "C", "B", "A", "A", "B", "C"],
  );
});

test("the closed probe schema accepts the actual frozen corpus task identifiers", (t) => {
  const f = probeFixture(t);
  const data = JSON.parse(readFileSync(join(f.root, "dataset.json")));
  data.tasks.forEach((task) => {
    task.id = `${task.category}-single_fact`;
  });
  f.manifest.task_ids = data.tasks.map((t) => t.id);
  f.manifest.dataset_sha256 = f.put("dataset.json", data);
  f.save();
  assert.equal(plannedTrials(validateRun(f.path)).length, 9);
});

function withBaseline(f, recipe) {
  const utility = join(f.root, "pdftotext");
  const script = "#!/bin/sh\nprintf 'page text'\n";
  writeFileSync(utility, script);
  chmodSync(utility, 0o755);
  const quoted = (value) => `'${value}'`;
  const source = quoted(join(f.root, "source.pdf"));
  const recipes = {
    whole: `${utility} ${source} -`,
    page: `${utility} -f {page} -l {page} ${source} -`,
    file: `${utility} ${source} source.txt`,
    pages: 2,
    ...recipe,
  };
  for (const key of Object.keys(recipes))
    if (recipes[key] === undefined) delete recipes[key];
  f.manifest.environment_sha256 = f.put("environment.json", {
    baseline: {
      executable: utility,
      sha256: digest(script),
      recipes: { "source.pdf": recipes },
    },
  });
  f.manifest.allowed_bash_commands = [
    recipes.whole,
    ...(recipes.file ? [recipes.file] : []),
    ...[1, 2].map((n) => recipes.page.replaceAll("{page}", String(n))),
  ];
  f.save();
  return recipes;
}

test("the probe schema accepts exact current model identifiers and refuses aliases", (t) => {
  for (const [model, accepted] of [
    ["claude-opus-5", true],
    ["claude-sonnet-4-6", true],
    ["claude-fable-5-1", true],
    ["claude-haiku-4-5-20251001", true],
    ["claude-opus-latest", false],
    ["claude-sonnet", false],
  ]) {
    const f = probeFixture(t);
    f.manifest.model_id = model;
    f.manifest.pricing_sha256 = f.put("pricing.json", {
      ...JSON.parse(readFileSync(join(f.root, "pricing.json"))),
      model_id: model,
    });
    f.save();
    if (accepted) assert.equal(validateRun(f.path).manifest.model_id, model);
    else assert.throws(() => validateRun(f.path), /schema/);
  }
});

test("probe reports text size, access adherence, and the actual SDK stop reason", (t) => {
  const f = probeFixture(t);
  const dataset = JSON.parse(readFileSync(join(f.root, "dataset.json")));
  dataset.tasks[0].document_size = {
    physical_pages: 80,
    extracted_characters: 37000,
    baseline_characters: 39000,
  };
  const rows = ["A", "B", "C"].map((arm) => ({
    task_id: "task0",
    repetition: 0,
    arm,
    state: "failed",
    usage: {
      complete: true,
      input_total: 10,
      status: "error_max_turns",
      tool_calls:
        arm === "C" ? { mcp__openreading__openreading_read: 2 } : { Read: 1 },
    },
  }));
  let report = buildReport(f.manifest, rows, dataset);
  assert.equal(report.probe[0].document_size.extracted_characters, 37000);
  assert.equal(report.rows[0].stop_reason, "error_max_turns");
  assert.equal(report.probe_adherence.plugin_only, 1);
  assert.equal(report.probe_adherence.fraction_of_planned, 1 / 3);
  rows[2].usage.tool_calls.Grep = 1;
  report = buildReport(f.manifest, rows, dataset);
  assert.equal(report.probe_adherence.mixed, 1);
  assert.equal(report.probe_adherence.plugin_only, 0);
});

test("account fingerprints use a per-study salt without changing historical records", async () => {
  const { accountFingerprint } = await import("../../measurement/run.mjs");
  const key = "synthetic-test-key";
  assert.equal(accountFingerprint(key, {}, "1"), digest(key));
  assert.throws(() => accountFingerprint(key, {}, "2"), /salted/);
  const first = accountFingerprint(
    key,
    { account_key_salt: "a".repeat(64) },
    "2",
  );
  assert.equal(first, digest("a".repeat(64) + "\0" + key));
  assert.notEqual(
    first,
    accountFingerprint(key, { account_key_salt: "b".repeat(64) }, "2"),
  );
});

test("C artifacts must match the frozen engine, source, and full extraction", async (t) => {
  const { verifyTrialArtifacts } = await import("../../measurement/run.mjs");
  const { mkdirSync } = await import("node:fs");
  const f = probeFixture(t);
  const run = validateRun(f.path);
  const trialRoot = join(f.root, "trial");
  assert.deepEqual(verifyTrialArtifacts(run, trialRoot), []);
  mkdirSync(join(trialRoot, "artifacts"), { recursive: true });
  const retrieval = JSON.parse(readFileSync(run.paths.retrieval));
  retrieval.generation.files = { "agreement.pdf": "source-hash" };
  retrieval.documents.agreement.full_text_sha256 = "text-hash";
  writeFileSync(run.paths.retrieval, JSON.stringify(retrieval));
  const record = {
    source_relative_path: "agreement.pdf",
    document_sha256: "source-hash",
    full_text_sha256: "text-hash",
    engine: retrieval.documents.agreement.engine,
  };
  const write = (rows) =>
    writeFileSync(
      run.manifest.source_python,
      "#!/bin/sh\nprintf '%s' '" + JSON.stringify(rows) + "'\n",
    );
  write([record]);
  assert.deepEqual(verifyTrialArtifacts(run, trialRoot), [record]);
  for (const changed of [
    { ...record, engine: {} },
    { ...record, document_sha256: "bad" },
    { ...record, full_text_sha256: "bad" },
    { ...record, source_relative_path: "other.pdf" },
  ]) {
    write([changed]);
    assert.throws(() => verifyTrialArtifacts(run, trialRoot), /differs/);
  }
  write({});
  assert.throws(() => verifyTrialArtifacts(run, trialRoot), /differs/);
});

test("an unpriced helper model cannot masquerade as a conservative cost estimate", async (t) => {
  const { trialUsage } = await import("../../measurement/run.mjs");
  const run = validateRun(probeFixture(t).path);
  const usage = trialUsage(run, [
    {
      ...result,
      total_cost_usd: 0,
      modelUsage: {
        ...result.modelUsage,
        expensive_unknown: result.modelUsage["claude-sonnet-4-6"],
      },
    },
  ]);
  assert.equal(usage.complete, true);
  assert.equal(usage.frozen_price_usd, null);
  assert.deepEqual(usage.unpriced_models, ["expensive_unknown"]);
  assert.equal(charge({ schema_version: "2", usage }), null);
});

test("historical probe reporting reads the captured environment without executing it", async (t) => {
  const f = probeFixture(t);
  const marker = join(f.root, "executed");
  writeFileSync(
    f.manifest.source_python,
    `#!/bin/sh\ntouch '${marker}'\nexit 7\n`,
  );
  await main([f.path, "--report"]);
  assert.equal(existsSync(marker), false);
  const report = JSON.parse(
    readFileSync(join(f.root, "runs/test/report.json")),
  );
  assert.equal(report.execution, "disabled");
  assert.equal(report.rows.length, 9);
});

test("historical priced usage remains conservative and missing counters remain unknown", async (t) => {
  const { trialUsage } = await import("../../measurement/run.mjs");
  const f = probeFixture(t);
  const run = validateRun(f.path);
  const usage = trialUsage(run, [result]);
  assert.equal(usage.frozen_price_usd, 19 / 1e6);
  assert.equal(charge({ schema_version: "2", usage }), 0.1);
  assert.equal(charge({ schema_version: "1", usage }), 0.1);
  assert.equal(
    charge({
      schema_version: "2",
      usage: { ...usage, frozen_price_usd: null },
    }),
    null,
  );
  assert.equal(
    charge({ schema_version: "1", usage: { complete: false } }),
    null,
  );
  assert.equal(trialUsage(run, []).complete, false);
});
