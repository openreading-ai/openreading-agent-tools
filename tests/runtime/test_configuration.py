"""Coding-client setup requires an explicit grant and keeps it outside plugin caches."""

import json
import tempfile
import unittest
from pathlib import Path

from runtime.configuration import configure, read_grant


class ConfigurationTests(unittest.TestCase):
    def test_explicit_grant_persists_and_is_client_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            grant = home / "Documents ü with spaces"
            grant.mkdir()
            configure("codex", grant, home=home)
            self.assertEqual(read_grant("codex", home=home), grant)
            with self.assertRaises(ValueError):
                read_grant("claude-code", home=home)
            configuration = (
                home / "Library/Application Support/OpenReading/agent-tools/codex/config.json"
            )
            self.assertEqual(configuration.stat().st_mode & 0o777, 0o600)
            self.assertEqual(set(json.loads(configuration.read_text())), {"input_root"})

    def test_missing_relative_or_symlink_grants_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            grant = home / "Documents"
            grant.mkdir()
            link = home / "link"
            link.symlink_to(grant)
            for value in [Path("relative"), home / "missing", link]:
                with self.assertRaises(ValueError):
                    configure("codex", value, home=home)
            with self.assertRaises(ValueError):
                configure("unknown-client", grant, home=home)
