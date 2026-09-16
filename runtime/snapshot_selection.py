"""Copy user-selected adapter-supported files without granting continuing folder access.

Traversal uses an iterative stack, never follows symlinks, and deduplicates device/inode
identities across overlapping selections. Discovered hidden entries, macOS packages, unsupported files
and special files are skipped with aggregate counts. Counts describe encountered entries;
skipped directories are not inspected. Unreadable or changed entries fail the entire copy.
There is no fixed count, byte or recursion cutoff. Cancellation is checked between entries
and within each existing intake copy. Ordinary failures revoke only this snapshot's copies.
A snapshot is a sequence of per-file copies, not a filesystem-wide atomic point in time.
Files discovered after enumeration are not included. Each copied file is checked for changes.
Receipt names contain basenames only; duplicate basenames keep separate opaque references.
"""

from __future__ import annotations

import ctypes
import os
import stat
from collections import Counter
from pathlib import Path

from openreading.artifacts.intake import directory

from runtime.selection import SelectionError, SelectionStore


def is_package(path: Path) -> bool:
    """Read macOS's package flag without starting Finder or indexing the directory."""
    cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    pointer = ctypes.c_void_p
    cf.CFURLCreateFromFileSystemRepresentation.argtypes = [
        pointer,
        ctypes.c_char_p,
        ctypes.c_long,
        ctypes.c_bool,
    ]
    cf.CFURLCreateFromFileSystemRepresentation.restype = pointer
    cf.CFURLCopyResourcePropertyForKey.argtypes = [
        pointer,
        pointer,
        ctypes.POINTER(pointer),
        ctypes.POINTER(pointer),
    ]
    cf.CFURLCopyResourcePropertyForKey.restype = ctypes.c_bool
    cf.CFBooleanGetValue.argtypes = [pointer]
    cf.CFBooleanGetValue.restype = ctypes.c_bool
    cf.CFRelease.argtypes = [pointer]
    raw = os.fsencode(path)
    url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), True)
    if not url:
        raise SelectionError("Cannot inspect this selected directory.")
    value, error = pointer(), pointer()
    try:
        key = pointer.in_dll(cf, "kCFURLIsPackageKey")
        if not cf.CFURLCopyResourcePropertyForKey(
            url, key, ctypes.byref(value), ctypes.byref(error)
        ):
            raise SelectionError("Cannot inspect this selected directory.")
        return bool(cf.CFBooleanGetValue(value))
    finally:
        for item in (value, error, url):
            if item:
                cf.CFRelease(item)


def snapshot(store: SelectionStore, paths: list[Path], *, cancelled=lambda: False) -> dict:
    references = []
    skipped: Counter[str] = Counter()
    seen = set()
    pending = [(path, None) for path in reversed(paths)]

    def check():
        if cancelled():
            raise SelectionError("Selection cancelled. No snapshot was returned.")

    try:
        check()
        with store.locked():
            store.used_bytes()
        while pending:
            check()
            path, expected = pending.pop()
            if not path.is_absolute():
                raise SelectionError("Choose absolute local files or directories.")
            info = path.lstat()
            identity = (info.st_dev, info.st_ino)
            if expected is not None and expected != identity:
                raise SelectionError("A selected entry changed. Select it again.")
            if stat.S_ISLNK(info.st_mode):
                skipped["symlink"] += 1
                continue
            if expected is not None and (
                path.name.startswith(".")
                or getattr(info, "st_flags", 0) & getattr(stat, "UF_HIDDEN", 0)
            ):
                skipped["hidden"] += 1
                continue
            if identity in seen:
                skipped["duplicate"] += 1
                continue
            seen.add(identity)
            if stat.S_ISDIR(info.st_mode):
                if is_package(path):
                    skipped["package"] += 1
                    continue
                with directory(path) as opened:
                    before = os.fstat(opened)
                    if (before.st_dev, before.st_ino) != identity:
                        raise SelectionError("A selected directory changed. Select it again.")
                    entries = []
                    for name in sorted(os.listdir(opened), reverse=True):
                        check()
                        child = os.stat(name, dir_fd=opened, follow_symlinks=False)
                        entries.append((path / name, (child.st_dev, child.st_ino)))
                    after = os.fstat(opened)
                    if (before.st_mtime_ns, before.st_ctime_ns) != (
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                    ):
                        raise SelectionError("A selected directory changed. Select it again.")
                    pending.extend(entries)
            elif stat.S_ISREG(info.st_mode):
                if not store.supports_name(path.name):
                    skipped["unsupported"] += 1
                    continue
                result = store.select(
                    path, cancelled=cancelled, expected_identity=identity, _existing_checked=True
                )
                references.append(result.reference)
            else:
                skipped["special"] += 1
        check()
        return {"references": tuple(references), "skipped": dict(skipped)}
    except BaseException:
        # Revocation never takes the publisher lock and cannot remove older selections.
        failures = []
        for reference in references:
            try:
                store.rollback(reference)
            except Exception as error:
                failures.append(error)
        if failures:
            raise SelectionError(
                "Snapshot cleanup failed. Clear private intake before retrying."
            ) from None
        raise
