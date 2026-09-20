import assert from "node:assert/strict";
import test from "node:test";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { main, runTrial, validateRun, digest } from "../../measurement/run.mjs";
import { fixture } from "./fixture.mjs";

const refusal = /Provider API trials are disabled/;

test("live CLI refuses before reading a manifest even with old approval flags", async () => {
  for (const argv of [
    ["missing.json", "--live"],
    ["missing.json", "--live", "--approved-manifest-sha256", "a".repeat(64)],
    ["missing.json", "--report", "--live"],
    ["--help", "--live"],
  ])
    await assert.rejects(main(argv), refusal);
  const result = spawnSync(
    process.execPath,
    ["measurement/run.mjs", "missing.json", "--live"],
    {
      encoding: "utf8",
      env: { PATH: process.env.PATH, ANTHROPIC_API_KEY: "synthetic-not-a-key" },
    },
  );
  assert.equal(result.status, 1);
  assert.match(result.stderr, refusal);
  assert.doesNotMatch(result.stderr, /synthetic-not-a-key/);
});

test("direct trial execution refuses even an approved manifest and injected transport", async (t) => {
  const { path } = fixture(t);
  const run = validateRun(path, digest(readFileSync(path)));
  let calls = 0;
  await assert.rejects(
    runTrial(
      run,
      { task_id: run.manifest.task_ids[0], arm: "A", repetition: 0 },
      {
        query: async function* () {
          calls++;
          yield { type: "result", subtype: "success" };
        },
      },
    ),
    refusal,
  );
  assert.equal(calls, 0);
});
