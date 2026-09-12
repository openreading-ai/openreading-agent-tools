/** Exercise policy boundaries so a green gate means more than readable Markdown. */
import assert from "node:assert/strict";
import {
  readFileSync,
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  rmSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { checkRepository } from "../scripts/check-repository.mjs";

function check(files) {
  const root = mkdtempSync(join(tmpdir(), "openreading-repo-check-"));
  try {
    for (const [path, content] of Object.entries(files)) {
      mkdirSync(join(root, path, ".."), { recursive: true });
      writeFileSync(join(root, path), content);
    }
    return checkRepository(root);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

test("proposals and directory guides are allowed", () => {
  assert.deepEqual(
    check({
      "README.md": "# Home\n\n[Design](design/proof.md)\n",
      "design/proof.md": "# Proposal\n",
      "product/specs/proof.product-spec.md": "# Intent\n",
      "scripts/README.md": "# Checks\n",
      "skills/read-document/SKILL.md": "# Document workflow\n",
    }),
    [],
  );
});

test("standalone code descriptions are refused", () => {
  assert.match(
    check({ "scripts/how-it-works.md": "# Guide\n" }).join("\n"),
    /not allowed/,
  );
});

test("missing relative links and local path escapes are refused", () => {
  const errors = check({
    "README.md": "# Home\n\n[Missing](absent.md) [Escape](../private.md)\n",
  });
  assert.equal(errors.length, 2);
  assert.match(errors.join("\n"), /missing|escapes/);
});

test("reference links are checked while sample code is ignored", () => {
  const errors = check({
    "README.md":
      "# Home\n\n[Missing][ref]\n\n[ref]: missing.md\n\n~~~text\n[Example](imaginary.md)\n~~~\n",
  });
  assert.equal(errors.length, 1);
});

test("malformed YAML and JSON fail", () => {
  const errors = check({
    "bad.json": "{",
    ".github/bad.yml": "key: 1\nkey: 2\n",
  });
  assert.equal(errors.length, 2);
});

test("HTTP links stay offline and Claude imports stay canonical", () => {
  assert.deepEqual(
    check({
      "README.md": "# Home\n\n[Remote](https://example.invalid/page)\n",
      "CLAUDE.md": "@AGENTS.md\n",
      "AGENTS.md": "# Instructions\n",
    }),
    [],
  );
  assert.match(
    check({ "CLAUDE.md": "Different instructions\n" }).join("\n"),
    /AGENTS/,
  );
});

test("MCPB resolves the binary command and preserves a configured directory argument", async () => {
  const { getMcpConfigForManifest } = await import("@anthropic-ai/mcpb");
  const manifest = JSON.parse(
    readFileSync(
      new URL("../clients/claude-desktop/manifest.json", import.meta.url),
    ),
  );
  const config = await getMcpConfigForManifest({
    manifest,
    extensionPath: "/installed/review bundle",
    systemDirs: {},
    userConfig: { input_root: "/documents/Unicode 界" },
    pathSeparator: "/",
  });
  assert.equal(
    config.command,
    "/installed/review bundle/server/openreading-worker",
  );
  assert.deepEqual(config.args.slice(-2), [
    "--input-root",
    "/documents/Unicode 界",
  ]);
});

test("coverage thresholds cannot fall below 95 percent", () => {
  const config = JSON.parse(
    readFileSync(new URL("../package.json", import.meta.url)),
  );
  for (const metric of ["lines", "branches", "functions"]) {
    const match = config.scripts.test.match(
      new RegExp(`--test-coverage-${metric}=(\\d+)`),
    );
    assert.ok(match && Number(match[1]) >= 95, metric);
  }
  const python = readFileSync(
    new URL("../runtime/pyproject.toml", import.meta.url),
    "utf8",
  );
  assert.ok(Number(python.match(/fail_under\s*=\s*(\d+)/)[1]) >= 95);
  const make = readFileSync(new URL("../Makefile", import.meta.url), "utf8");
  assert.ok(
    make.includes("python -m runtime.coverage_gate coverage-report.json"),
  );
  assert.match(
    readFileSync("runtime/pyproject.toml", "utf8"),
    /source = \["runtime", "measurement", "scripts"\]/,
  );
});

test("Docling Desktop setup resolves both OCR states and preserves hostile-looking paths", async () => {
  const { getMcpConfigForManifest, v0_4 } = await import("@anthropic-ai/mcpb");
  const manifest = JSON.parse(
    readFileSync(
      new URL(
        "../clients/claude-desktop/docling/manifest.json",
        import.meta.url,
      ),
    ),
  );
  assert.equal(v0_4.McpbManifestSchema.safeParse(manifest).success, true);
  for (const ocr of [false, true]) {
    const grant = "/documents/界 space ' $(echo forbidden) ; *";
    const config = await getMcpConfigForManifest({
      manifest,
      extensionPath: "/installed/界 bundle",
      systemDirs: {},
      userConfig: { input_root: grant, ocr },
      pathSeparator: "/",
    });
    assert.equal(
      config.command,
      "/installed/界 bundle/server/openreading-worker",
    );
    assert.deepEqual(config.args, [
      "--client",
      "claude-desktop",
      "--input-root",
      grant,
      "--ocr",
      String(ocr),
    ]);
    assert.ok(!config.env || Object.keys(config.env).length === 0);
  }
});
