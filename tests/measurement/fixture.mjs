/** Shared synthetic evidence setup; importing it never registers tests. */
import {
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  rmSync,
  chmodSync,
  realpathSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createHash } from "node:crypto";
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
