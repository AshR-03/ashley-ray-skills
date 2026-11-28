#!/usr/bin/env bash
# Seed the workspace with a brainstorm in progress.
set -euo pipefail
mkdir -p docs/brainstorm
cp "$(dirname "$0")/../fixtures/complete.json" docs/brainstorm/graph.json
