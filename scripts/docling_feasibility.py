"""Measure the selected local engine with network denied and prohibited packages absent.

Preparation downloads only pinned layout assets on explicit request. Measurement never
installs packages or downloads files. Each cell starts a fresh process and performs one
first conversion, including native initialization, followed by two warm conversions.
These are diagnostic observations, not independent cold repetitions, p95 measurements,
or supported product limits.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import os
import platform
import re
import signal
import socket
import subprocess
import sys
import time
import tomllib
from importlib import metadata
from pathlib import Path

# PyMuPDF releases before 1.24.3 install only the legacy `fitz` module.
PROHIBITED = ("torch", "torchvision", "docling_ibm_models", "pymupdf", "fitz")
PAGE_COUNTS = (1, 10, 30, 100)
RASTER_TEXT = "Seventy dollars is the service fee."
NATIVE_TEXT = ("RENEWAL POLICY", "Provide notice at least 60 days before renewal.")
TABLE_TEXT = ("Policy", "Exception", "Renewal", "EXCEPTION 17", "Fee", "Deferred")
# Table structure is disabled, so the core projection always discloses the table region.
# Any other warning, such as omitted provenance or unreadable pages, is an incomplete result.
ALLOWED_WARNINGS = {"table_text_unavailable"}
MARKER = re.compile(r"Physical source page (\d+)\.")
RSS_LIMIT = 4 * 1024**3
CELL_SECONDS = 300


def accepts(observations, pages, ocr):
    setup = [row for row in observations if row.get("stage") == "setup"]
    runs = [row for row in observations if "run" in row]
    return (
        len(setup) == 1
        and setup[0].get("network_denied") is True
        and len(runs) == 3
        and all(
            row.get("run") == index
            and row.get("pages") == pages
            and row.get("status") == "success"
            and row.get("page_numbers_match") is True
            and row.get("page_markers_match") is True
            and row.get("native_found") is True
            and row.get("table_found") is True
            and row.get("origins_match") is True
            and row.get("image_found") is ocr
            and isinstance(row.get("warnings"), list)
            and set(row["warnings"]) <= ALLOWED_WARNINGS
            and isinstance(row.get("seconds"), (float, int))
            and math.isfinite(row["seconds"])
            and row["seconds"] > 0
            for index, row in enumerate(runs)
        )
    )


def inspect_pages(pages, ocr, schema, origins):
    """Compare every projected physical page with the text drawn on that fixture page.

    Aggregate or repeated text cannot pass: each page must carry only its own marker,
    so shifted, duplicated, or reordered page provenance fails the matrix.
    """
    projected = [(page["page_number"], page["text"] or "") for page in schema["document"]["pages"]]
    texts = [text for _, text in projected]
    return {
        "pages": len(projected),
        "page_numbers_match": [number for number, _ in projected] == list(range(1, pages + 1)),
        "page_markers_match": all(
            MARKER.findall(text) == [str(number)] for number, text in projected
        ),
        "native_found": all(all(value in text for value in NATIVE_TEXT) for text in texts),
        # With OCR off, the raster sentence must be absent from every page.
        "image_found": all(RASTER_TEXT in text for text in texts)
        if ocr
        else any(RASTER_TEXT in text for text in texts),
        "table_found": all(all(value in text for value in TABLE_TEXT) for text in texts),
        "origins_match": origins
        == {number: "mixed" if ocr else "native" for number in range(1, pages + 1)},
        "warnings": sorted({warning["code"] for warning in schema.get("warnings") or []}),
    }


def network_denied():
    """Loopback connection fails with EPERM only under operating-system network denial.

    Without denial, the same closed port refuses the connection instead.
    """
    try:
        socket.create_connection(("127.0.0.1", 9), timeout=1).close()
    except PermissionError:
        return True
    except OSError:
        return False
    return False


def required_packages(locked):
    """Follow active lock edges and requested extras for this interpreter and platform."""
    from packaging.markers import Marker

    pending = [("openreading-docling-feasibility", ())]
    seen, required = set(), set()
    while pending:
        name, extras = pending.pop()
        if (name, extras) in seen:
            continue
        seen.add((name, extras))
        package = locked[name]
        if "virtual" not in package.get("source", {}):
            required.add(name)
        edges = list(package.get("dependencies", []))
        for extra in extras:
            edges.extend(package.get("optional-dependencies", {}).get(extra, []))
        for edge in edges:
            if "marker" not in edge or Marker(edge["marker"]).evaluate():
                pending.append((edge["name"], tuple(sorted(edge.get("extra", [])))))
    return required


def selected_environment(lock):
    """Require the running interpreter to hold exactly the locked candidate.

    A sibling checkout on PYTHONPATH or an editable core install would otherwise report
    the pinned lock while measuring different engine code.
    """
    present = [name for name in PROHIBITED if importlib.util.find_spec(name) is not None]
    if present:
        raise RuntimeError(f"Prohibited packages are installed: {present}")
    locked = {package["name"]: package for package in tomllib.loads(lock.read_text())["package"]}
    installed = {}
    for distribution in metadata.distributions():
        name = re.sub(r"[-_.]+", "-", distribution.metadata["Name"]).lower()
        if locked.get(name, {}).get("version") != distribution.version:
            raise RuntimeError(f"Installed {name} {distribution.version} is not in the lock.")
        installed[name] = distribution.version
    missing = required_packages(locked) - installed.keys()
    if missing:
        raise RuntimeError(f"Locked dependencies are missing: {sorted(missing)}")
    core = metadata.distribution("openreading")
    origin = json.loads(core.read_text("direct_url.json") or "{}")
    commit = origin.get("vcs_info", {}).get("commit_id")
    expected = locked["openreading"]["source"]["git"].rpartition("#")[2]
    spec = importlib.util.find_spec("openreading")
    module = Path(core.locate_file("openreading/__init__.py")).resolve()
    if commit != expected or spec is None or Path(spec.origin).resolve() != module:
        raise RuntimeError("The imported core is not the locked core commit.")
    return {"core_commit": commit, "packages": dict(sorted(installed.items()))}


def tree_rss(pid):
    """Sum RSS for the sampled process tree; children exiting mid-sample are skipped."""
    import psutil

    try:
        parent = psutil.Process(pid)
        processes = [parent, *parent.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0
    except psutil.Error:
        return None
    total = 0
    for process in processes:
        try:
            total += process.memory_info().rss
        except psutil.NoSuchProcess:
            if process.pid == pid:
                return 0
        except psutil.Error:
            return None
    return total


def read_observations(log):
    """Parse JSON observation lines; corrupted lines drop rows and therefore fail the cell."""
    rows = []
    for line in log.read_text(errors="replace").splitlines():
        if line.startswith('{"'):
            with contextlib.suppress(json.JSONDecodeError):
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
    return rows


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
        RASTER_TEXT,
        fill="black",
        font=ImageFont.truetype(str(font), 48),
    )
    hashes = {}
    for pages in PAGE_COUNTS:
        path = directory / f"case-{pages}.pdf"
        canvas = Canvas(str(path), invariant=1)
        for page in range(pages):
            canvas.drawString(50, 770, NATIVE_TEXT[0])
            canvas.drawString(50, 735, f"Physical source page {page + 1}. {NATIVE_TEXT[1]}")
            canvas.drawImage(ImageReader(picture), 50, 600, width=500, height=71)
            for x in [50, 220, 420]:
                canvas.line(x, 390, x, 510)
            for y in [390, 430, 470, 510]:
                canvas.line(50, y, 420, y)
            for row, (left, right) in enumerate(
                zip(TABLE_TEXT[::2], TABLE_TEXT[1::2], strict=True)
            ):
                canvas.drawString(60, 480 - row * 40, left)
                canvas.drawString(230, 480 - row * 40, right)
            canvas.showPage()
        canvas.save()
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def convert(args):
    selected_environment(args.lock)
    denied = network_denied()
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
    setup = {
        "stage": "setup",
        "seconds": time.monotonic() - started,
        "network_denied": denied,
    }
    print(json.dumps(setup), flush=True)
    if not denied:
        raise RuntimeError("Conversion requires operating-system network denial.")
    for repetition in range(3):
        started = time.monotonic()
        raw = client.convert((args.output / f"case-{args.pages}.pdf").read_bytes())
        response, origins = project_document(
            raw, Outputs(text=True, blocks=True, markdown=False, tables="none")
        )
        seconds = time.monotonic() - started
        schema = response.to_schema_dict()
        print(
            json.dumps(
                {
                    "run": repetition,
                    "seconds": seconds,
                    "status": "success"
                    if response.status.state.value == "succeeded"
                    else "failure",
                    **inspect_pages(args.pages, args.ocr, schema, origins),
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
                json.dumps(schema, indent=2)
            )


def measure(args):
    identity = selected_environment(args.lock)
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise RuntimeError("This diagnostic runner requires Apple Silicon macOS network denial.")
    from openreading.adapters.docling_local.config import LocalDoclingConfig

    # Fail before any cell when assets differ, and record OCR executable and data identity.
    engine_hashes = LocalDoclingConfig(
        args.assets,
        ocr=True,
        tesseract_cmd=args.tesseract,
        tessdata_path=args.tessdata,
        dependency_lock=args.lock,
    ).validate_assets()
    version = subprocess.run(
        [str(args.tesseract), "--version"], capture_output=True, text=True, check=True
    )
    args.output.mkdir(parents=True, exist_ok=False)
    source_hashes = generate(args.output, args.font)
    report = {
        "format": "docling-feasibility.v2",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        **identity,
        "tesseract_version": (version.stdout or version.stderr).splitlines()[0],
        "engine_hashes": engine_hashes,
        "lock_sha256": hashlib.sha256(args.lock.read_bytes()).hexdigest(),
        "font_sha256": hashlib.sha256(args.font.read_bytes()).hexdigest(),
        "source_hashes": source_hashes,
        "cells": [],
        "limits": {
            "seconds_per_cell": CELL_SECONDS,
            "sampled_tree_rss_bytes": RSS_LIMIT,
        },
        "limitations": [
            "one first plus two warm conversions per cell",
            "not OS-cold or p95",
            "no base-machine or host-timeout proof",
            "conversion timings include asset hashing and page projection",
            "timings exclude staging, supervised worker control, and artifact commit",
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
            started, peak, samples, failure = time.monotonic(), 0, 0, None
            with log.open("w") as stream:
                process = subprocess.Popen(
                    command,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=args.output,
                )
                try:
                    while process.poll() is None:
                        rss = tree_rss(process.pid)
                        if rss is None and process.poll() is None:
                            failure = "memory_monitor"
                            break
                        if rss is not None and rss > 0:
                            samples += 1
                            peak = max(peak, rss)
                        if peak > RSS_LIMIT or time.monotonic() - started > CELL_SECONDS:
                            failure = "memory" if peak > RSS_LIMIT else "deadline"
                            break
                        time.sleep(0.1)
                finally:
                    # Kill the whole session group even after a normal exit, so an orphaned
                    # OCR child cannot overlap the next cell's timing or memory samples.
                    with contextlib.suppress(ProcessLookupError, PermissionError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            observations = read_observations(log)
            row = {
                "pages": pages,
                "ocr": ocr,
                "returncode": process.returncode,
                "failure": failure,
                "total_seconds": time.monotonic() - started,
                "peak_sampled_rss": peak,
                "rss_samples": samples,
                "observations": observations,
            }
            row["passed"] = (
                process.returncode == 0
                and failure is None
                and samples > 0
                and accepts(observations, pages, ocr)
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
