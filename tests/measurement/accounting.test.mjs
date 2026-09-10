import assert from "node:assert/strict";
import test from "node:test";
import { normalizeQuery } from "../../measurement/accounting.mjs";

const usage = (input, output = 8) => ({
  inputTokens: input,
  cacheCreationInputTokens: 10,
  cacheReadInputTokens: 50,
  outputTokens: output,
  costUSD: 0.01,
});
const result = (input, extra = {}) => ({
  type: "result",
  subtype: "success",
  modelUsage: { model: usage(input) },
  total_cost_usd: 0.01,
  ...extra,
});

test("latest cumulative snapshot wins without counting assistant copies", () => {
  const normalized = normalizeQuery([
    {
      type: "assistant",
      message: { id: "same", usage: { input_tokens: 999 } },
    },
    result(100),
    { type: "assistant", message: { id: "same" } },
    result(150),
  ]);
  assert.equal(normalized.input_uncached, 150);
  assert.equal(normalized.input_total, 210);
  assert.equal(normalized.all_tokens, 218);
  assert.equal(normalized.duplicate_message_ids, 1);
});

test("whole-query per-model usage includes children exactly once", () => {
  const normalized = normalizeQuery([
    result(40, {
      usage: { input_tokens: 999 },
      modelUsage: {
        main: usage(40),
        child: {
          ...usage(50, 2),
          cacheCreationInputTokens: 0,
          cacheReadInputTokens: 0,
        },
      },
    }),
  ]);
  assert.equal(normalized.input_total, 150);
  assert.equal(normalized.output, 10);
});

test("valid failed trial usage counts but missing and zero crash usage are incomplete", () => {
  assert.equal(
    normalizeQuery([result(40, { subtype: "error_max_turns" })]).complete,
    true,
  );
  for (const events of [
    [],
    [{ type: "result", subtype: "error_during_execution", modelUsage: {} }],
    [
      result(0, {
        subtype: "error_during_execution",
        modelUsage: {
          model: {
            inputTokens: 0,
            cacheCreationInputTokens: 0,
            cacheReadInputTokens: 0,
            outputTokens: 0,
          },
        },
      }),
    ],
  ]) {
    const normalized = normalizeQuery(events);
    assert.equal(normalized.complete, false);
    assert.equal(normalized.input_total, null);
  }
});

test("missing cache counters and counter rollback cannot become zero usage", () => {
  assert.equal(
    normalizeQuery([
      result(10, {
        modelUsage: { model: { inputTokens: 10, outputTokens: 2 } },
      }),
    ]).complete,
    false,
  );
  assert.equal(normalizeQuery([result(100), result(50)]).complete, false);
});
