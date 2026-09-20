"""The source probe fingerprint reacts to installed code including bytecode and startup hooks."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as Box
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location(
    "probe_environment", Path(__file__).resolve().parents[2] / "scripts/probe_environment.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class EnvironmentTests(unittest.TestCase):
    def test_trial_artifacts_are_verified_before_their_identity_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profile.json"
            profile.write_text('{"docling":{},"pages":100}')
            folder = root / "documents" / "artifact"
            folder.mkdir(parents=True)
            response = b'{"document":{"pages":[{"page_number":1,"text":"60 days"}]}}'
            fake_service = Mock()
            service = fake_service.ArtifactService.return_value
            service.store.documents = folder.parent
            manifest = Box(
                source_relative_path="agreement.pdf",
                document_sha256="hash",
                engine=Box(wire=lambda: {"engine": "fixed"}),
                files={"response.json": Box(length=len(response))},
            )
            service.store.load.return_value = (manifest, [])
            with (
                patch.dict(
                    "sys.modules",
                    {
                        "openreading.adapters.docling_local.config": Mock(),
                        "openreading.artifacts.limits": Mock(),
                        "openreading.artifacts.service": fake_service,
                    },
                ),
                patch("openreading.artifacts.store.safe_read", return_value=response),
            ):
                records = module.verify_artifacts(profile, root / "lock", root / "input", root)
                self.assertEqual(records[0]["document_sha256"], "hash")
                self.assertEqual(records[0]["source_relative_path"], "agreement.pdf")
                service.store.load.assert_called_once_with("artifact")
                service.close.assert_called_once()
                service.store.load.side_effect = ValueError("corrupt")
                with self.assertRaises(ValueError):
                    module.verify_artifacts(profile, root / "lock", root / "input", root)
                self.assertEqual(service.close.call_count, 2)

    def test_installed_files_bytecode_and_startup_hooks_change_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "engine.py").write_text("code")
            (root / "engine.pyc").write_text("cache")
            profile = root / "profile.json"
            profile.write_text('{"docling":{},"pages":100}')
            dist = Box(
                files=[Path("engine.py"), Path("engine.pyc"), Path("missing")],
                locate_file=lambda entry: root / entry,
            )
            fake_config = Mock()
            fake_limits = Mock()
            fake_service = Mock()
            fake_service.engine_identity.return_value.wire.return_value = {
                "backend_id": "docling_local"
            }
            with (
                patch.dict(
                    "sys.modules",
                    {
                        "openreading.adapters.docling_local.config": fake_config,
                        "openreading.artifacts.limits": fake_limits,
                        "openreading.artifacts.service": fake_service,
                    },
                ),
                patch.object(
                    module, "selected_environment", return_value={"packages": {"core": "1"}}
                ),
                patch.object(module.metadata, "distribution", return_value=dist),
            ):
                first = module.snapshot(profile, root / "lock")
                (root / "engine.pyc").write_text("new cache")
                self.assertNotEqual(first, module.snapshot(profile, root / "lock"))
                (root / "injected.pth").write_text("import altered_startup")
                hooked = module.snapshot(profile, root / "lock")
                (root / "injected.pth").write_text("import different_startup")
                self.assertNotEqual(hooked, module.snapshot(profile, root / "lock"))
                (root / "engine.py").write_text("changed source")
                self.assertNotEqual(
                    first["installed_files_sha256"],
                    module.snapshot(profile, root / "lock")["installed_files_sha256"],
                )
                with (
                    patch.object(module, "snapshot", return_value=first),
                    patch("builtins.print") as printed,
                ):
                    module.main(["--profile", str(profile), "--lock", str(root / "lock")])
                    self.assertEqual(json.loads(printed.call_args.args[0]), first)

    def test_artifact_command_requires_both_roots_and_dispatches_verification(self):
        args = ["--profile", "profile", "--lock", "lock", "--input-root", "input"]
        with patch("sys.stderr"), self.assertRaises(SystemExit):
            module.main(args)
        with (
            patch.object(module, "verify_artifacts", return_value=[]) as verify,
            patch("builtins.print") as printed,
        ):
            module.main([*args, "--artifact-root", "artifacts"])
            verify.assert_called_once_with(
                Path("profile"), Path("lock"), Path("input"), Path("artifacts")
            )
            self.assertEqual(json.loads(printed.call_args.args[0]), [])
