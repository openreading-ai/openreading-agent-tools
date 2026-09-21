"""Switch client storage at reconnect without deleting the previous retained copy.

A shared control-directory lock covers each document connection. Migration needs exclusive
ownership and terminal import jobs. The target client partition must not already exist;
merging independent stores could mix grants. Files are copied before the active pointer
changes. Failures remove only the newly reserved partition and keep the old pointer.
Core binds evidence to the intake path and inode. Only the copied private intake grant
is rebound; unrelated developer grants and artifact identifiers remain unchanged.
Previously returned export paths continue to refer to the retained original copy.
Legacy Downloads exports stay at their published paths. New exports live in this data root.
An existing installation keeps its active location until preferences are explicitly saved,
so unfinished historical jobs remain reachable after upgrading.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import stat
from contextlib import contextmanager
from pathlib import Path

from openreading.artifacts.intake import directory, source
from openreading.artifacts.limits import ArtifactError
from openreading.artifacts.store import safe_read

from runtime.app_settings import read_preferences, write_private
from runtime.configuration import client_root


def desired_root(client, *, home=None):
    return read_preferences(client, home=home).data_folder / "clients" / client / "v2"


def data_root(client, *, home=None):
    control = client_root(client, home=home)
    path = control / "storage.json"
    if path.exists() or path.is_symlink():
        try:
            value = json.loads(safe_read(path, 16384))
            if (
                not isinstance(value, dict)
                or set(value) != {"schema_version", "active_root"}
                or type(value["schema_version"]) is not int
                or value["schema_version"] != 1
                or not isinstance(value["active_root"], str)
            ):
                raise ValueError
            root = Path(value["active_root"])
            if not root.is_absolute() or ".." in root.parts or "\x00" in str(root):
                raise ValueError
            return root
        except (ValueError, OSError, ArtifactError):
            raise ValueError(
                "Cannot read the active data location. Restore the storage control record before continuing."
            ) from None
    legacy = control / "v2"
    return legacy if legacy.exists() else desired_root(client, home=home)


def copy_tree(old, new):
    """Copy regular files through checked descriptors; links never become retained inputs."""
    with directory(old):
        for entry in old.iterdir():
            info = entry.lstat()
            target = new / entry.name
            if stat.S_ISDIR(info.st_mode):
                target.mkdir(mode=0o700)
                copy_tree(entry, target)
            elif stat.S_ISREG(info.st_mode):
                with source(old, entry.name) as fd, os.fdopen(os.dup(fd), "rb") as reader:
                    with target.open("xb") as writer:
                        os.chmod(target, 0o600)
                        shutil.copyfileobj(reader, writer, 1024 * 1024)
                        writer.flush()
                        os.fsync(writer.fileno())
            else:
                raise ValueError("Data migration refuses symbolic links and special files.")


def grant_id(path):
    from openreading.artifacts.limits import ProfileConfig
    from openreading.artifacts.store import Store

    store = Store(ProfileConfig(path, path.parent.parent / "artifacts"))
    try:
        return store.grant
    finally:
        close = getattr(store, "close", None)
        if close:
            close()


def check_idle(root):
    # Previous builds did not hold our connection lock. Their private profiles remain live
    # until the parent closes its worker, so refuse migration while those profiles exist.
    if any((root / "launch").glob("*/profile.json")):
        raise ValueError("Close the existing OpenReading document connection before moving data.")
    for job in (root / "artifacts/jobs").glob("*/*"):
        value = json.loads(safe_read(job / "status.json", 65536))
        if not isinstance(value, dict) or value.get("state") not in {
            "succeeded",
            "failed",
            "cancelled",
        }:
            raise ValueError(
                "Finish or cancel existing imports before moving data. Keep the current data folder until they finish."
            )


def rebind_intake(old, new):
    original = old / "selection/ready"
    if not original.exists():
        return
    before, after = grant_id(original), grant_id(new / "selection/ready")
    for group in ("documents", "jobs"):
        source_group = new / "artifacts" / group / before
        if not source_group.exists():
            continue
        target_group = source_group.with_name(after)
        if target_group.exists():
            try:
                target_group.rmdir()
            except OSError:
                raise ValueError(
                    "The migrated intake conflicts with another retained grant."
                ) from None
        source_group.rename(target_group)
        for path in target_group.glob(
            "*/manifest.json" if group == "documents" else "*/request.json"
        ):
            value = json.loads(safe_read(path, 1024 * 1024))
            if group == "documents":
                if value.get("input_grant_sha256") != before:
                    raise ValueError("The retained document grant is inconsistent.")
                value["input_grant_sha256"] = after
            else:
                if value.get("grant") != before:
                    raise ValueError("The retained import grant is inconsistent.")
                value.update(
                    grant=after,
                    input_root=str(new / "selection/ready"),
                    artifact_root=str(new / "artifacts"),
                )
            write_private(path, value)


def migrate(old, new):
    if old == new:
        with directory(new, create=True):
            pass
        return
    if old in new.parents or new in old.parents:
        raise ValueError("Choose a data folder outside the current client partition.")
    if old.exists():
        check_idle(old)
    with directory(new.parent, create=True):
        try:
            new.mkdir(mode=0o700)
        except FileExistsError:
            raise ValueError(
                "That folder already contains an OpenReading client partition. Choose a fresh folder; stores are never merged."
            ) from None
    try:
        if old.exists():
            copy_tree(old, new)
            rebind_intake(old, new)
    except BaseException:
        shutil.rmtree(new)
        raise


@contextmanager
def storage_session(client, *, home=None):
    control = client_root(client, home=home)
    with directory(control, create=True) as parent:
        fd = os.open("storage.lock", os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR, 0o600, dir_fd=parent)
        try:
            old, new = data_root(client, home=home), desired_root(client, home=home)
            if not (control / "preferences.json").exists() and old.exists():
                new = old
            try:
                fcntl.flock(fd, (fcntl.LOCK_EX if old != new else fcntl.LOCK_SH) | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError(
                    "Close the other OpenReading document connection before applying this data-folder change."
                ) from None
            # Another launcher may have completed migration before this lock was acquired.
            old = data_root(client, home=home)
            if old != new:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise ValueError(
                        "Close the other OpenReading document connection before moving data."
                    ) from None
            migrate(old, new)
            try:
                write_private(
                    control / "storage.json", {"schema_version": 1, "active_root": str(new)}
                )
            except BaseException:
                if old != new and data_root(client, home=home) != new:
                    shutil.rmtree(new)
                raise
            fcntl.flock(fd, fcntl.LOCK_SH)
            yield new
        except (OSError, ArtifactError):
            raise ValueError(
                "Cannot switch the data folder. The previous copy remains intact; check permissions and free space."
            ) from None
        finally:
            os.close(fd)
