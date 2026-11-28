#!/usr/bin/env bash
# Run the eval suite in evals/ on your claude.ai plan's usage limits.
#
# Cases use read-only tools (Read, Glob, Grep, Skill), so no OS sandbox is
# needed. Each case runs with and without the skill so the score difference
# shows what the skill adds. Extra arguments go to `claude plugin eval`, e.g.
#   tools/run_evals.sh --case not-done-yet --runs 1 --model sonnet
# --case takes one glob (a second --case replaces the first), e.g. "trigger-*".
# MAX_COST_USD (default 5) caps the estimated spend at list prices.
set -euo pipefail

if [[ -n "${ANTHROPIC_API_KEY:-}${ANTHROPIC_AUTH_TOKEN:-}" ]]; then
  echo "An Anthropic API credential is set, so this run would be billed to the API." >&2
  echo "Unset ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN to use your claude.ai usage limits." >&2
  exit 1
fi

# Drop PATH entries the CLI can't read, such as Windows drives under WSL.
clean=""
IFS=: read -ra dirs <<<"$PATH"
for dir in "${dirs[@]}"; do
  [[ "$dir" == /mnt/* || ! -r "$dir" || ! -x "$dir" ]] && continue
  clean="${clean:+$clean:}$dir"
done
export PATH="$clean"

cd "$(dirname "$0")/.."
exec claude plugin eval . --trust-plugin --scaffold --no-publish \
  --max-cost-usd "${MAX_COST_USD:-5}" "$@"
