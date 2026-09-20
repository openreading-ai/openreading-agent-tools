"""Build a deterministic runtime download separately from client plugin archives.

The builder receives an explicitly verified runtime. The payload retains every file,
including Docling assets and optional Core-server support. Content hashes bind the
plugin to one payload; a release never resolves a moving latest-version endpoint.
The caller supplies the eventual HTTPS asset directory. Building does not publish,
probe that directory, install anything, or authenticate a publisher. Native signing
and distribution availability remain separate acceptance requirements.
"""

from __future__ import annotations

import gzip
import tarfile
from pathlib import Path
from urllib.parse import urlsplit

from runtime.verify import sha256


def validate_base_url(url: str) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or any(ord(char) <= 32 or ord(char) >= 127 for char in url)
        or any(char in url for char in "%\\?#")
        or ".." in parsed.path.split("/")
    ):
        raise ValueError(
            "Runtime downloads require an HTTPS URL without credentials or query data."
        )


def pack(runtime: Path, output: Path, base_url: str) -> dict:
    validate_base_url(base_url)
    digest = sha256(runtime / "release.json")
    output.mkdir(parents=True)
    payload = output / f"openreading-runtime-{digest}.tar.gz"
    # Stable headers make the same reviewed runtime reproduce the same download hash.
    with (
        payload.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed,
    ):
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in sorted(runtime.rglob("*")):
                if path.is_file():
                    item = tarfile.TarInfo(path.relative_to(runtime).as_posix())
                    item.size = path.stat().st_size
                    item.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                    with path.open("rb") as contents:
                        archive.addfile(item, contents)
    return {
        "url": base_url.rstrip("/") + "/" + payload.name,
        "sha256": sha256(payload),
        "length": payload.stat().st_size,
    }
