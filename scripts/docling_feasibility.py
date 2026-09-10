"""Measure the selected local engine with network denied and prohibited packages absent.

Preparation downloads only pinned layout assets on explicit request. Measurement never
installs packages or downloads files. Each cell starts a fresh process and performs one
cold conversion followed by two warm conversions. These are diagnostic observations,
not independent cold repetitions, p95 measurements, or supported product limits.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

PROHIBITED = ("torch", "torchvision", "docling_ibm_models", "pymupdf")
PAGE_COUNTS = (1, 10, 30, 100)


def accepts(observations, pages, ocr):
    runs = [row for row in observations if "run" in row]
    return len(runs) == 3 and all(
        row.get("run") == index
        and row.get("pages") == pages
        and row.get("status") == "success"
        and row.get("native_found") is True
        and row.get("table_found") is True
        and row.get("origins_match") is True
        and row.get("image_found") is ocr
        and isinstance(row.get("seconds"), (float, int))
        and math.isfinite(row["seconds"])
        and row["seconds"] > 0
        for index, row in enumerate(runs)
    )


def selected_environment():
    present = [name for name in PROHIBITED if importlib.util.find_spec(name) is not None]
    if present:
        raise RuntimeError(f"Prohibited packages are installed: {present}")


def prepare(args):
    from huggingface_hub import snapshot_download
    from openreading.adapters.docling_local.config import (
        MODEL_FILES,
        MODEL_REPOSITORY,
        MODEL_REVISION,
        LocalDoclingConfig,
    )

    snapshot_download(
        MODEL_REPOSITORY,
        revision=MODEL_REVISION,
        local_dir=args.assets / MODEL_REPOSITORY.replace("/", "--"),
        allow_patterns=[*MODEL_FILES, "README.md"],
    )
    LocalDoclingConfig(args.assets).validate_assets()


def generate(directory, font):
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen.canvas import Canvas

    picture = Image.new("RGB", (1200, 170), "white")
    ImageDraw.Draw(picture).text(
        (25, 50),
        "Seventy dollars is the service fee.",
        fill="black",
        font=ImageFont.truetype(str(font), 48),
    )
    hashes = {}
    for pages in PAGE_COUNTS:
        path = directory / f"case-{pages}.pdf"
        canvas = Canvas(str(path), invariant=1)
        for page in range(pages):
            canvas.drawString(50, 770, "RENEWAL POLICY")
            canvas.drawString(
                50,
                735,
                f"Physical source page {page + 1}. Provide notice at least 60 days before renewal.",
            )
            canvas.drawImage(ImageReader(picture), 50, 600, width=500, height=71)
            for x in [50, 220, 420]:
                canvas.line(x, 390, x, 510)
            for y in [390, 430, 470, 510]:
                canvas.line(50, y, 420, y)
            for row, (left, right) in enumerate(
                [
                    ("Policy", "Exception"),
                    ("Renewal", "EXCEPTION 17"),
                    ("Fee", "Deferred"),
                ]
            ):
                canvas.drawString(60, 480 - row * 40, left)
                canvas.drawString(230, 480 - row * 40, right)
            canvas.showPage()
        canvas.save()
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def convert(args):
    selected_environment()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    started = time.monotonic()
    from openreading.adapters.docling_local.client import LocalDoclingClient
    from openreading.adapters.docling_local.config import LocalDoclingConfig
    from openreading.adapters.docling_local.projection import project_document
    from openreading.types.request import Outputs

    config = LocalDoclingConfig(
        args.assets,
        ocr=args.ocr,
        tesseract_cmd=args.tesseract,
        tessdata_path=args.tessdata,
        dependency_lock=args.lock,
    )
    client = LocalDoclingClient(config)
    print(json.dumps({"stage": "setup", "seconds": time.monotonic() - started}), flush=True)
    for repetition in range(3):
        started = time.monotonic()
        raw = client.convert((args.output / f"case-{args.pages}.pdf").read_bytes())
        response, origins = project_document(
            raw, Outputs(text=True, blocks=True, markdown=False, tables="none")
        )
        texts = [page.text or "" for page in response.document.pages]
        print(
            json.dumps(
                {
                    "run": repetition,
                    "seconds": time.monotonic() - started,
                    "status": "success"
                    if response.status.state.value == "succeeded"
                    else "failure",
                    "pages": len(texts),
                    "native_found": all("60 days" in text for text in texts),
                    "image_found": all("Seventy dollars" in text for text in texts)
                    if args.ocr
                    else any("Seventy dollars" in text for text in texts),
                    "table_found": all("EXCEPTION 17" in text for text in texts),
                    "origins_match": len(origins) == args.pages
                    and all(
                        origin == ("mixed" if args.ocr else "native") for origin in origins.values()
                    ),
                    "text_bytes": len((response.document.text or "").encode()),
                }
            ),
            flush=True,
        )
        if repetition == 0:
            (args.output / f"converted-{args.pages}-{args.ocr}.json").write_text(
                json.dumps(raw, indent=2)
            )
            (args.output / f"projected-{args.pages}-{args.ocr}.json").write_text(
                json.dumps(response.to_schema_dict(), indent=2)
            )


def measure(args):
    import psutil

    selected_environment()
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise RuntimeError("This diagnostic runner requires Apple Silicon macOS network denial.")
    args.output.mkdir(parents=True, exist_ok=False)
    source_hashes = generate(args.output, args.font)
    report = {
        "format": "docling-feasibility.v1",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "lock_sha256": hashlib.sha256(args.lock.read_bytes()).hexdigest(),
        "font_sha256": hashlib.sha256(args.font.read_bytes()).hexdigest(),
        "source_hashes": source_hashes,
        "cells": [],
        "limits": {"seconds_per_cell": 300, "sampled_tree_rss_bytes": 4 * 1024**3},
        "limitations": [
            "one cold plus two warm conversions per cell",
            "not OS-cold or p95",
            "no base-machine or host-timeout proof",
            "client conversion and page projection exclude artifact commit",
        ],
    }
    for pages in PAGE_COUNTS:
        for ocr in [False, True]:
            command = [
                "/usr/bin/sandbox-exec",
                "-p",
                "(version 1) (allow default) (deny network*)",
                sys.executable,
                str(Path(__file__).resolve()),
                "convert",
                "--assets",
                str(args.assets),
                "--output",
                str(args.output),
                "--tesseract",
                str(args.tesseract),
                "--tessdata",
                str(args.tessdata),
                "--lock",
                str(args.lock),
                "--pages",
                str(pages),
            ]
            if ocr:
                command.append("--ocr")
            log = args.output / f"matrix-{pages}-{ocr}.log"
            started, peak, failure = time.monotonic(), 0, None
            with log.open("w") as stream:
                process = subprocess.Popen(
                    command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True
                )
                try:
                    while process.poll() is None:
                        try:
                            parent = psutil.Process(process.pid)
                            rss = sum(
                                child.memory_info().rss
                                for child in [parent, *parent.children(recursive=True)]
                            )
                        except psutil.NoSuchProcess:
                            continue
                        peak = max(peak, rss)
                        if peak > 4 * 1024**3 or time.monotonic() - started > 300:
                            failure = "memory" if peak > 4 * 1024**3 else "deadline"
                            os.killpg(process.pid, signal.SIGKILL)
                            break
                        time.sleep(0.1)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            observations = [
                json.loads(line) for line in log.read_text().splitlines() if line.startswith('{"')
            ]
            row = {
                "pages": pages,
                "ocr": ocr,
                "returncode": process.returncode,
                "failure": failure,
                "total_seconds": time.monotonic() - started,
                "peak_sampled_rss": peak,
                "observations": observations,
            }
            row["passed"] = (
                process.returncode == 0 and failure is None and accepts(observations, pages, ocr)
            )
            report["cells"].append(row)
            (args.output / "matrix.json").write_text(json.dumps(report, indent=2))
            print(json.dumps(row), flush=True)
    return 0 if all(row["passed"] for row in report["cells"]) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "measure", "convert"])
    parser.add_argument("--assets", required=True, type=lambda path: Path(path).resolve())
    parser.add_argument("--output", type=lambda path: Path(path).resolve())
    parser.add_argument("--font", type=lambda path: Path(path).resolve())
    parser.add_argument("--tesseract", type=lambda path: Path(path).resolve())
    parser.add_argument("--tessdata", type=lambda path: Path(path).resolve())
    parser.add_argument("--lock", type=lambda path: Path(path).resolve())
    parser.add_argument("--pages", type=int, choices=PAGE_COUNTS)
    parser.add_argument("--ocr", action="store_true")
    args = parser.parse_args()
    if args.action != "prepare" and any(
        getattr(args, name) is None for name in ["output", "tesseract", "tessdata", "lock"]
    ):
        parser.error(
            "Conversion and measurement require output, tesseract, tessdata, and lock paths."
        )
    if args.action == "measure" and args.font is None:
        parser.error("Measurement requires an explicit font path.")
    if args.action == "convert" and args.pages is None:
        parser.error("Internal conversion requires a page count.")
    return {"prepare": prepare, "measure": measure, "convert": convert}[args.action](args)


if __name__ == "__main__":
    raise SystemExit(main())
