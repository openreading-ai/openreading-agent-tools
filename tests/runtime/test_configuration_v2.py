"""Versioned setup preserves old clients and refuses ambiguous document grants."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime import configuration


class VersionTwoConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.grant = self.home / "Documents ü spaces"
        self.grant.mkdir()

    def require_api(self):
        self.assertTrue(hasattr(configuration, "configure_v2"), "Version 2 setup is absent")

    def test_new_setup_coexists_with_legacy_and_keeps_ocr_boolean(self):
        self.require_api()
        configuration.configure("codex", self.grant, home=self.home)
        root = configuration.client_root("codex", home=self.home)
        legacy = (root / "config.json").read_bytes()
        configuration.configure_v2("codex", self.grant, True, home=self.home)
        self.assertEqual((root / "config.json").read_bytes(), legacy)
        self.assertEqual(configuration.read_grant("codex", home=self.home), self.grant)
        stored = root / "v2/config.json"
        self.assertEqual(
            json.loads(stored.read_text()),
            {
                "schema_version": 2,
                "input_root": str(self.grant),
                "ocr": True,
            },
        )
        self.assertEqual(stored.stat().st_mode & 0o777, 0o600)
        value = configuration.read_settings("codex", home=self.home)
        self.assertEqual((value.input_root, value.ocr), (self.grant, True))
        self.assertTrue((root / "v2/artifacts").is_dir())
        with self.assertRaises(ValueError):
            configuration.read_settings("chatgpt", home=self.home)

    def test_missing_or_invalid_replacement_never_reuses_legacy_settings(self):
        self.require_api()
        configuration.configure("codex", self.grant, home=self.home)
        with self.assertRaises(ValueError):
            configuration.read_settings("codex", home=self.home)
        configuration.configure_v2("codex", self.grant, home=self.home)
        root = configuration.client_root("codex", home=self.home) / "v2"
        before = (root / "config.json").read_bytes()
        for grant, ocr in [
            (Path("relative"), False),
            (self.home / "missing", False),
            (self.grant, "false"),
        ]:
            with self.subTest(grant=grant, ocr=ocr), self.assertRaises(ValueError):
                configuration.configure_v2("codex", grant, ocr, home=self.home)
            self.assertEqual((root / "config.json").read_bytes(), before)
        with patch("runtime.configuration.os.replace", side_effect=OSError("private path")):
            with self.assertRaisesRegex(ValueError, "configuration_required"):
                configuration.configure_v2("codex", self.grant, True, home=self.home)
        self.assertEqual((root / "config.json").read_bytes(), before)
        self.assertEqual(sorted(p.name for p in root.iterdir()), ["artifacts", "config.json"])

    def test_closed_saved_settings_reject_wrong_types_and_extra_fields(self):
        self.require_api()
        configuration.configure_v2("chatgpt", self.grant, home=self.home)
        path = configuration.client_root("chatgpt", home=self.home) / "v2/config.json"
        base = {"schema_version": 2, "input_root": str(self.grant), "ocr": False}
        for data in [
            [],
            {},
            {**base, "schema_version": True},
            {**base, "schema_version": 1},
            {**base, "ocr": 0},
            {**base, "ocr": "false"},
            {**base, "input_root": 4},
            {**base, "input_root": "relative"},
            {**base, "backend": "hosted"},
        ]:
            path.write_text(json.dumps(data))
            with (
                self.subTest(data=data),
                self.assertRaisesRegex(ValueError, "configuration_required"),
            ):
                configuration.read_settings("chatgpt", home=self.home)
        path.write_text('{"password":')
        with self.assertRaises(ValueError):
            configuration.read_settings("chatgpt", home=self.home)

    def test_settings_symlink_cannot_redirect_writes_or_reads(self):
        self.require_api()
        root = configuration.client_root("chatgpt", home=self.home)
        root.mkdir(parents=True)
        outside = self.home / "outside"
        outside.mkdir()
        (root / "v2").symlink_to(outside)
        with self.assertRaises(ValueError):
            configuration.configure_v2("chatgpt", self.grant, home=self.home)
        self.assertEqual(list(outside.iterdir()), [])
        with self.assertRaises(ValueError):
            configuration.read_settings("chatgpt", home=self.home)

    def test_ocr_tokens_are_closed_and_direct_setup_is_not_merged(self):
        self.require_api()
        for token, expected in [
            (None, False),
            ("", False),
            ("off", False),
            ("false", False),
            ("on", True),
            ("true", True),
        ]:
            self.assertIs(configuration.ocr_value(token), expected)
        for token in ["False", "0", "1", " ", "yes", "${user_config.ocr}"]:
            with self.subTest(token=token), self.assertRaises(ValueError):
                configuration.ocr_value(token)
        configuration.configure_v2("chatgpt", self.grant, True, home=self.home)
        self.assertTrue(configuration.select_settings("chatgpt", None, None, home=self.home).ocr)
        self.assertFalse(
            configuration.select_settings("chatgpt", self.grant, None, home=self.home).ocr
        )
        with self.assertRaises(ValueError):
            configuration.select_settings("chatgpt", None, "off", home=self.home)
        with self.assertRaises(ValueError):
            configuration.configure_v2("unrecognized", self.grant, home=self.home)
