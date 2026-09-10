/** Build a complete, redacted report from planned trials and reviewed quality labels.
 * Missing or incomplete trials remain visible. Usage on failed calls still counts.
 * Unverified or Bash-constrained baselines cannot produce a primary savings ratio.
 * Human quality review is an input, not a result inferred from cheap token usage.
 */
const identity = (row) => `${row.task_id}:${row.repetition}:${row.arm}`;
const validInput = (row) =>
  row.usage?.complete === true &&
  Number.isSafeInteger(row.usage.input_total) &&
  row.usage.input_total >= 0;
const pass = (row) => row.state === "completed" && row.quality?.passed === true;
const median = (values) => {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

export function buildReport(manifest, trials, dataset) {
  const taskCategories = new Map(
    (dataset?.tasks ?? []).map((task) => [task.id, task.category]),
  );
  const indexed = new Map();
  for (const trial of trials) {
    const key = identity(trial);
    if (indexed.has(key)) throw new Error(`Duplicate trial identity: ${key}`);
    indexed.set(key, trial);
  }
  const rows = [];
  for (const task_id of manifest.task_ids)
    for (let repetition = 0; repetition < manifest.repetitions; repetition++)
      for (const arm of ["A", "B", "C"]) {
        const key = identity({ task_id, repetition, arm });
        const trial = indexed.get(key);
        indexed.delete(key);
        rows.push({
          task_id,
          repetition,
          arm,
          category: taskCategories.get(task_id) ?? trial?.category ?? null,
          baseline: trial?.baseline
            ? {
                utility_verified: trial.baseline.utility_verified === true,
                bash_denials: trial.baseline.bash_denials ?? null,
              }
            : null,
          state: trial?.state ?? "unrun",
          usage: trial
            ? {
                complete: validInput(trial),
                input_uncached: trial.usage?.input_uncached ?? null,
                input_cache_write: trial.usage?.input_cache_write ?? null,
                input_cache_read: trial.usage?.input_cache_read ?? null,
                input_total: trial.usage?.input_total ?? null,
                output: trial.usage?.output ?? null,
              }
            : null,
          quality: trial
            ? {
                passed: trial.quality?.passed ?? null,
                citation_valid: trial.quality?.citation_valid ?? null,
              }
            : null,
          wall_ms: trial?.wall_ms ?? null,
        });
      }
  if (indexed.size)
    throw new Error("Trial records include unplanned identities.");
  const arms = {};
  for (const arm of ["A", "B", "C"]) {
    const selected = rows.filter((row) => row.arm === arm);
    const known = selected.filter(validInput);
    const sum = (field) =>
      known.reduce((total, row) => total + (row.usage[field] ?? 0), 0);
    arms[arm] = {
      planned: selected.length,
      completed: selected.filter((row) => row.state === "completed").length,
      quality_passed: selected.filter(pass).length,
      usage_complete: known.length,
      input_total: known.length === selected.length ? sum("input_total") : null,
      known_input_total: sum("input_total"),
      output: known.length === selected.length ? sum("output") : null,
      input_cache_read:
        known.length === selected.length ? sum("input_cache_read") : null,
      input_cache_write:
        known.length === selected.length ? sum("input_cache_write") : null,
      median_wall_ms: median(
        selected
          .filter((row) => Number.isFinite(row.wall_ms))
          .map((row) => row.wall_ms),
      ),
    };
  }
  const ratios = [],
    diagnostic = [];
  let completePairs = true;
  for (const task of manifest.task_ids)
    for (let repetition = 0; repetition < manifest.repetitions; repetition++) {
      const pair = rows.filter(
        (row) => row.task_id === task && row.repetition === repetition,
      );
      const [a, b, c] = ["A", "B", "C"].map((arm) =>
        pair.find((row) => row.arm === arm),
      );
      if (
        ![a, c].every((row) => row.state === "completed" && validInput(row)) ||
        a.usage?.input_total === 0
      )
        completePairs = false;
      if (
        [a, c].every((row) => pass(row) && validInput(row)) &&
        a.usage.input_total > 0
      )
        ratios.push(c.usage.input_total / a.usage.input_total);
      if (
        [b, c].every((row) => pass(row) && validInput(row)) &&
        b.usage.input_total > 0
      )
        diagnostic.push(c.usage.input_total / b.usage.input_total);
    }
  const categories = [
    ...new Set(
      rows
        .filter((row) => row.arm !== "B" && row.category !== null)
        .map((row) => row.category),
    ),
  ];
  const categoryQuality = categories.every((category) => {
    const selected = rows.filter((row) => row.category === category);
    return (
      selected.filter((row) => row.arm === "C" && pass(row)).length >=
      selected.filter((row) => row.arm === "A" && pass(row)).length
    );
  });
  const conditions = {
    primary_design:
      manifest.study_kind === "primary" &&
      manifest.task_ids.length === 12 &&
      manifest.repetitions === 3,
    baseline_available: rows
      .filter((row) => row.arm === "A")
      .every(
        (row) =>
          row.baseline?.utility_verified === true &&
          row.baseline?.bash_denials === 0,
      ),
    complete_pairs: completePairs,
    complete_usage_all_arms: rows.every(validInput),
    quality_floor: arms.C.quality_passed / arms.C.planned >= 0.9,
    quality_not_worse:
      arms.C.quality_passed >= arms.A.quality_passed && categoryQuality,
    supported_citations: rows
      .filter((row) => row.arm === "C" && pass(row))
      .every((row) => row.quality.citation_valid === true),
    median_half_input: ratios.length > 0 && median(ratios) <= 0.5,
    total_input_lower:
      arms.A.input_total !== null &&
      arms.C.input_total !== null &&
      arms.C.input_total < arms.A.input_total,
  };
  return {
    schema_version: "1",
    study_kind: manifest.study_kind,
    rows,
    arms,
    claim: {
      supported: Object.values(conditions).every(Boolean),
      conditions,
      median_c_over_a: completePairs && conditions.baseline_available ? median(ratios) : null,
      diagnostic_median_c_over_b: median(diagnostic),
    },
    limitations: [
      "Synthetic fixed task set; no general token-savings or subscription-price claim.",
      "SDK query-pipeline accounting excludes helpers outside that pipeline.",
      "Quality and citation support require independent human review.",
      "Fresh sessions do not establish cold provider caches.",
    ],
  };
}
