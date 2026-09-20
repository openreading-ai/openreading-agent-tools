"""Run the real Docling corpus gate under externally enforced network denial.

This opt-in developer command imports from the locked installed distribution only.
Run it through sandbox-exec as shown in measurement/README.md. It refuses a working
network, mismatched corpus bytes, or an existing report. Functional OCR is separate
from the three OCR-disabled primary documents. Diagnostics are not product limits.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from measurement.corpus import generate, recipe  # noqa: E402
from measurement.retrieval import evaluate  # noqa: E402
from scripts.docling_feasibility import network_denied, selected_environment  # noqa: E402


def check(args):
    if not network_denied():
        raise ValueError("Network denial was not observed.")
    environment = selected_environment(args.lock)
    if args.output.exists():
        raise FileExistsError("Use a new evidence directory.")
    from openreading.adapters.docling_local.config import LocalDoclingConfig
    from openreading.artifacts.limits import DoclingLimits, ProfileConfig
    from openreading.artifacts.service import ArtifactService

    generation = generate(args.output)
    spec = recipe()
    if generation["files"] != spec["expected_hashes"]:
        raise ValueError("Generated corpus bytes differ from the frozen recipe.")
    report = {
        "generation": generation,
        "environment": environment,
        "network_denied": True,
        "tasks": [],
        "documents": {},
        "functional": {},
    }
    for ocr in (False, True):
        config = ProfileConfig(
            input_root=args.output / "documents",
            artifact_root=args.output / f"store-{ocr}",
            limits=DoclingLimits(
                pages=100,
                deadline_seconds=300,
                worker_memory_bytes=4 * 1024**3,
                worker_idle_seconds=60,
            ),
            docling=LocalDoclingConfig(
                args.assets,
                ocr=ocr,
                dependency_lock=args.lock,
                tesseract_cmd=args.tesseract,
                tessdata_path=args.tessdata,
            ),
        )
        service = ArtifactService(config)
        try:
            names = ["functional"] if ocr else [*spec["documents"], "functional"]
            for name in names:
                started = time.monotonic()
                receipt = service.import_document(f"{name}.pdf")
                manifest, passages = service.store.load(receipt.artifact_id)
                folder = service.store.documents / receipt.artifact_id
                response = json.loads((folder / "response.json").read_text())
                if manifest.document_sha256 != generation["files"][f"{name}.pdf"]:
                    raise ValueError("Imported source differs from the frozen input.")
                warnings = sorted({w["code"] for w in response.get("warnings", [])})
                record = {
                    "receipt": receipt.wire(),
                    "engine": manifest.engine.wire(),
                    "warnings": warnings,
                    "origins": manifest.page_origins,
                    "import_seconds": time.monotonic() - started,
                }
                pages = response["document"]["pages"]
                # This projection is also arm B's input. Blocks are never duplicated into it.
                text = "\n\n".join(
                    f"[Physical page {p['page_number']}]\n{p.get('text') or ''}" for p in pages
                )
                (args.output / f"{name}-ocr-{ocr}.txt").write_text(text)
                record["full_text_sha256"] = hashlib.sha256(text.encode()).hexdigest()
                if name == "functional":
                    page_text = {p["page_number"]: (p.get("text") or "") for p in pages}
                    record["checks"] = {
                        "pages": list(page_text) == list(range(1, 7)),
                        "blank_none": manifest.page_origins["4"] == "none",
                        "native": "30 days" in page_text[1]
                        and manifest.page_origins["1"] == "native",
                        "scanned": ("45 days" in page_text[2]) is ocr,
                        "mixed_scan": ("two signatures" in page_text[3]) is ocr,
                        "scan_origin": manifest.page_origins["2"] == ("ocr" if ocr else "none"),
                        "mixed_origin": manifest.page_origins["3"]
                        == ("mixed" if ocr else "native"),
                        "columns": all(
                            t in page_text[5] for t in ["filter inspection", "motor inspection"]
                        ),
                        "ligature_search": any(
                            h.page == 6 for h in service.search(receipt.artifact_id, "office").hits
                        ),
                        "dehyphenation_search": any(
                            h.page == 6 for h in service.search(receipt.artifact_id, "renewal").hits
                        ),
                    }
                    report["functional"][str(ocr)] = record
                else:
                    if not set(warnings) <= {"table_text_unavailable", "furniture_text_omitted"}:
                        raise ValueError(f"Unexpected primary extraction warnings: {warnings}")
                    if len(pages) != spec["documents"][name]["pages"]:
                        raise ValueError("Physical page count differs from the frozen corpus.")
                    report["documents"][name] = record
                    for task in (t for t in spec["tasks"] if t["document"] == name):
                        report["tasks"].append(
                            evaluate(service, receipt.artifact_id, task, passages)
                        )
        finally:
            service.close()
    report["passed"] = all(
        row["passed"] for row in report["tasks"] if row["passed"] is not None
    ) and all(all(row["checks"].values()) for row in report["functional"].values())
    (args.output / "retrieval-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("assets", "output", "lock", "tesseract", "tessdata"):
        parser.add_argument(f"--{name}", required=True, type=lambda value: Path(value).resolve())
    args = parser.parse_args(argv)
    report = check(args)
    print(
        json.dumps(
            {"passed": report["passed"], "report": str(args.output / "retrieval-report.json")}
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
