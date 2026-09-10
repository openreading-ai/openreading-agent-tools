import assert from "node:assert/strict";
import test from "node:test";
import { buildReport } from "../../measurement/report.mjs";

const manifest = {
  schema_version: "1",
  study_kind: "primary",
  task_ids: Array.from({ length: 12 }, (_, i) => `task${i}`),
  repetitions: 3,
  arms: ["A", "B", "C"],
};
const trials = () =>
  manifest.task_ids.flatMap((task_id) =>
    Array.from({ length: 3 }, (_, repetition) =>
      manifest.arms.map((arm) => ({
        task_id,
        arm,
        repetition,
        category: "agreement",
        state: "completed",
        baseline: { utility_verified: true, bash_denials: 0 },
        usage: {
          complete: true,
          input_total: arm === "C" ? 40 : 100,
          output: 10,
          input_cache_read: 0,
          input_cache_write: 0,
          input_uncached: arm === "C" ? 40 : 100,
        },
        quality: { passed: true, citation_valid: true },
        wall_ms: 100,
      })),
    ).flat(),
  );

test("complete matched quality can support the narrow input-token threshold", () => {
  const report = buildReport(manifest, trials());
  assert.equal(report.claim.supported, true);
  assert.equal(report.claim.median_c_over_a, 0.4);
  assert.equal(report.rows.length, 108);
});

test("missing planned trials remain visible and block the claim", () => {
  const report = buildReport(manifest, trials().slice(1));
  assert.equal(report.rows.length, 108);
  assert.equal(report.rows[0].state, "unrun");
  assert.equal(report.claim.supported, false);
});

test("cheap wrong answers, incomplete usage and zero denominator cannot pass", () => {
  for (const mutate of [
    (rows) => (rows[2].quality.passed = false),
    (rows) => (rows[2].usage.complete = false),
    (rows) => (rows[0].usage.input_total = 0),
    (rows) => (rows[2].quality.citation_valid = false),
  ]) {
    const rows = trials();
    mutate(rows);
    assert.equal(buildReport(manifest, rows).claim.supported, false);
  }
});

test("failed calls count usage and duplicate trial identities are refused", () => {
  const rows = trials();
  rows[0].state = "failed";
  const report = buildReport(manifest, rows);
  assert.equal(report.arms.A.input_total, 3600);
  assert.equal(report.claim.supported, false);
  assert.throws(() => buildReport(manifest, [...rows, rows[0]]), /Duplicate/);
});

test("calibration cannot support a primary claim and reports contain no raw text", () => {
  const rows = trials();
  rows[0].raw_events = "private-text";
  const report = buildReport({ ...manifest, study_kind: "calibration" }, rows);
  assert.equal(report.claim.supported, false);
  assert.equal(JSON.stringify(report).includes("private-text"), false);
});

test("incomplete diagnostic arm usage also blocks the registered claim", () => {
  const rows = trials();
  rows[1].usage.complete = false;
  assert.equal(buildReport(manifest, rows).claim.supported, false);
});

test("a constrained or unverified baseline cannot support savings", () => {
  for (const baseline of [
    undefined,
    { utility_verified: false, bash_denials: 0 },
    { utility_verified: true, bash_denials: 1 },
  ]) {
    const rows = trials();
    rows[0].baseline = baseline;
    const report = buildReport(manifest, rows);
    assert.equal(report.claim.supported, false);
    assert.equal(report.claim.median_c_over_a, null);
  }
});

test("unrun rows use the frozen dataset category instead of inventing one", () => {
  const dataset = {
    tasks: manifest.task_ids.map((id) => ({ id, category: "agreement" })),
  };
  const report = buildReport(manifest, [], dataset);
  assert.ok(report.rows.every((row) => row.category === "agreement"));
  assert.ok(
    buildReport(manifest, []).rows.every((row) => row.category === null),
  );
});
