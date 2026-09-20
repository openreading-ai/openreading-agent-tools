import { fixture } from "./fixture.mjs";
import assert from "node:assert/strict";
import test from "node:test";
import {
  mkdirSync,
  writeFileSync,
  rmSync,
  readFileSync,
  chmodSync,
} from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";
import {
  validateRun,
  plannedTrials,
  runTrial,
} from "../../measurement/run.mjs";
import { normalizeQuery } from "../../measurement/accounting.mjs";

const hash = (data) => createHash("sha256").update(data).digest("hex");

/** Store a completed trial whose record matches its raw result event. */
function recordTrial(directory, record, cost, inputTokens) {
  const event = {
    type: "result",
    subtype: "success",
    total_cost_usd: cost,
    modelUsage: {
      model: {
        inputTokens,
        cacheCreationInputTokens: 0,
        cacheReadInputTokens: 0,
        outputTokens: 1,
      },
    },
  };
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, "events.jsonl"), JSON.stringify(event) + "\n");
  writeFileSync(
    join(directory, "trial.json"),
    JSON.stringify({ ...record, usage: normalizeQuery([event]) }),
  );
}

test("dry validation checks every frozen input and deterministic complete schedule", (t) => {
  const { path } = fixture(t);
  const run = validateRun(path);
  assert.equal(plannedTrials(run).length, 12);
  assert.deepEqual(plannedTrials(run), plannedTrials(run));
  assert.equal(run.liveApproved, false);
});

test("changed manifest hash, changed dataset and escaped paths refuse execution", (t) => {
  const { root, path, manifest } = fixture(t);
  assert.throws(() => validateRun(path, "0".repeat(64)), /approval/);
  writeFileSync(join(root, "source.pdf"), "changed");
  assert.throws(() => validateRun(path), /hash/);
  manifest.prompt_file = "../private";
  writeFileSync(path, JSON.stringify(manifest));
  assert.throws(() => validateRun(path), /path|hash/);
});

test("frozen plugin configuration cannot change after manifest approval", (t) => {
  const { root, path, manifest } = fixture(t);
  writeFileSync(join(root, "plugin/mcp.json"), "{}");
  const environment = JSON.stringify({
    plugin_files: { "plugin/mcp.json": hash("{}") },
  });
  writeFileSync(join(root, "environment.json"), environment);
  manifest.environment_sha256 = hash(environment);
  writeFileSync(path, JSON.stringify(manifest));
  validateRun(path);
  writeFileSync(join(root, "plugin/mcp.json"), '{"changed":true}');
  assert.throws(() => validateRun(path), /hash/);
});

test("report-only rebuilds all planned rows without approval or model calls", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const { root, path } = fixture(t);
  await main([path, "--report"], {
    query: () => {
      throw new Error("model invoked");
    },
  });
  const report = JSON.parse(readFileSync(join(root, "runs/test/report.json")));
  assert.equal(report.rows.length, 12);
  assert.equal(report.claim.supported, false);
});

test("an added plugin hook cannot enter a frozen experiment", (t) => {
  const { root, path, manifest } = fixture(t);
  const environment = JSON.stringify({ plugin_files: {} });
  writeFileSync(join(root, "environment.json"), environment);
  manifest.environment_sha256 = hash(environment);
  writeFileSync(path, JSON.stringify(manifest));
  validateRun(path);
  writeFileSync(join(root, "plugin/hooks.json"), "{}");
  assert.throws(() => validateRun(path), /plugin inventory/);
});

test("changed or undiscoverable baseline utilities refuse validation", (t) => {
  const { path, executable } = withBaseline(t);
  validateRun(path);
  writeFileSync(executable, "changed");
  assert.throws(() => validateRun(path), /baseline/i);
});

test("baseline recipes must describe the complete frozen allowlist", (t) => {
  const { path, manifest } = withBaseline(t);
  manifest.allowed_bash_commands.pop();
  writeFileSync(path, JSON.stringify(manifest));
  assert.throws(() => validateRun(path), /baseline/i);
});

function rewrite(data, name, value) {
  const text = JSON.stringify(value);
  writeFileSync(join(data.root, name), text);
  const field = {
    "environment.json": "environment_sha256",
    "dataset.json": "dataset_sha256",
    "plugin/server/release.json": "runtime_sha256",
  }[name];
  if (field) data.manifest[field] = hash(text);
  writeFileSync(data.path, JSON.stringify(data.manifest));
}
const resultEvent = (cost = 0.1) => ({
  type: "result",
  subtype: "success",
  total_cost_usd: cost,
  modelUsage: {
    model: {
      inputTokens: 20,
      cacheCreationInputTokens: 0,
      cacheReadInputTokens: 0,
      outputTokens: 2,
    },
  },
});

function freezeEnvironment(data, extra = {}) {
  const environment = JSON.parse(
    readFileSync(join(data.root, "environment.json")),
  );
  rewrite(data, "environment.json", {
    ...environment,
    plugin_files: {},
    package_lock_sha256: hash(
      readFileSync(new URL("../../package-lock.json", import.meta.url)),
    ),
    measurement_source_sha256: hash(
      Buffer.concat(
        ["run.mjs", "accounting.mjs", "report.mjs"].map((name) =>
          readFileSync(new URL(`../../measurement/${name}`, import.meta.url)),
        ),
      ),
    ),
    account_key_sha256: hash("synthetic-offline-key"),
    ...extra,
  });
}

test("nested runtime files and internal symlinks must match the frozen inventory", async (t) => {
  const { symlinkSync } = await import("node:fs");
  const data = fixture(t);
  const dir = join(data.root, "plugin/server");
  mkdirSync(join(dir, "lib"));
  writeFileSync(join(dir, "lib/native"), "native");
  symlinkSync("lib/native", join(dir, "alias"));
  const release = JSON.parse(readFileSync(join(dir, "release.json")));
  release.files["lib/native"] = {
    length: 6,
    sha256: hash("native"),
    executable: false,
  };
  release.files.alias = { symlink: "lib/native" };
  rewrite(data, "plugin/server/release.json", release);
  validateRun(data.path);
  release.files.alias.symlink = "wrong";
  rewrite(data, "plugin/server/release.json", release);
  assert.throws(() => validateRun(data.path), /symlink/);
  release.files.alias.symlink = "lib/native";
  delete release.files["lib/native"];
  rewrite(data, "plugin/server/release.json", release);
  assert.throws(() => validateRun(data.path), /Unlisted/);
});

test("validation refuses unfrozen tasks, changed engine, and invalid study limits", (t) => {
  const data = fixture(t);
  const original = { ...data.manifest };
  for (const change of [
    { model_id: "latest" },
    { max_trials: 11 },
    { repetitions: 2 },
    { task_ids: ["task0"] },
    { core_commit: "b".repeat(40) },
    { client_sha256: "0".repeat(64) },
    { sdk_version: "0.0.1" },
  ]) {
    data.manifest = { ...original, ...change };
    writeFileSync(data.path, JSON.stringify(data.manifest));
    assert.throws(() => validateRun(data.path));
  }
  data.manifest = original;
  const dataset = JSON.parse(readFileSync(join(data.root, "dataset.json")));
  dataset.tasks[0].document = "unfrozen.pdf";
  rewrite(data, "dataset.json", dataset);
  assert.throws(() => validateRun(data.path), /unfrozen/);
});

test("evidence under Git and changed measurement code or dependency lock are refused", (t) => {
  const data = fixture(t);
  mkdirSync(join(data.root, ".git"));
  assert.throws(() => validateRun(data.path), /Git repository/);
  rmSync(join(data.root, ".git"), { recursive: true });
  freezeEnvironment(data);
  validateRun(data.path);
  freezeEnvironment(data, { package_lock_sha256: "0".repeat(64) });
  assert.throws(() => validateRun(data.path), /dependency lock/);
  freezeEnvironment(data, { measurement_source_sha256: "0".repeat(64) });
  assert.throws(() => validateRun(data.path), /source hash/);
});

test("primary study schedules all 108 trials and refuses malformed task inventories", (t) => {
  const data = fixture(t);
  const dataset = JSON.parse(readFileSync(join(data.root, "dataset.json")));
  const template = dataset.tasks[0];
  dataset.tasks = Array.from({ length: 12 }, (_, index) => ({
    ...template,
    id: `task${index}`,
  }));
  Object.assign(data.manifest, {
    study_kind: "primary",
    task_ids: dataset.tasks.map((task) => task.id),
    repetitions: 3,
    max_trials: 108,
    max_estimated_usd_total: 100,
  });
  rewrite(data, "dataset.json", dataset);
  const run = validateRun(data.path);
  assert.equal(plannedTrials(run).length, 108);
  dataset.tasks.pop();
  rewrite(data, "dataset.json", dataset);
  assert.throws(() => validateRun(data.path), /tasks/);
});

test("baseline recipe shape and bounds are validated before execution", (t) => {
  const data = withBaseline(t);
  const original = JSON.parse(
    readFileSync(join(data.root, "environment.json")),
  );
  for (const change of [
    { whole: 1 },
    { page: "missing placeholder" },
    { pages: 0 },
    { pages: 101 },
    { pages: 1.5 },
  ]) {
    const environment = structuredClone(original);
    Object.assign(environment.baseline.recipes["source.pdf"], change);
    rewrite(data, "environment.json", environment);
    assert.throws(() => validateRun(data.path), /baseline/i);
  }
  const environment = structuredClone(original);
  delete environment.baseline.recipes["source.pdf"];
  rewrite(data, "environment.json", environment);
  assert.throws(() => validateRun(data.path), /baseline/i);
});

function withBaseline(t) {
  const data = fixture(t),
    { root, path, manifest } = data;
  const executable = join(root, "pdftotext");
  writeFileSync(executable, "#!/bin/sh\nprintf 'source text\\n'\n");
  chmodSync(executable, 0o755);
  const whole = `${executable} ${join(root, "source.pdf")} -`;
  const page = `${executable} -f {page} -l {page} ${join(root, "source.pdf")} -`;
  manifest.allowed_bash_commands = [whole, page.replaceAll("{page}", "1")];
  const environment = {
    baseline: {
      executable,
      sha256: hash(readFileSync(executable)),
      recipes: { "source.pdf": { whole, page, pages: 1 } },
    },
  };
  writeFileSync(join(root, "environment.json"), JSON.stringify(environment));
  manifest.environment_sha256 = hash(JSON.stringify(environment));
  writeFileSync(path, JSON.stringify(manifest));
  return { ...data, executable, whole, page };
}

test("historical replay checks raw usage and manifest binding and releases its lock", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const data = fixture(t);
  const run = validateRun(data.path);
  const task = plannedTrials(run)[0];
  const trialDir = join(
    data.root,
    "runs/test",
    `${task.task_id}-${task.repetition}-${task.arm}`,
  );
  const record = {
    ...task,
    state: "completed",
    schema_version: "1",
    manifest_sha256: run.manifestHash,
    baseline: { utility_verified: true, bash_denials: 0 },
    quality: { passed: true, citation_valid: true },
  };
  recordTrial(trialDir, record, 1, 100);
  await main([data.path, "--report"]);
  let report = JSON.parse(
    readFileSync(join(data.root, "runs/test/report.json")),
  );
  assert.equal(report.execution, "disabled");
  assert.equal(
    report.rows.filter((row) => row.state === "completed").length,
    1,
  );
  const stored = JSON.parse(readFileSync(join(trialDir, "trial.json")));
  stored.usage.estimated_usd = 0;
  writeFileSync(join(trialDir, "trial.json"), JSON.stringify(stored));
  await assert.rejects(main([data.path, "--report"]), /raw events/);
  recordTrial(trialDir, { ...record, manifest_sha256: "wrong" }, 1, 100);
  await assert.rejects(main([data.path, "--report"]), /another manifest/);
  recordTrial(trialDir, record, 1, 100);
  await main([data.path, "--report"]);
});

test("historical report replay needs records, not the original executable or installed dependencies", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const data = fixture(t);
  freezeEnvironment(data, {
    package_lock_sha256: "0".repeat(64),
    measurement_source_sha256: "0".repeat(64),
  });
  rmSync(data.manifest.client_path);
  await main([data.path, "--report"]);
  const report = JSON.parse(
    readFileSync(join(data.root, "runs/test/report.json")),
  );
  assert.equal(report.execution, "disabled");
  assert.equal(report.claim.supported, false);
  assert.match(report.scope, /not Desktop/);
  writeFileSync(join(data.root, "source.pdf"), "changed");
  await assert.rejects(main([data.path, "--report"]), /hash/);
});

test("offline help and validation never grant execution authority", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const data = fixture(t);
  assert.equal(await main([]), 0);
  assert.equal(await main(["--help"]), 0);
  assert.equal(await main([data.path]), 0);
  assert.equal(
    validateRun(data.path, hash(readFileSync(data.path))).liveApproved,
    false,
  );
});
