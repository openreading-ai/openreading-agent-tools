"""Relocate a diagnostic macOS Tesseract dependency closure into one private bundle.

Absolute names and library-local LC_RPATH entries are resolved. Unknown loader searches
refuse the build instead of depending on the developer's Homebrew configuration.
Ad-hoc signatures allow modified Mach-O files to execute on Apple Silicon. They provide
no publisher identity, notarization, or permission to distribute this diagnostic build.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def dependencies(binary: Path) -> list[str]:
    output = subprocess.check_output(["/usr/bin/otool", "-L", str(binary)], text=True)
    return [line.strip().split(" (", 1)[0] for line in output.splitlines()[1:] if line.strip()]


def resolve_dependency(name: str, source: Path) -> Path:
    if name.startswith("@loader_path/"):
        return (source.parent / name.removeprefix("@loader_path/")).resolve(strict=True)
    if name.startswith("@rpath/"):
        listing = subprocess.check_output(["/usr/bin/otool", "-l", str(source)], text=True)
        paths = []
        for block in listing.split("cmd LC_RPATH")[1:]:
            line = next(
                line.strip() for line in block.splitlines() if line.strip().startswith("path ")
            )
            prefix = line.removeprefix("path ").split(" (offset", 1)[0]
            if prefix.startswith("@loader_path/"):
                prefix = str(source.parent / prefix.removeprefix("@loader_path/"))
            if Path(prefix).is_absolute():
                candidate = Path(prefix) / name.removeprefix("@rpath/")
                if candidate.is_file():
                    paths.append(candidate.resolve(strict=True))
        if len(set(paths)) == 1:
            return paths[0]
        raise ValueError("Native rpath is unresolved or ambiguous.")
    if not Path(name).is_absolute():
        raise ValueError("Unresolved native install name; this build cannot relocate it.")
    return Path(name).resolve(strict=True)


def bundle_native(binary: Path, destination: Path) -> dict:
    source = binary.resolve(strict=True)
    target = destination / "bin/tesseract"
    target.parent.mkdir(parents=True)
    (destination / "lib").mkdir()
    sources = {source: target}
    names = {}
    pending = [source]
    edges = {}
    while pending:
        current = pending.pop()
        edges[current] = []
        for dependency in dependencies(current):
            if dependency.startswith(("/usr/lib/", "/System/Library/")):
                continue
            resolved = resolve_dependency(dependency, current)
            if resolved == current:
                continue
            if resolved not in sources:
                name = resolved.name
                if name in names and names[name] != resolved:
                    raise ValueError("Native dependencies have colliding filenames.")
                names[name] = resolved
                sources[resolved] = destination / "lib" / name
                pending.append(resolved)
            edges[current].append((dependency, resolved))
    for current, copied in sources.items():
        shutil.copy2(current, copied)
        # Homebrew bottles can be read-only; install_name_tool needs owner write access.
        copied.chmod(copied.stat().st_mode | 0o200)
        for original, resolved in edges[current]:
            replacement = "@loader_path/" + os.path.relpath(sources[resolved], copied.parent)
            subprocess.run(
                ["/usr/bin/install_name_tool", "-change", original, replacement, str(copied)],
                check=True,
            )
        if copied.suffix == ".dylib":
            subprocess.run(
                ["/usr/bin/install_name_tool", "-id", "@loader_path/" + copied.name, str(copied)],
                check=True,
            )
        subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", str(copied)], check=True)
    version = subprocess.check_output([str(target), "--version"], text=True, timeout=10)
    return {"tesseract": version.strip(), "libraries": sorted(names)}
