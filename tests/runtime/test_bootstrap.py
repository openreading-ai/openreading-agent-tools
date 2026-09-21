"""Native plugin startup stays responsive while a verified runtime downloads."""

import copy
import hashlib
import io
import json
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from runtime import bootstrap


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.archive = self.root / "runtime.tar.gz"
        source = self.root / "source"
        source.mkdir()
        (source / "openreading-worker").write_text("synthetic worker")
        with tarfile.open(self.archive, "w:gz") as archive:
            archive.add(source, arcname="runtime")
        self.config = {
            "url": "https://example.test/runtime.tar.gz",
            "archive_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            "archive_bytes": self.archive.stat().st_size,
            "worker_sha256": "a" * 64,
            "catalogs": {"--settings-tools": {"tools": [{"name": "openreading_open_settings"}]}},
        }
        self.verify = self.enterContext(
            patch.object(bootstrap, "verify_release", return_value={"worker_sha256": "a" * 64})
        )

    def download(self):
        return patch.object(
            bootstrap, "open_download", side_effect=lambda url: self.archive.open("rb")
        )

    def test_download_verifies_and_reuses_cache_without_touching_settings(self):
        marker = self.root / "home/.openreading/marker"
        marker.parent.mkdir(parents=True)
        marker.write_text("retained")
        with self.download() as request:
            first = bootstrap.install(self.config, self.root / "home")
            second = bootstrap.install(self.config, self.root / "home")
        self.assertEqual(first, second)
        self.assertTrue((first / "openreading-worker").is_file())
        self.assertEqual(request.call_count, 1)
        self.assertEqual(marker.read_text(), "retained")
        self.assertFalse(list(first.parent.glob(".download-*")))

    def test_corrupt_download_refuses_before_extraction(self):
        self.config["archive_sha256"] = "b" * 64
        with self.download(), self.assertRaisesRegex(ValueError, "checksum"):
            bootstrap.install(self.config, self.root / "home")
        self.verify.assert_not_called()

    def test_mcp_initialize_and_catalog_do_not_wait_for_download(self):
        manager = bootstrap.Manager(self.config, self.root / "home")
        incoming = io.StringIO(
            "\n".join(
                json.dumps(x)
                for x in [
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-11-25"},
                    },
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "openreading_open_settings"},
                    },
                ]
            )
            + "\n"
        )
        output = io.StringIO()
        with patch.object(manager, "start"):
            bootstrap.serve(manager, "--settings-tools", incoming, output)
        responses = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([r["id"] for r in responses], [1, 2, 3])
        self.assertEqual(responses[1]["result"], self.config["catalogs"]["--settings-tools"])
        self.assertTrue(responses[2]["result"]["isError"])
        self.assertIn("Downloading", responses[2]["result"]["content"][0]["text"])

    def test_size_worker_and_cache_failures_leave_no_installed_payload(self):
        for change in ({"archive_bytes": 1}, {"archive_bytes": 1000000}):
            with self.subTest(change=change), self.download():
                with self.assertRaises(ValueError):
                    bootstrap.install({**self.config, **change}, self.root / "home")
        self.verify.return_value = {"worker_sha256": "c" * 64}
        with self.download(), self.assertRaisesRegex(ValueError, "worker"):
            bootstrap.install(self.config, self.root / "home")
        self.verify.return_value = {"worker_sha256": "a" * 64}
        with self.download():
            target = bootstrap.install(self.config, self.root / "home")
        self.verify.return_value = {"worker_sha256": "c" * 64}
        with self.assertRaisesRegex(ValueError, "Cached"):
            bootstrap.install(self.config, self.root / "home")
        self.assertTrue(target.is_dir())

    def test_invalid_digest_and_symlink_cache_refuse(self):
        with self.assertRaisesRegex(ValueError, "digest"):
            bootstrap.install({**self.config, "worker_sha256": "../bad"}, self.root / "home")
        home = self.root / "home"
        home.mkdir()
        (home / "Library").symlink_to(self.root / "outside")
        with self.assertRaisesRegex(ValueError, "symbolic"):
            bootstrap.install(self.config, home)

    def test_archive_traversal_is_rejected(self):
        with tarfile.open(self.archive, "w:gz") as archive:
            member = tarfile.TarInfo("../../escaped")
            member.size = 1
            archive.addfile(member, io.BytesIO(b"x"))
        self.config.update(
            archive_bytes=self.archive.stat().st_size,
            archive_sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest(),
        )
        with self.download(), self.assertRaises(tarfile.TarError):
            bootstrap.install(self.config, self.root / "home")

    def test_https_origin_redirects_and_system_certificates(self):
        with self.assertRaises(ValueError):
            bootstrap.open_download("http://example.test/file")
        with (
            patch.object(bootstrap.ssl, "create_default_context") as ssl,
            patch.object(bootstrap.urllib.request, "build_opener") as opener,
        ):
            bootstrap.open_download(self.config["url"])
            ssl.assert_called_once_with(cafile="/etc/ssl/cert.pem")
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header("Ngrok-skip-browser-warning"), "1")
        redirect = bootstrap.HTTPSRedirect()
        with self.assertRaises(ValueError):
            redirect.redirect_request(None, None, 302, "Found", {}, "http://example.test/file")
        with patch.object(
            bootstrap.urllib.request.HTTPRedirectHandler, "redirect_request", return_value="safe"
        ):
            self.assertEqual(
                redirect.redirect_request(None, None, 302, "Found", {}, self.config["url"]), "safe"
            )

    def test_manager_reports_failure_and_retries_then_stays_offline(self):
        manager = bootstrap.Manager(self.config, self.root)
        with patch.object(bootstrap, "install", side_effect=OSError("offline")):
            manager.start()
            manager.thread.join(2)
        self.assertIn("offline", manager.status)
        with patch.object(bootstrap, "install", return_value=self.root) as install:
            manager.start()
            manager.thread.join(2)
            manager.start()
        install.assert_called_once()
        self.assertEqual(manager.root, self.root)
        manager.progress("halfway")
        self.assertEqual(manager.status, "halfway")

    def test_proxy_forwards_real_worker_results_and_reports_worker_exit(self):
        worker = self.root / "openreading-worker"
        worker.write_text(f"""#!{sys.executable}
import json,sys
for line in sys.stdin:
 r=json.loads(line)
 if 'id' not in r: continue
 if r['method']=='initialize': result={{}}
 elif r['method']=='tools/list': result={self.config["catalogs"]["--settings-tools"]!r}
 elif r['id']==4: sys.exit(1)
 else: result={{'content':[{{'type':'text','text':'worker response'}}]}}
 print(json.dumps({{'jsonrpc':'2.0','id':r['id'],'result':result}}),flush=True)
""")
        worker.chmod(0o755)
        manager = bootstrap.Manager(self.config, self.root)
        manager.root = self.root
        output = io.StringIO()

        def incoming():
            for identifier in (3, 4):
                yield (
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": identifier,
                            "method": "tools/call",
                            "params": {"name": "openreading_open_settings"},
                        }
                    )
                    + "\n"
                )
                deadline = time.monotonic() + 3
                while (
                    f'"id": {identifier},' not in output.getvalue() and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
            yield json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"

        with patch.object(manager, "start"):
            # The exit case closes the input pipe; the final notification may encounter EOF.
            try:
                bootstrap.serve(manager, "--settings-tools", incoming(), output)
            except BrokenPipeError:
                pass
        messages = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(messages[0]["result"]["content"][0]["text"], "worker response")
        self.assertIn("stopped", messages[1]["error"]["message"])

    def test_worker_initialization_and_catalog_mismatch_terminate_child(self):
        manager = bootstrap.Manager(self.config, self.root)
        manager.root = self.root
        for replies in (
            '{"id": 0, "error": {}}\n',
            '{"id": 0, "result": {}}\n{"id": 1, "result": {"tools": []}}\n',
        ):
            child = MagicMock()
            child.stdout = io.StringIO(replies)
            with (
                patch.object(bootstrap.subprocess, "Popen", return_value=child),
                self.assertRaises(ValueError),
            ):
                bootstrap.start_worker(manager, "--settings-tools", "2025-11-25")
            child.terminate.assert_called_once()

    def test_verified_server_catalog_keeps_upload_annotations_and_is_advertised(self):
        local = self.config["catalogs"]["--settings-tools"]
        server = copy.deepcopy(local)
        server["tools"][0].update(
            description="Uploads to your configured Core server.",
            annotations={"openWorldHint": True, "idempotentHint": False},
        )
        self.config["catalog_variants"] = {"--settings-tools": [local, server]}
        manager = bootstrap.Manager(self.config, self.root)
        manager.root = self.root
        child = MagicMock()
        child.stdout = io.StringIO(
            json.dumps({"id": 0, "result": {}})
            + "\n"
            + json.dumps({"id": 1, "result": server})
            + "\n"
        )
        with patch.object(bootstrap.subprocess, "Popen", return_value=child):
            accepted = bootstrap.start_worker(manager, "--settings-tools", "2025-11-25")
        self.assertEqual(accepted.catalog, server)
        child.terminate.assert_not_called()
        incoming = io.StringIO('{"id":2,"method":"tools/list"}\n')
        output = io.StringIO()
        child.stdout = io.StringIO()
        with (
            patch.object(manager, "start"),
            patch.object(bootstrap, "start_worker", return_value=child),
        ):
            bootstrap.serve(manager, "--settings-tools", incoming, output)
        self.assertEqual(json.loads(output.getvalue())["result"], server)

    def test_completed_setup_notifies_catalog_change_before_returning_active_tools(self):
        manager = bootstrap.Manager(self.config, self.root)
        active = {"tools": [{"name": "openreading_open_settings", "description": "verified"}]}
        child = MagicMock(catalog=active)
        child.stdout = io.StringIO()
        output = io.StringIO()

        def incoming():
            yield '{"id":1,"method":"tools/list"}\n'
            manager.root = self.root
            yield '{"id":2,"method":"tools/list"}\n'

        with (
            patch.object(manager, "start"),
            patch.object(bootstrap, "start_worker", return_value=child),
        ):
            bootstrap.serve(manager, "--settings-tools", incoming(), output)
        replies = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(replies[0]["result"], self.config["catalogs"]["--settings-tools"])
        self.assertEqual(replies[1]["method"], "notifications/tools/list_changed")
        self.assertEqual(replies[2]["result"], active)

    def test_protocol_errors_and_failed_worker_are_reported(self):
        manager = bootstrap.Manager(self.config, self.root)
        manager.root = self.root
        incoming = io.StringIO(
            'garbage\n{"id":1,"method":"ping"}\n{"id":2,"method":"missing"}\n{"id":3,"method":"tools/call"}\n'
        )
        output = io.StringIO()
        with (
            patch.object(manager, "start"),
            patch.object(bootstrap, "start_worker", side_effect=ValueError("synthetic")),
        ):
            bootstrap.serve(manager, "--settings-tools", incoming, output)
        replies = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(replies[0]["error"]["code"], -32700)
        self.assertEqual(replies[1]["result"], {})
        self.assertEqual(replies[2]["error"]["code"], -32601)
        self.assertIn("synthetic", replies[3]["result"]["content"][0]["text"])

    def test_main_checks_platform_and_connector(self):
        with patch.object(bootstrap.sys, "platform", "linux"), self.assertRaises(ValueError):
            bootstrap.main([])
        config = self.root / "bootstrap.json"
        config.write_text(json.dumps(self.config))
        with (
            patch.object(bootstrap.sys, "platform", "darwin"),
            patch.object(bootstrap.platform, "machine", return_value="arm64"),
        ):
            with self.assertRaises(ValueError):
                bootstrap.main([str(config), "missing"])
            with patch.object(bootstrap, "serve") as serve:
                bootstrap.main([str(config), "--settings-tools"])
                serve.assert_called_once()
