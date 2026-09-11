"""Probe preparation is offline and cannot turn an unresolved account into approval."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from measurement.corpus import generate, recipe
from measurement.probe import finalize, main, prepare, schedule
from runtime.verify import sha256

REAL_RUN = subprocess.run


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.evidence = self.root / "evidence"
        generation = generate(self.evidence)
        self.environment = {"core_commit": "a" * 40, "packages": {"openreading": "0.3.0"}}
        self.report = {
            "passed": True,
            "generation": generation,
            "environment": self.environment,
            "tasks": [
                {"task_id": t["id"], "passed": bool(t["support"])} for t in recipe()["tasks"]
            ],
            "documents": {},
        }
        for name in ("agreement", "manual", "report"):
            text = self.evidence / f"{name}-ocr-False.txt"
            text.write_text(f"[Physical page 1]\n{name} extracted text")
            self.report["documents"][name] = {
                "full_text_sha256": sha256(text),
                "engine": {"extraction_settings": {"retriever": "lexical-v2-dehyphenated"}},
            }
        self.save_report()
        (self.evidence / "restart-report.json").write_text('{"passed":true}')
        self.utility = self.root / "utility"
        self.utility.write_text("fake local executable")
        self.identity = {
            "environment": self.environment,
            "engine": {"extraction_settings": {"retriever": "lexical-v2-dehyphenated"}},
        }
        self.args = dict(
            output=self.root / "probe",
            evidence=self.evidence,
            python=self.utility,
            client=self.utility,
            assets=self.root / "assets",
            lock=self.utility,
        )
        self.which = patch("measurement.probe.shutil.which", return_value=str(self.utility)).start()
        self.calls = patch(
            "measurement.probe.subprocess.check_output", side_effect=self.command
        ).start()
        patch("measurement.probe.platform.platform", return_value="test-os").start()
        patch("measurement.probe.platform.machine", return_value="arm64").start()
        self.validation = patch("measurement.probe.subprocess.run").start()
        self.addCleanup(patch.stopall)

    def save_report(self):
        (self.evidence / "retrieval-report.json").write_text(json.dumps(self.report))

    def command(self, args, **kwargs):
        if "--profile" in args:
            return (json.dumps(self.identity) + "\n").encode()
        if "--version" in args:
            return "2.1.267 (Claude Code)"
        return b"usable baseline text"

    def test_probe_preparation_is_separate_and_unapproved(self):
        self.assertEqual(len(schedule()), 9)
        path = prepare(**self.args)
        manifest = json.loads(path.read_text())
        self.assertIsNone(manifest["model_id"])
        self.assertIsNone(manifest["account_label"])
        self.assertEqual(manifest["max_trials"], 9)
        self.assertEqual(len(manifest["allowed_bash_commands"]), 155)
        self.assertEqual(manifest["max_estimated_usd_per_trial"], 0.5)
        self.assertFalse((path.parent / "manifest.json").exists())
        dataset = json.loads((path.parent / "dataset.json").read_text())
        self.assertEqual(len(dataset["tasks"]), 12)
        self.assertNotIn("support", dataset["tasks"][0])
        self.assertNotIn("ground-truth.json", dataset["files"])
        self.assertTrue((path.parent / "approval-needed.json").exists())
        with self.assertRaises(ValueError):
            prepare(**self.args)

    def test_rejects_unverified_corpus_engine_extraction_and_baseline(self):
        for condition in (
            "report",
            "generation",
            "engine",
            "identity",
            "extraction",
            "utility",
            "empty",
        ):
            with self.subTest(condition=condition):
                self.args["output"] = self.root / condition
                with patch("measurement.probe.recipe", wraps=recipe) as get_recipe:
                    self.report["passed"] = condition != "report"
                    self.save_report()
                    if condition == "generation":
                        altered = recipe()
                        altered["expected_hashes"] = {}
                        get_recipe.return_value = altered
                    self.identity["environment"] = {} if condition == "engine" else self.environment
                    self.identity["engine"]["extraction_settings"]["retriever"] = (
                        "changed" if condition == "identity" else "lexical-v2-dehyphenated"
                    )
                    if condition == "extraction":
                        (self.evidence / "agreement-ocr-False.txt").write_text("changed")
                    self.which.return_value = None if condition == "utility" else str(self.utility)
                    self.calls.side_effect = (
                        (lambda *a, **kw: b"") if condition == "empty" else self.command
                    )
                    if condition == "empty":
                        self.calls.side_effect = lambda args, **kw: (
                            self.command(args, **kw)
                            if "--profile" in args or "--version" in args
                            else b" "
                        )
                    with self.assertRaises(ValueError):
                        prepare(**self.args)
                    (self.evidence / "agreement-ocr-False.txt").write_text(
                        "[Physical page 1]\nagreement extracted text"
                    )

    def test_rejects_git_output_and_generation_drift(self):
        (self.root / ".git").mkdir()
        with self.assertRaises(ValueError):
            prepare(**self.args)
        (self.root / ".git").rmdir()
        with patch("measurement.probe.generate", return_value={}):
            with self.assertRaisesRegex(ValueError, "Generation"):
                prepare(**self.args)

    def test_finalization_requires_account_and_never_runs_a_model(self):
        root = prepare(**self.args).parent
        prices = self.root / "prices.json"
        prices.write_text('{"model_id":"claude-sonnet-4-6"}')
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                finalize(root, "claude-sonnet-4-6", "account", prices)
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "synthetic-test-key"}):
            for model, account in [
                ("latest", "account"),
                ("claude-latest", "account"),
                ("claude-sonnet-4-6", " "),
            ]:
                with self.assertRaises(ValueError):
                    finalize(root, model, account, prices)
            with self.assertRaises(ValueError):
                finalize(root, "claude-opus-4-6", "account", prices)
            self.validation.side_effect = ValueError("invalid frozen input")
            with self.assertRaises(ValueError):
                finalize(root, "claude-sonnet-4-6", "account", prices)
            self.assertFalse((root / "manifest.json").exists())
            self.assertFalse((root / "manifest-pending.json").exists())
            self.validation.side_effect = None
            path = finalize(root, "claude-sonnet-4-6", "account", prices)
            manifest = json.loads(path.read_text())
            self.assertEqual(manifest["model_id"], "claude-sonnet-4-6")
            self.assertNotIn("synthetic-test-key", path.read_text())
            with self.assertRaises(FileExistsError):
                finalize(root, "claude-sonnet-4-6", "account", prices)

    def test_cli_routes_only_local_preparation_or_finalization(self):
        with (
            patch("measurement.probe.prepare", return_value="draft") as prep,
            patch("builtins.print"),
        ):
            main(
                [
                    "prepare",
                    *[
                        part
                        for key, value in self.args.items()
                        for part in (f"--{key}", str(value))
                    ],
                ]
            )
            self.assertEqual(prep.call_args.kwargs["python"], self.utility)
        with (
            patch("measurement.probe.finalize", return_value="manifest") as final,
            patch("builtins.print"),
        ):
            main(
                [
                    "finalize",
                    str(self.root),
                    "--model",
                    "model",
                    "--account",
                    "label",
                    "--pricing",
                    str(self.utility),
                ]
            )
            final.assert_called_once()

    def test_python_preparation_round_trips_through_the_real_node_validator(self):
        source = self.root / "source-python"
        encoded = json.dumps(self.identity) + "\n"
        source.write_text("#!/bin/sh\nprintf '%s' '" + encoded + "'\n")
        source.chmod(0o755)
        self.args["python"] = source
        root = prepare(**self.args).parent
        prices = root / "test-pricing.json"
        prices.write_text(
            json.dumps(
                {
                    "model_id": "claude-sonnet-4-6",
                    "source": "https://platform.claude.com/docs/en/about-claude/pricing",
                    "checked_on": "2026-09-11",
                    "usd_per_million": dict.fromkeys(
                        ["input", "cache_write", "cache_read", "output"], 0
                    ),
                }
            )
        )
        self.validation.side_effect = REAL_RUN
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "synthetic-offline-test"}):
            manifest = finalize(root, "claude-sonnet-4-6", "synthetic-offline-test", prices)
        self.assertTrue(manifest.exists())
        self.assertFalse((root / "runs").exists())
        self.assertNotIn("--live", self.validation.call_args.args[0])
