#!/bin/sh
set -eu
plugin=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HOME"
exec "$plugin/runtime/openreading-worker" --client codex --connector "$@"
