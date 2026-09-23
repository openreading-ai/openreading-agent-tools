"""A migrated real artifact retains its identity and readable evidence under the new intake."""

import tempfile
import unittest
from pathlib import Path

from openreading.artifacts.limits import ProfileConfig
from openreading.artifacts.service import ArtifactService
from reportlab.pdfgen import canvas

from runtime.app_settings import save_preferences
from runtime.storage_settings import storage_session


class MigrationTests(unittest.TestCase):
    def test_real_import_remains_readable_after_copy_and_grant_rebinding(self):
        home = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        with storage_session("chatgpt", home=home) as old:
            intake = old / "selection/ready"
            intake.mkdir(parents=True)
            pdf = canvas.Canvas(str(intake / "synthetic.pdf"))
            pdf.drawString(50, 750, "Storage migration preserves this synthetic evidence.")
            pdf.save()
            service = ArtifactService(ProfileConfig(intake, old / "artifacts"))
            try:
                receipt = service.import_document("synthetic.pdf")
                original_grant = service.store.grant
            finally:
                service.close()
        save_preferences("chatgpt", home / "Downloads/OpenReading", 8192, home=home)
        with storage_session("chatgpt", home=home) as new:
            service = ArtifactService(ProfileConfig(new / "selection/ready", new / "artifacts"))
            try:
                self.assertNotEqual(original_grant, service.store.grant)
                manifest, passages = service.store.load(receipt.artifact_id)
                self.assertEqual(manifest.artifact_id, receipt.artifact_id)
                self.assertTrue(passages)
            finally:
                service.close()
        service = ArtifactService(ProfileConfig(old / "selection/ready", old / "artifacts"))
        try:
            self.assertEqual(
                service.store.load(receipt.artifact_id)[0].artifact_id, receipt.artifact_id
            )
        finally:
            service.close()

    def test_completed_jobs_rebind_but_corrupt_records_never_publish_a_switch(self):
        import json

        from runtime.storage_settings import data_root, grant_id

        home = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        with storage_session("chatgpt", home=home) as old:
            (old / "selection/ready").mkdir(parents=True)
            before = grant_id(old / "selection/ready")
            job = old / "artifacts/jobs" / before / "j1_synthetic"
            job.mkdir(parents=True)
            (job / "status.json").write_text(json.dumps({"state": "succeeded"}))
            (job / "request.json").write_text(
                json.dumps(
                    {
                        "grant": before,
                        "input_root": str(old / "selection/ready"),
                        "artifact_root": str(old / "artifacts"),
                    }
                )
            )
        save_preferences("chatgpt", home / "new", 8192, home=home)
        with storage_session("chatgpt", home=home) as new:
            after = grant_id(new / "selection/ready")
            record = json.loads(
                (new / "artifacts/jobs" / after / "j1_synthetic/request.json").read_text()
            )
            self.assertEqual(record["grant"], after)
            self.assertEqual(record["input_root"], str(new / "selection/ready"))
            (new / "artifacts/jobs" / after / "j1_synthetic/request.json").write_text(
                '{"grant":"wrong"}'
            )
        save_preferences("chatgpt", home / "third", 8192, home=home)
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            with storage_session("chatgpt", home=home):
                pass
        self.assertEqual(data_root("chatgpt", home=home), new)
