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

const hash = (data) => createHash("sha256").update(data).digest("hex");

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
        [
          "Grep",
          {
            pattern: "secret",
            path: root,
            file_path: join(root, "source.pdf"),
          },
        ],
        ["Glob", { pattern: "{../../private,*.txt}" }],
        ["Read", { file_path: join(options.cwd, "escape/environment.json") }],
        ["Glob", { pattern: "**/*.txt", path: join(options.cwd, "escape") }],
      ])
        decisions.push((await options.canUseTool(name, input)).behavior);
      yield { type: "result", subtype: "success" };
    },
  });
  assert.deepEqual(decisions, [
    "allow",
    "deny",
    "deny",
    "deny",
    "deny",
    "deny",
  ]);
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
  const missingRun = validateRun(
    missing.path,
    hash(readFileSync(missing.path)),
  );
  await assert.rejects(
    runTrial(missingRun, plannedTrials(missingRun)[0]),
    /verified local PDF baseline/,
  );
  const { path, executable, root, manifest } = withBaseline(t);
  writeFileSync(executable, "#!/bin/sh\nexit 0\n");
  const environment = JSON.parse(readFileSync(join(root, "environment.json")));
  environment.baseline.sha256 = hash(readFileSync(executable));
  writeFileSync(join(root, "environment.json"), JSON.stringify(environment));
  manifest.environment_sha256 = hash(JSON.stringify(environment));
  writeFileSync(path, JSON.stringify(manifest));
  const run = validateRun(path, hash(readFileSync(path)));
  let called = false;
  await assert.rejects(
    runTrial(run, plannedTrials(run)[0], {
      query: async function* () {
        called = true;
      },
    }),
    /produced no text/,
  );
  assert.equal(called, false);
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

test("all arms carry their intended input and plugin configuration", async (t) => {
  for (const arm of ["A", "B", "C"]) {
    const data = fixture(t);
    const run = validateRun(data.path, hash(readFileSync(data.path)));
    const trial = await runTrial(
      run,
      plannedTrials(run).find((task) => task.arm === arm),
      {
        query: async function* ({ prompt, options }) {
          assert.equal(options.permissionMode, "default");
          assert.equal(
            (
              await options.canUseTool("Read", {
                file_path: "/missing-evidence-file",
              })
            ).behavior,
            "deny",
          );
          assert.equal(
            (await options.canUseTool("mcp__openreading__read_document", {}))
              .behavior,
            "allow",
          );
          assert.equal(
            (
              await options.canUseTool(
                "mcp__plugin_openreading-local-proof_openreading__search_document",
                {},
              )
            ).behavior,
            "allow",
          );
          assert.equal(
            (await options.canUseTool("Write", { file_path: "secret" }))
              .behavior,
            "deny",
          );
          if (arm === "C") {
            assert.deepEqual(options.plugins, [
              { type: "local", path: run.paths.plugin },
            ]);
            assert.equal(
              options.settings.pluginConfigs["openreading-local-proof"].options
                .input_root,
              data.root,
            );
          } else assert.equal(options.plugins, undefined);
          assert.ok(prompt.includes("When?"));
          yield resultEvent();
        },
      },
    );
    assert.equal(trial.state, "completed");
    assert.equal(trial.permission_denials.Read, 1);
  }
});

test("query exceptions and oversized event streams produce failed retained trials", async (t) => {
  for (const oversized of [false, true]) {
    const data = fixture(t);
    const run = validateRun(data.path, hash(readFileSync(data.path)));
    let signal;
    const trial = await runTrial(run, plannedTrials(run)[0], {
      query: async function* ({ options }) {
        signal = options.abortController.signal;
        if (oversized)
          yield { type: "assistant", data: "x".repeat(51 * 1024 * 1024) };
        else throw new Error("synthetic SDK failure");
      },
    });
    assert.equal(trial.state, oversized ? "timeout" : "failed");
    assert.equal(trial.usage.complete, false);
    assert.equal(signal.aborted, true);
  }
});

test("deadline abort stops a stalled SDK trial", async (t) => {
  const data = fixture(t);
  data.manifest.timeout_seconds_per_trial = 1;
  writeFileSync(data.path, JSON.stringify(data.manifest));
  const run = validateRun(data.path, hash(readFileSync(data.path)));
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let aborted;
  const trial = await runTrial(run, plannedTrials(run)[0], {
    query: async function* ({ options }) {
      t.mock.timers.tick(1001);
      aborted = options.abortController.signal.aborted;
      throw new Error("SDK request aborted");
    },
  });
  assert.equal(aborted, true);
  assert.equal(trial.state, "timeout");
});

test("live startup refuses missing key, unfrozen sources, wrong account, and wrong client", async (t) => {
  let sdkCalls = 0;
  t.mock.module("@anthropic-ai/claude-agent-sdk", {
    namedExports: {
      query: async function* () {
        sdkCalls++;
        throw new Error("SDK execution must remain blocked");
      },
    },
  });
  const original = process.env.ANTHROPIC_API_KEY;
  t.after(() => {
    if (original === undefined) delete process.env.ANTHROPIC_API_KEY;
    else process.env.ANTHROPIC_API_KEY = original;
  });
  for (const stage of ["key", "freeze", "account", "client"]) {
    const data = withBaseline(t);
    writeFileSync(
      join(data.root, "client"),
      "#!/bin/sh\necho 'wrong-version'\n",
    );
    chmodSync(join(data.root, "client"), 0o755);
    data.manifest.client_sha256 = hash(readFileSync(join(data.root, "client")));
    writeFileSync(data.path, JSON.stringify(data.manifest));
    delete process.env.ANTHROPIC_API_KEY;
    if (stage !== "key")
      process.env.ANTHROPIC_API_KEY = "synthetic-offline-key";
    if (["account", "client"].includes(stage))
      freezeEnvironment(
        data,
        stage === "account" ? { account_key_sha256: "wrong" } : {},
      );
    const run = validateRun(data.path, hash(readFileSync(data.path)));
    await assert.rejects(runTrial(run, plannedTrials(run)[0]), {
      message: new RegExp(
        {
          key: "account key",
          freeze: "frozen",
          account: "fingerprint",
          client: "client version",
        }[stage],
      ),
    });
  }
  assert.equal(sdkCalls, 0);
});

test("approved live startup loads only the mocked SDK and passes the bounded budget", async (t) => {
  const data = withBaseline(t);
  writeFileSync(join(data.root, "client"), "#!/bin/sh\necho '2.1.266 test'\n");
  chmodSync(join(data.root, "client"), 0o755);
  data.manifest.client_sha256 = hash(readFileSync(join(data.root, "client")));
  writeFileSync(data.path, JSON.stringify(data.manifest));
  freezeEnvironment(data);
  const previous = process.env.ANTHROPIC_API_KEY;
  process.env.ANTHROPIC_API_KEY = "synthetic-offline-key";
  t.after(() => {
    if (previous === undefined) delete process.env.ANTHROPIC_API_KEY;
    else process.env.ANTHROPIC_API_KEY = previous;
  });
  let calls = 0;
  t.mock.module("@anthropic-ai/claude-agent-sdk", {
    namedExports: {
      query: async function* ({ options }) {
        calls++;
        assert.equal(options.maxBudgetUsd, 0.25);
        yield resultEvent();
      },
    },
  });
  const run = validateRun(data.path, hash(readFileSync(data.path)));
  const trial = await runTrial(run, plannedTrials(run)[0], {
    remainingBudget: 0.25,
  });
  assert.equal(calls, 1);
  assert.equal(trial.state, "completed");
});

test("CLI help and invalid approval modes cannot start a query", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  assert.equal(await main([]), 0);
  const { path } = fixture(t);
  await assert.rejects(main([path, "--live"]), /approved manifest/);
  await assert.rejects(main([path, "--live", "--report"]), /Choose/);
});

test("resumption skips completed trials and stops exactly at the remaining budget", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const data = fixture(t);
  data.manifest.max_estimated_usd_total = 1;
  data.manifest.max_estimated_usd_per_trial = 1;
  writeFileSync(data.path, JSON.stringify(data.manifest));
  const run = validateRun(data.path);
  const first = plannedTrials(run)[0];
  const dir = join(
    data.root,
    "runs/test",
    `${first.task_id}-${first.repetition}-${first.arm}`,
  );
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    join(dir, "trial.json"),
    JSON.stringify({
      ...first,
      category: "agreement",
      manifest_sha256: run.manifestHash,
      state: "completed",
      usage: { complete: true, input_total: 20, estimated_usd: 0.75 },
      quality: { passed: null, citation_valid: null },
    }),
  );
  let calls = 0;
  await main(
    [data.path, "--live", "--approved-manifest-sha256", run.manifestHash],
    {
      query: async function* ({ options }) {
        calls++;
        assert.equal(options.maxBudgetUsd, 0.25);
        yield resultEvent(0.25);
      },
    },
  );
  assert.equal(calls, 1);
  const report = JSON.parse(
    readFileSync(join(data.root, "runs/test/report.json")),
  );
  assert.equal(
    report.rows.filter((row) => row.state === "completed").length,
    2,
  );
});

test("incomplete usage prevents the next trial and releases the study lock", async (t) => {
  const { main } = await import("../../measurement/run.mjs");
  const data = fixture(t);
  const approval = hash(readFileSync(data.path));
  let calls = 0;
  await main([data.path, "--live", "--approved-manifest-sha256", approval], {
    query: async function* () {
      calls++;
      yield { type: "result", subtype: "success" };
    },
  });
  assert.equal(calls, 1);
  await main([data.path, "--report"]);
  const run = validateRun(data.path),
    task = plannedTrials(run)[0];
  const record = join(
    data.root,
    "runs/test",
    `${task.task_id}-${task.repetition}-${task.arm}`,
    "trial.json",
  );
  const trial = JSON.parse(readFileSync(record));
  trial.manifest_sha256 = "other";
  writeFileSync(record, JSON.stringify(trial));
  await assert.rejects(main([data.path, "--report"]), /another manifest/);
  trial.manifest_sha256 = approval;
  writeFileSync(record, JSON.stringify(trial));
  await main([data.path, "--report"]);
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

test("unplanned trials refuse even with an approved manifest", async (t) => {
  const data = fixture(t),
    run = validateRun(data.path, hash(readFileSync(data.path)));
  for (const task of [
    { task_id: "absent", arm: "A", repetition: 0 },
    { ...plannedTrials(run)[0], repetition: 99 },
  ]) {
    await assert.rejects(
      runTrial(run, task, {
        query: async function* () {
          throw new Error("query must not run");
        },
      }),
      /Unplanned/,
    );
  }
});
