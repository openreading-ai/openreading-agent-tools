import assert from "node:assert/strict";
import test from "node:test";
import { fixture } from "./fixture.mjs";
import {
  validateRun,
  plannedTrials,
  runTrial,
  main,
  digest,
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
    retriever_revision: "lexical-v2-dehyphenated",
  });
  delete f.manifest.runtime_dir;
  delete f.manifest.plugin_dir;
  const runtime =
    JSON.stringify({
      environment: { core_commit: "a".repeat(40) },
      engine: { extraction_settings: { retriever: "lexical-v2-dehyphenated" } },
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
              extraction_settings: { retriever: "lexical-v2-dehyphenated" },
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
    model: {
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
      engine: { extraction_settings: { retriever: "lexical-v2-dehyphenated" } },
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

test("all arms preserve ordinary tools and C alone uses the selected MCP developer profile", async (t) => {
  const f = probeFixture(t);
  const run = validateRun(f.path, digest(readFileSync(f.path)));
  for (const arm of ["A", "B", "C"]) {
    const trial = await runTrial(
      run,
      { task_id: "task0", repetition: 0, arm },
      {
        query: async function* ({ prompt, options }) {
          assert.deepEqual(options.tools, ["Read", "Glob", "Grep", "Bash"]);
          assert.equal(options.maxBudgetUsd, 0.5);
          assert.equal(options.plugins, undefined);
          if (arm === "C") {
            assert.match(prompt, /Import and read/);
            assert.equal(
              options.mcpServers.openreading.command,
              "/usr/bin/sandbox-exec",
            );
            assert.ok(
              options.mcpServers.openreading.args.includes(run.paths.profile),
            );
            assert.ok(
              options.mcpServers.openreading.args.includes("--artifact-root"),
            );
          } else assert.equal(options.mcpServers, undefined);
          if (arm === "B") assert.match(prompt, /Complete local extraction/);
          yield result;
        },
      },
    );
    assert.equal(trial.schema_version, "2");
    assert.equal(trial.turns, 2);
    assert.equal(trial.usage.input_total, 15);
  }
  const report = buildReport(f.manifest, [], run.dataset);
  assert.equal(report.schema_version, "2");
  assert.equal(report.unscored, true);
  assert.equal(report.claim.supported, false);
  assert.equal(report.probe.length, 3);
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
  }));
  let report = buildReport(f.manifest, rows, data);
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

test("probe dry run makes no query and a nine-trial fixture honors the total cap", async (t) => {
  const f = probeFixture(t);
  let calls = 0;
  const query = async function* () {
    calls++;
    yield { ...result, total_cost_usd: 0.5 };
  };
  await main([f.path], { query });
  assert.equal(calls, 0);
  assert.equal(existsSync(join(f.root, "runs")), false);
  f.manifest.max_estimated_usd_total = 1;
  f.save();
  await main(
    [
      f.path,
      "--live",
      "--approved-manifest-sha256",
      digest(readFileSync(f.path)),
    ],
    { query },
  );
  assert.equal(calls, 2);
  const report = JSON.parse(
    readFileSync(join(f.root, "runs/test/report.json")),
  );
  assert.equal(report.rows.filter((r) => r.state === "unrun").length, 7);
  assert.equal(report.claim.supported, false);
});

test("probe refuses a failed or changed retrieval prerequisite", (t) => {
  for (const change of ["failed", "ocr", "generation", "restart"]) {
    const f = probeFixture(t);
    const key =
      change === "ocr"
        ? "profile"
        : change === "restart"
          ? "restart"
          : "retrieval";
    const value = JSON.parse(readFileSync(join(f.root, `${key}.json`)));
    if (change === "ocr") value.docling.ocr = true;
    else if (change === "generation") value.generation = { changed: true };
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
