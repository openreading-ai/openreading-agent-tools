"""Read historical probe schedules; API study preparation and finalization are disabled.

Old model/account/budget fields retain their historical meaning and authorize nothing.
Owner-operated Desktop testing does not use this retired provider execution workflow.
"""

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = [f"{name}-single_fact" for name in ("agreement", "manual", "report")]
# Mirrors probe-manifest.schema.json: exact family and version digits, never an alias.
MODEL_ID = re.compile(r"claude-(opus|sonnet|haiku|fable)-[0-9]+(-[0-9]+)*")


def schedule(seed=20260911):
    rows = []
    for task in TASKS:
        arms = ["A", "B", "C"]
        for index in (2, 1):
            seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
            other = int(seed / 2**32 * (index + 1))
            arms[index], arms[other] = arms[other], arms[index]
        rows.extend({"task_id": task, "repetition": 0, "arm": arm} for arm in arms)
    return rows


def prepare(output, evidence, python, client, assets, lock):
    """Refuse new API study drafts without touching the supplied paths."""
    raise ValueError("Provider API trials are disabled. Use the Desktop app for functional checks.")


def finalize(root, model, account, pricing):
    """Refuse finalization even when a historical draft and account approval exist."""
    raise ValueError("Provider API trials are disabled. Use the Desktop app for functional checks.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    for name in ("output", "evidence", "python", "client", "assets", "lock"):
        # Preserve the venv interpreter symlink: resolving it selects the base interpreter.
        prep.add_argument(f"--{name}", required=True, type=lambda p: Path(p).absolute())
    final = sub.add_parser("finalize")
    final.add_argument("root", type=Path)
    final.add_argument("--model", required=True)
    final.add_argument("--account", required=True)
    final.add_argument("--pricing", required=True, type=Path)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    print(prepare(**args) if command == "prepare" else finalize(**args))


if __name__ == "__main__":
    main()
