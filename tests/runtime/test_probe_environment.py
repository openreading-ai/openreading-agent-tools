"""The source probe fingerprint reacts to installed code and ignores only bytecode."""

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
    def test_installed_file_mutation_changes_snapshot_but_bytecode_does_not(self):
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
                self.assertEqual(first, module.snapshot(profile, root / "lock"))
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
