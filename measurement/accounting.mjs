/** Normalize one SDK query from its last cumulative modelUsage snapshot.
 * The pinned SDK includes main-loop, subagent and query-pipeline helper calls here.
 * Helpers outside that pipeline are not covered; this is not a billing statement.
 * Assistant-message copies and top-level usage are diagnostics, never additional totals.
 */
const fields = {
  input_uncached: "inputTokens",
  input_cache_write: "cacheCreationInputTokens",
  input_cache_read: "cacheReadInputTokens",
  output: "outputTokens",
};
const empty = {
  complete: false,
  input_uncached: null,
  input_cache_write: null,
  input_cache_read: null,
  input_total: null,
  output: null,
  all_tokens: null,
  estimated_usd: null,
};

export function normalizeQuery(events) {
  const ids = new Set();
  const toolIds = new Set(),
    toolCalls = {};
  let duplicates = 0;
  let previous = null;
  let final = null;
  let invalid = false;
  for (const event of events) {
    const id = event.type === "assistant" ? event.message?.id : null;
    if (id) {
      if (ids.has(id)) duplicates++;
      ids.add(id);
    }
    if (event.type === "assistant")
      for (const block of event.message?.content ?? []) {
        if (
          block.type === "tool_use" &&
          typeof block.id === "string" &&
          typeof block.name === "string" &&
          !toolIds.has(block.id)
        ) {
          toolIds.add(block.id);
          toolCalls[block.name] = (toolCalls[block.name] ?? 0) + 1;
        }
      }
    if (event.type !== "result") continue;
    final = event;
    const models = event.modelUsage;
    if (!models || typeof models !== "object" || !Object.keys(models).length) {
      invalid = true;
      continue;
    }
    const sums = Object.fromEntries(Object.keys(fields).map((key) => [key, 0]));
    for (const usage of Object.values(models)) {
      for (const [key, native] of Object.entries(fields)) {
        const value = usage?.[native];
        if (!Number.isSafeInteger(value) || value < 0) invalid = true;
        else sums[key] += value;
      }
    }
    if (previous && Object.keys(sums).some((key) => sums[key] < previous[key]))
      invalid = true;
    previous = sums;
  }
  const diagnostics = {
    duplicate_message_ids: duplicates,
    tool_calls: toolCalls,
    status: final?.subtype ?? "missing_result",
    accounting_scope:
      "SDK query pipeline; excludes helpers outside that pipeline",
  };
  if (
    !final ||
    !previous ||
    invalid ||
    Object.values(previous).every((value) => value === 0)
  )
    return { ...empty, ...diagnostics };
  const input =
    previous.input_uncached +
    previous.input_cache_write +
    previous.input_cache_read;
  return {
    ...previous,
    complete: true,
    input_total: input,
    all_tokens: input + previous.output,
    estimated_usd:
      Number.isFinite(final.total_cost_usd) && final.total_cost_usd >= 0
        ? final.total_cost_usd
        : null,
    ...diagnostics,
  };
}
