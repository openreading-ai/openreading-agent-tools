import assert from "node:assert/strict";
import test from "node:test";
import {
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  rmSync,
  readFileSync,
  chmodSync,
  realpathSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createHash } from "node:crypto";
import {
  validateRun,
  plannedTrials,
  runTrial,
} from "../../measurement/run.mjs";

const hash = (data) => createHash("sha256").update(data).digest("hex");
export function fixture(t) {
  const root = realpathSync(
    mkdtempSync(join(tmpdir(), "openreading-measurement-")),
  );
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, "plugin/server"), { recursive: true });
  const task_ids = ["task0", "task1", "task2", "task3"];
  const dataset = {
    tasks: task_ids.map((id) => ({
      id,
      category: "agreement",
      question: "When?",
      document: "source.pdf",
      extraction: "source.txt",
    })),
    files: { "source.pdf": hash("pdf"), "source.txt": hash("text") },
  };
  const content = {
    "dataset.json": JSON.stringify(dataset),
    "prompt.txt": "Answer using cited evidence.",
    "skill.md": "Import and read.",
    "environment.json": "{}",
    "source.pdf": "pdf",
    "source.txt": "text",
    client: "client",
    "plugin/server/release.json": JSON.stringify({
      core_commit: "a".repeat(40),
      worker_sha256: hash("worker"),
      files: {
        "openreading-worker": {
          length: 6,
          sha256: hash("worker"),
          executable: true,
        },
      },
    }),
    "plugin/server/openreading-worker": "worker",
  };
  for (const [name, value] of Object.entries(content))
    writeFileSync(join(root, name), value);
  chmodSync(join(root, "plugin/server/openreading-worker"), 0o755);
  const manifest = {
    schema_version: "1",
    experiment_id: "test",
    spec_revision: 1,
    study_kind: "calibration",
    dataset_manifest: "dataset.json",
    dataset_sha256: hash(content["dataset.json"]),
    model_id: "claude-sonnet-4-6",
    client_path: join(root, "client"),
    client_sha256: hash("client"),
    client_version: "2.1.266",
    sdk_version: "0.3.267",
    core_commit: "a".repeat(40),
    runtime_dir: "plugin/server",
    runtime_sha256: hash(content["plugin/server/release.json"]),
    plugin_dir: "plugin",
    prompt_file: "prompt.txt",
    prompt_sha256: hash(content["prompt.txt"]),
    skill_file: "skill.md",
    skill_sha256: hash(content["skill.md"]),
    environment_file: "environment.json",
    environment_sha256: hash("{}"),
    arms: ["A", "B", "C"],
    task_ids,
    repetitions: 1,
    order_seed: 13,
    max_trials: 12,
    max_turns_per_trial: 12,
    timeout_seconds_per_trial: 180,
    max_estimated_usd_per_trial: 2,
    max_estimated_usd_total: 20,
    evidence_root: root,
    account_label: "approved-test-account",
    allowed_bash_commands: [],
  };
  const path = join(root, "manifest.json");
  writeFileSync(path, JSON.stringify(manifest));
  return { root, manifest, path };
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

test("unapproved run cannot invoke a model", async (t) => {
  const { path } = fixture(t);
  const run = validateRun(path);
  await assert.rejects(
    () =>
      runTrial(run, plannedTrials(run)[0], {
        query: () => {
          throw new Error("model invoked");
        },
      }),
    /approved/,
  );
});

test("approved fake query records real counters and failures without zero substitution", async (t) => {
  const { root, path } = fixture(t);
  const run = validateRun(path, hash(readFileSync(path)));
  const query = async function* () {
    yield {
      type: "result",
      subtype: "success",
      modelUsage: {
        model: {
          inputTokens: 40,
          cacheCreationInputTokens: 10,
          cacheReadInputTokens: 50,
          outputTokens: 8,
        },
      },
      total_cost_usd: 0.02,
    };
  };
  const trial = await runTrial(run, plannedTrials(run)[0], { query });
  assert.equal(trial.usage.input_total, 100);
  assert.equal(trial.quality.passed, null);
  assert.equal(trial.state, "completed");
  assert.ok(readFileSync(join(root, trial.evidence.events)).length);
});

test("a search pattern cannot read outside the granted evidence", async (t) => {
  const { root, path } = fixture(t);
  const run = validateRun(path, hash(readFileSync(path)));
  const decisions = {};
  const query = async function* ({ options }) {
    for (const [label, tool, input] of [
      ["absolute_glob", "Glob", { pattern: "/etc/**" }],
      ["escaping_glob", "Glob", { pattern: "../../**/*.pdf" }],
      ["home_glob", "Glob", { pattern: "~/Documents/**" }],
      ["escaping_grep", "Grep", { pattern: "secret", path: "../.." }],
      ["workspace_glob", "Glob", { pattern: "**/*.txt" }],
      ["granted_pdf", "Read", { file_path: join(root, "source.pdf") }],
    ])
      decisions[label] = (await options.canUseTool(tool, input)).behavior;
    yield {
      type: "result",
      subtype: "success",
      modelUsage: {
        model: {
          inputTokens: 40,
          cacheCreationInputTokens: 10,
          cacheReadInputTokens: 50,
          outputTokens: 8,
        },
      },
      total_cost_usd: 0.01,
    };
  };
  await runTrial(run, plannedTrials(run)[0], { query });
  assert.deepEqual(decisions, {
    absolute_glob: "deny",
    escaping_glob: "deny",
    home_glob: "deny",
    escaping_grep: "deny",
    workspace_glob: "allow",
    granted_pdf: "allow",
  });
});

test("resume accounts for later recorded trials before spending again", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const { root, path } = fixture(t),
    run = validateRun(path),
    schedule = plannedTrials(run);
  const later = schedule.at(-1),
    id = `${later.task_id}-${later.repetition}-${later.arm}`;
  const directory = join(root, "runs", "test", id);
  mkdirSync(directory, { recursive: true });
  writeFileSync(
    join(directory, "trial.json"),
    JSON.stringify({
      ...later,
      category: "agreement",
      manifest_sha256: run.manifestHash,
      state: "completed",
      usage: { complete: true, input_total: 100, estimated_usd: 20 },
      quality: { passed: null, citation_valid: null },
    }),
  );
  let calls = 0;
  await main([path, "--live", "--approved-manifest-sha256", run.manifestHash], {
    query: () => {
      calls++;
      throw new Error("must not spend");
    },
  });
  assert.equal(calls, 0);
  const report = JSON.parse(readFileSync(join(root, "runs/test/report.json")));
  assert.equal(report.rows.filter((row) => row.state === "unrun").length, 11);
});

test("an interrupted raw log blocks another paid attempt and dry CLI calls no model", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const { root, path } = fixture(t),
    run = validateRun(path),
    task = plannedTrials(run)[0];
  const directory = join(
    root,
    "runs",
    "test",
    `${task.task_id}-${task.repetition}-${task.arm}`,
  );
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, "events.jsonl"), "partial");
  let calls = 0;
  const query = () => {
    calls++;
    throw new Error("must not spend");
  };
  await main([path], { query });
  await main([path, "--live", "--approved-manifest-sha256", run.manifestHash], {
    query,
  });
  assert.equal(calls, 0);
  assert.equal(
    JSON.parse(readFileSync(join(root, "runs/test/report.json"))).claim
      .supported,
    false,
  );
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

test("search grants distinguish regex text, filename globs, and symlink targets", async (t) => {
  const { symlinkSync } = await import("node:fs");
  const { root, path } = fixture(t);
  const run = validateRun(path, hash(readFileSync(path)));
  const decisions = [];
  await runTrial(run, plannedTrials(run)[0], {
    query: async function* ({ options }) {
      symlinkSync(root, join(options.cwd, "escape"));
      for (const [name, input] of [
        [
          "Grep",
          { pattern: "/etc/../~literal", path: join(root, "source.pdf") },
        ],
        ["Grep", { pattern: "secret", glob: "/etc/**" }],
        ["Grep", { pattern: "secret", path: root, file_path: join(root, "source.pdf") }],
        ["Glob", { pattern: "{../../private,*.txt}" }],
        ["Read", { file_path: join(options.cwd, "escape/environment.json") }],
        ["Glob", { pattern: "**/*.txt", path: join(options.cwd, "escape") }],
      ])
        decisions.push((await options.canUseTool(name, input)).behavior);
      yield { type: "result", subtype: "success" };
    },
  });
  assert.deepEqual(decisions, ["allow", "deny", "deny", "deny", "deny", "deny"]);
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

test("baseline recipes are discoverable without disclosing 155 commands", async (t) => {
  const { path, whole, page } = withBaseline(t);
  const run = validateRun(path, hash(readFileSync(path)));
  const task = plannedTrials(run).find((trial) => trial.arm === "A");
  let seen;
  const trial = await runTrial(run, task, {
    query: async function* ({ prompt, options }) {
      seen = prompt;
      assert.equal(
        (await options.canUseTool("Bash", { command: whole })).behavior,
        "allow",
      );
      assert.equal(
        (
          await options.canUseTool("Bash", {
            command: whole + " | cat /etc/passwd",
          })
        ).behavior,
        "deny",
      );
      yield {
        type: "assistant",
        message: {
          id: "one",
          content: [
            {
              type: "tool_use",
              id: "call1",
              name: "Bash",
              input: { command: whole },
            },
          ],
        },
      };
      yield { type: "result", subtype: "success" };
    },
  });
  assert.ok(seen.includes(whole));
  assert.ok(seen.includes(page));
  assert.equal(trial.baseline.utility_verified, true);
  assert.equal(trial.baseline.bash_denials, 1);
  assert.equal(trial.usage.tool_calls.Bash, 1);
});

test("changed or undiscoverable baseline utilities refuse validation", (t) => {
  const { path, executable } = withBaseline(t);
  validateRun(path);
  writeFileSync(executable, "changed");
  assert.throws(() => validateRun(path), /baseline/i);
});


test("missing or empty baseline refuses before a live query", async (t) => {
  const missing = fixture(t);
  const missingRun = validateRun(missing.path, hash(readFileSync(missing.path)));
  await assert.rejects(runTrial(missingRun, plannedTrials(missingRun)[0]), /verified local PDF baseline/);
  const { path, executable, root, manifest } = withBaseline(t);
  writeFileSync(executable, "#!/bin/sh\nexit 0\n");
  const environment = JSON.parse(readFileSync(join(root, "environment.json")));
  environment.baseline.sha256 = hash(readFileSync(executable));
  writeFileSync(join(root, "environment.json"), JSON.stringify(environment));
  manifest.environment_sha256 = hash(JSON.stringify(environment));
  writeFileSync(path, JSON.stringify(manifest));
  const run = validateRun(path, hash(readFileSync(path)));
  let called = false;
  await assert.rejects(runTrial(run, plannedTrials(run)[0], {
    query: async function* () { called = true; },
  }), /produced no text/);
  assert.equal(called, false);
});

test("baseline recipes must describe the complete frozen allowlist", (t) => {
  const { path, manifest } = withBaseline(t);
  manifest.allowed_bash_commands.pop();
  writeFileSync(path, JSON.stringify(manifest));
  assert.throws(() => validateRun(path), /baseline/i);
});
