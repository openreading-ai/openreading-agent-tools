/** Execute only an explicitly approved, frozen synthetic experiment.
 * Every arm receives frozen PDF extraction recipes. Utility preflight precedes queries.
 * Filename filters and canonical targets bound base-tool grants, not content regexes.
 * Dry validation does not import the model SDK or perform network calls.
 * A manifest hash authorizes one account label and bounded SDK-estimated spend.
 * The SDK cap is not a hard billing cap: an in-flight request can exceed it.
 * Failed or incomplete usage stops scheduling instead of assuming unspent budget.
 */
import { createHash } from "node:crypto";
import {
  appendFileSync,
  closeSync,
  existsSync,
  lstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  readdirSync,
  readlinkSync,
  realpathSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";
import Ajv2020 from "ajv/dist/2020.js";
import { normalizeQuery } from "./accounting.mjs";
import { buildReport } from "./report.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const schema = JSON.parse(readFileSync(join(HERE, "manifest.schema.json")));
const validate = new Ajv2020({ allErrors: true, strict: true }).compile(schema);
export const digest = (value) =>
  createHash("sha256").update(value).digest("hex");
const fileHash = (path) => digest(readFileSync(path));

function contained(root, value) {
  if (
    typeof value !== "string" ||
    isAbsolute(value) ||
    value.split(/[\\/]/).some((part) => ["", ".", ".."].includes(part))
  )
    throw new Error("Invalid evidence path.");
  const path = join(root, value);
  const real = realpathSync(path);
  if (real !== path || !real.startsWith(root + sep))
    throw new Error("Evidence path escapes its root or uses a symlink.");
  return path;
}
function checkedFile(root, name, hash) {
  const path = contained(root, name);
  if (!lstatSync(path).isFile() || fileHash(path) !== hash)
    throw new Error("Frozen input hash mismatch.");
  return path;
}
function runtimeInventory(root, metadata) {
  const names = [];
  function walk(directory) {
    for (const name of readdirSync(directory)) {
      const path = join(directory, name),
        rel = relative(root, path),
        stat = lstatSync(path);
      if (rel === "release.json") continue;
      if (stat.isDirectory() && !stat.isSymbolicLink()) {
        walk(path);
        continue;
      }
      names.push(rel);
      const entry = metadata.files[rel];
      if (!entry) throw new Error("Unlisted runtime file.");
      if (stat.isSymbolicLink()) {
        if (
          readlinkSync(path) !== entry.symlink ||
          !realpathSync(path).startsWith(root + sep)
        )
          throw new Error("Runtime symlink mismatch.");
      } else if (
        !stat.isFile() ||
        stat.size !== entry.length ||
        fileHash(path) !== entry.sha256 ||
        Boolean(stat.mode & 0o111) !== entry.executable
      )
        throw new Error("Runtime file hash mismatch.");
    }
  }
  walk(root);
  if (names.length !== Object.keys(metadata.files).length)
    throw new Error("Missing runtime file.");
}

function baselineInventory(environment, manifest, dataset) {
  const baseline = environment.baseline;
  if (baseline == null) return null;
  try {
    if (
      !isAbsolute(baseline.executable) ||
      fileHash(baseline.executable) !== baseline.sha256
    )
      throw new Error();
    const commands = [];
    for (const document of new Set(
      dataset.tasks.map((task) => task.document),
    )) {
      const recipe = baseline.recipes[document];
      if (
        !recipe ||
        typeof recipe.whole !== "string" ||
        typeof recipe.page !== "string" ||
        !recipe.page.includes("{page}") ||
        !Number.isSafeInteger(recipe.pages) ||
        recipe.pages < 1 ||
        recipe.pages > 100
      )
        throw new Error();
      commands.push(recipe.whole);
      for (let page = 1; page <= recipe.pages; page++)
        commands.push(recipe.page.replaceAll("{page}", String(page)));
    }
    if (
      JSON.stringify([...new Set(commands)].sort()) !==
      JSON.stringify([...manifest.allowed_bash_commands].sort())
    )
      throw new Error();
    return baseline;
  } catch {
    throw new Error(
      "Frozen baseline utility or command recipes changed. Prepare a new study.",
    );
  }
}

function baselinePrompt(run, task) {
  if (!run.baseline) return "";
  const recipe = run.baseline.recipes[task.document];
  return (
    "\nAvailable local PDF utility (same in every arm). Choose Read or local extraction as appropriate. " +
    "Bash permits these exact forms; no pipes or redirects.\n" +
    "Whole document: " +
    recipe.whole +
    "\n" +
    "One physical page: " +
    recipe.page +
    "\n" +
    "Replace each {page} with the same integer from 1 through " +
    recipe.pages +
    ".\n"
  );
}

export function validateRun(manifestPath, approvedHash) {
  const path = realpathSync(manifestPath),
    bytes = readFileSync(path),
    manifest = JSON.parse(bytes);
  if (!validate(manifest))
    throw new Error("Experiment manifest does not match the closed schema.");
  const hash = digest(bytes);
  if (approvedHash !== undefined && approvedHash !== hash)
    throw new Error("Manifest approval hash does not match.");
  const root = realpathSync(manifest.evidence_root);
  if (
    !isAbsolute(manifest.evidence_root) ||
    root !== manifest.evidence_root ||
    !path.startsWith(root + sep)
  )
    throw new Error("Invalid evidence root or manifest path.");
  for (let parent = root; ; parent = dirname(parent)) {
    if (existsSync(join(parent, ".git")))
      throw new Error(
        "Experiment evidence must remain outside a Git repository.",
      );
    if (dirname(parent) === parent) break;
  }
  const primary = manifest.study_kind === "primary";
  if (
    manifest.task_ids.length !== (primary ? 12 : 4) ||
    manifest.repetitions !== (primary ? 3 : 1) ||
    manifest.max_trials !== (primary ? 108 : 12) ||
    (!primary && manifest.max_estimated_usd_total > 20) ||
    manifest.model_id.includes("latest")
  )
    throw new Error("Experiment design or model is not pinned.");
  const paths = {};
  for (const [name, hashName] of [
    ["dataset_manifest", "dataset_sha256"],
    ["prompt_file", "prompt_sha256"],
    ["skill_file", "skill_sha256"],
    ["environment_file", "environment_sha256"],
  ])
    paths[name] = checkedFile(root, manifest[name], manifest[hashName]);
  paths.runtime = contained(root, manifest.runtime_dir);
  paths.plugin = contained(root, manifest.plugin_dir);
  if (fileHash(join(paths.runtime, "release.json")) !== manifest.runtime_sha256)
    throw new Error("Runtime metadata hash mismatch.");
  const release = JSON.parse(readFileSync(join(paths.runtime, "release.json")));
  if (release.core_commit !== manifest.core_commit)
    throw new Error("Runtime core revision mismatch.");
  runtimeInventory(paths.runtime, release);
  if (
    !isAbsolute(manifest.client_path) ||
    fileHash(manifest.client_path) !== manifest.client_sha256
  )
    throw new Error("Client executable hash mismatch.");
  const dataset = JSON.parse(readFileSync(paths.dataset_manifest));
  if (
    !Array.isArray(dataset.tasks) ||
    !dataset.files ||
    manifest.task_ids.some(
      (id) => dataset.tasks.filter((task) => task.id === id).length !== 1,
    )
  )
    throw new Error("Dataset tasks do not match the experiment.");
  for (const [name, hash] of Object.entries(dataset.files))
    checkedFile(root, name, hash);
  for (const task of dataset.tasks) {
    if (
      !dataset.files[task.document] ||
      !dataset.files[task.extraction] ||
      typeof task.question !== "string" ||
      !["agreement", "manual", "report"].includes(task.category)
    )
      throw new Error("Dataset task has unfrozen inputs.");
  }
  const environment = JSON.parse(readFileSync(paths.environment_file));
  for (const [name, hash] of Object.entries(environment.plugin_files ?? {}))
    checkedFile(root, name, hash);
  if (
    environment.package_lock_sha256 &&
    environment.package_lock_sha256 !==
      fileHash(join(HERE, "../package-lock.json"))
  )
    throw new Error("Measurement dependency lock hash mismatch.");
  if (environment.plugin_files) {
    const actual = [];
    function walkPlugin(directory) {
      for (const name of readdirSync(directory)) {
        const candidate = join(directory, name);
        if (candidate === paths.runtime) continue;
        const stat = lstatSync(candidate);
        if (stat.isDirectory() && !stat.isSymbolicLink()) walkPlugin(candidate);
        else actual.push(relative(root, candidate));
      }
    }
    walkPlugin(paths.plugin);
    if (
      JSON.stringify(actual.sort()) !==
      JSON.stringify(Object.keys(environment.plugin_files).sort())
    )
      throw new Error("Frozen plugin inventory changed.");
  }
  const sourceHash = digest(
    Buffer.concat(
      ["run.mjs", "accounting.mjs", "report.mjs"].map((name) =>
        readFileSync(join(HERE, name)),
      ),
    ),
  );
  if (
    environment.measurement_source_sha256 &&
    environment.measurement_source_sha256 !== sourceHash
  )
    throw new Error("Measurement source hash mismatch.");
  if (dataset.ground_truth_sha256)
    checkedFile(root, "ground-truth.json", dataset.ground_truth_sha256);
  return {
    manifest,
    manifestPath: path,
    manifestHash: hash,
    root,
    paths,
    dataset,
    baseline: baselineInventory(environment, manifest, dataset),
    liveApproved: approvedHash === hash,
  };
}

export function plannedTrials(run) {
  let seed = run.manifest.order_seed >>> 0;
  const random = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 2 ** 32;
  };
  const trials = [];
  for (const task_id of run.manifest.task_ids)
    for (
      let repetition = 0;
      repetition < run.manifest.repetitions;
      repetition++
    ) {
      const arms = ["A", "B", "C"];
      for (let i = arms.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1));
        [arms[i], arms[j]] = [arms[j], arms[i]];
      }
      for (const arm of arms) trials.push({ task_id, repetition, arm });
    }
  return trials;
}

function permission(run, workspace, decisions) {
  const readable = [
    workspace,
    ...Object.keys(run.dataset.files)
      .filter((name) => /\.pdf$/.test(name))
      .map((name) => join(run.root, name)),
  ];
  const decide = (name, input) => {
    if (
      name.startsWith("mcp__openreading") ||
      name.startsWith("mcp__plugin_openreading-local-proof_openreading__")
    )
      return { behavior: "allow", updatedInput: input };
    if (
      name === "Bash" &&
      run.manifest.allowed_bash_commands.includes(input.command)
    )
      return { behavior: "allow", updatedInput: input };
    if (["Read", "Glob", "Grep"].includes(name)) {
      let candidate;
      try {
        candidate = realpathSync(
          resolve(workspace, (name === "Read" ? input.file_path : input.path) ?? "."),
        );
      } catch {
        return {
          behavior: "deny",
          message: "The requested evidence path is unavailable.",
        };
      }
      // Grep's pattern is content, while its glob and Glob's pattern select filenames.
      // Restrict filename expansion syntax so braces or escapes cannot hide traversal.
      const pattern =
        name === "Glob"
          ? input.pattern
          : name === "Grep"
            ? input.glob
            : undefined;
      const boundedPattern =
        pattern === undefined ||
        (typeof pattern === "string" &&
          !isAbsolute(pattern) &&
          !pattern.startsWith("~") &&
          !pattern.split("/").includes("..") &&
          ![...pattern].some((character) => "\\{}()[]!".includes(character)));
      if (
        boundedPattern &&
        readable.some(
          (path) =>
            candidate === path ||
            (path === workspace && candidate.startsWith(path + sep)),
        )
      )
        return { behavior: "allow", updatedInput: input };
    }
    return {
      behavior: "deny",
      message:
        "This experiment grants only its frozen document inputs and approved local commands.",
    };
  };
  return async (name, input) => {
    const result = decide(name, input);
    if (result.behavior === "deny")
      decisions[name] = (decisions[name] ?? 0) + 1;
    return result;
  };
}

export async function runTrial(
  run,
  task,
  { query, remainingBudget = run.manifest.max_estimated_usd_per_trial } = {},
) {
  if (!run.liveApproved)
    throw new Error("Model execution requires an approved manifest hash.");
  run = validateRun(run.manifestPath, run.manifestHash);
  if (!query && !run.baseline)
    throw new Error(
      "Prepare a verified local PDF baseline before live execution.",
    );
  const datasetTask = run.dataset.tasks.find(
    (item) => item.id === task.task_id,
  );
  if (run.baseline && datasetTask) {
    const text = execFileSync(
      run.baseline.executable,
      ["-f", "1", "-l", "1", join(run.root, datasetTask.document), "-"],
      { encoding: "utf8", timeout: 5000, maxBuffer: 2 * 1024 * 1024 },
    );
    if (!text.trim())
      throw new Error(
        "Baseline utility produced no text; no model call was started.",
      );
  }
  if (!query) {
    if (!process.env.ANTHROPIC_API_KEY)
      throw new Error("Live experiments require an explicit API account key.");
    const environment = JSON.parse(readFileSync(run.paths.environment_file));
    if (
      !environment.measurement_source_sha256 ||
      !environment.plugin_files ||
      !environment.package_lock_sha256
    )
      throw new Error(
        "The measurement source must be frozen before live execution.",
      );
    if (
      environment.account_key_sha256 !== digest(process.env.ANTHROPIC_API_KEY)
    )
      throw new Error("Approved account key fingerprint does not match.");
    const version = execFileSync(run.manifest.client_path, ["--version"], {
      encoding: "utf8",
    }).trim();
    if (!version.startsWith(run.manifest.client_version))
      throw new Error("Installed client version differs from the manifest.");
    ({ query } = await import("@anthropic-ai/claude-agent-sdk"));
  }
  if (
    !datasetTask ||
    !plannedTrials(run).some(
      (item) =>
        item.task_id === task.task_id &&
        item.arm === task.arm &&
        item.repetition === task.repetition,
    )
  )
    throw new Error("Unplanned trial.");
  const id = `${task.task_id}-${task.repetition}-${task.arm}`;
  const trialRoot = join(run.root, "runs", run.manifest.experiment_id, id);
  mkdirSync(trialRoot, { recursive: true, mode: 0o700 });
  const eventsPath = join(trialRoot, "events.jsonl");
  closeSync(openSync(eventsPath, "wx", 0o600));
  const events = [],
    controller = new AbortController();
  const started = Date.now();
  let state = "completed",
    rawBytes = 0;
  const timeout = setTimeout(
    () => controller.abort(),
    run.manifest.timeout_seconds_per_trial * 1000,
  );
  let prompt =
    readFileSync(run.paths.prompt_file, "utf8") +
    "\nQuestion: " +
    datasetTask.question +
    "\n";
  if (task.arm === "B")
    prompt +=
      "Complete local extraction with physical page markers:\n" +
      readFileSync(join(run.root, datasetTask.extraction), "utf8");
  else
    prompt +=
      "Document: " +
      (task.arm === "C"
        ? datasetTask.document.split("/").at(-1)
        : join(run.root, datasetTask.document));
  prompt += baselinePrompt(run, datasetTask);
  const decisions = {};
  const options = {
    model: run.manifest.model_id,
    pathToClaudeCodeExecutable: run.manifest.client_path,
    cwd: trialRoot,
    settingSources: [],
    tools: ["Read", "Glob", "Grep", "Bash"],
    permissionMode: "default",
    canUseTool: permission(run, trialRoot, decisions),
    maxTurns: run.manifest.max_turns_per_trial,
    maxBudgetUsd: Math.min(
      remainingBudget,
      run.manifest.max_estimated_usd_per_trial,
    ),
    abortController: controller,
    persistSession: false,
    env: {
      PATH: process.env.PATH,
      HOME: trialRoot,
      TMPDIR: trialRoot,
      ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
      CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
    },
    ...(task.arm === "C"
      ? {
          plugins: [{ type: "local", path: run.paths.plugin }],
          settings: {
            pluginConfigs: {
              "openreading-local-proof": {
                options: {
                  input_root: dirname(join(run.root, datasetTask.document)),
                },
              },
            },
          },
        }
      : {}),
  };
  try {
    for await (const event of query({ prompt, options })) {
      const line = JSON.stringify(event) + "\n";
      rawBytes += Buffer.byteLength(line);
      if (rawBytes > 50 * 1024 * 1024) {
        controller.abort();
        throw new Error("Evidence limit");
      }
      appendFileSync(eventsPath, line);
      events.push(event);
    }
    if (
      controller.signal.aborted ||
      events.filter((e) => e.type === "result").at(-1)?.subtype !== "success"
    )
      state = "failed";
  } catch {
    state = controller.signal.aborted ? "timeout" : "failed";
  } finally {
    clearTimeout(timeout);
    controller.abort();
  }
  const trial = {
    schema_version: "1",
    ...task,
    category: datasetTask.category,
    manifest_sha256: run.manifestHash,
    state,
    usage: normalizeQuery(events),
    baseline: {
      utility_verified: run.baseline !== null,
      bash_denials: decisions.Bash ?? 0,
    },
    permission_denials: decisions,
    quality: { passed: null, citation_valid: null },
    wall_ms: Date.now() - started,
    evidence: { events: relative(run.root, eventsPath) },
  };
  writeFileSync(
    join(trialRoot, "trial.json"),
    JSON.stringify(trial, null, 2) + "\n",
    { flag: "wx", mode: 0o600 },
  );
  return trial;
}

export async function main(argv = process.argv.slice(2), { query } = {}) {
  const path = argv[0];
  if (!path || argv.includes("--help")) {
    console.log(
      "node measurement/run.mjs MANIFEST [--report | --live --approved-manifest-sha256 HASH]",
    );
    return 0;
  }
  const reportOnly = argv.includes("--report");
  if (reportOnly && argv.includes("--live"))
    throw new Error("Choose report or live execution.");
  const live = argv.includes("--live"),
    approval = argv.indexOf("--approved-manifest-sha256");
  if (live && approval < 0)
    throw new Error("Live mode requires an approved manifest hash.");
  const run = validateRun(path, approval >= 0 ? argv[approval + 1] : undefined),
    schedule = plannedTrials(run);
  if (!live && !reportOnly) {
    console.log(
      JSON.stringify(
        {
          mode: "dry-run",
          manifest_sha256: run.manifestHash,
          planned_trials: schedule.length,
          estimated_usd_ceiling: run.manifest.max_estimated_usd_total,
          account_label: run.manifest.account_label,
        },
        null,
        2,
      ),
    );
    return 0;
  }
  const output = join(run.root, "runs", run.manifest.experiment_id);
  mkdirSync(output, { recursive: true, mode: 0o700 });
  const lock = join(output, ".lock"),
    fd = openSync(lock, "wx", 0o600),
    trials = [];
  try {
    let spent = 0,
      incomplete = false;
    const completed = new Set();
    // Account for all existing trials before scheduling anything after a restart.
    for (const task of schedule) {
      const id = `${task.task_id}-${task.repetition}-${task.arm}`;
      const record = join(output, id, "trial.json");
      if (!existsSync(record)) {
        if (existsSync(join(output, id, "events.jsonl"))) incomplete = true;
        continue;
      }
      const trial = JSON.parse(readFileSync(record));
      if (trial.manifest_sha256 !== run.manifestHash)
        throw new Error("Stored trial belongs to another manifest.");
      trials.push(trial);
      completed.add(id);
      if (
        !trial.usage.complete ||
        !Number.isFinite(trial.usage.estimated_usd) ||
        trial.usage.estimated_usd < 0
      )
        incomplete = true;
      else spent += trial.usage.estimated_usd;
    }
    if (!incomplete && !reportOnly)
      for (const task of schedule) {
        if (completed.has(`${task.task_id}-${task.repetition}-${task.arm}`))
          continue;
        if (spent >= run.manifest.max_estimated_usd_total) break;
        const trial = await runTrial(run, task, {
          query,
          remainingBudget: run.manifest.max_estimated_usd_total - spent,
        });
        trials.push(trial);
        if (!trial.usage.complete || trial.usage.estimated_usd === null) break;
        spent += trial.usage.estimated_usd;
      }
    writeFileSync(
      join(output, "report.json"),
      JSON.stringify(buildReport(run.manifest, trials, run.dataset), null, 2) +
        "\n",
      { mode: 0o600 },
    );
  } finally {
    closeSync(fd);
    unlinkSync(lock);
  }
  return 0;
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href
)
  main().catch(() => {
    console.error(
      "Experiment stopped. Check the manifest, approval, and private trial records.",
    );
    process.exitCode = 1;
  });
