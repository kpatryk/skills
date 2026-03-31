#!/usr/bin/env bash

set -euo pipefail

# Reusable local/CI entrypoint for Skill Scanner.
# Defaults are CI-safe and can be overridden via env vars.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${SKILLS_DIR:-$ROOT_DIR/skills}"
OUTPUT_FILE="${OUTPUT_FILE:-$ROOT_DIR/skill-scanner-results.sarif}"
POLICY="${POLICY:-balanced}"
FAIL_ON_SEVERITY="${FAIL_ON_SEVERITY:-high}"
RECURSIVE="${RECURSIVE:-true}"
CHECK_OVERLAP="${CHECK_OVERLAP:-true}"
USE_BEHAVIORAL="${USE_BEHAVIORAL:-false}"
LENIENT="${LENIENT:-false}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

if ! command -v skill-scanner >/dev/null 2>&1; then
  echo "skill-scanner is not installed. Install with:" >&2
  echo "  uv tool install cisco-ai-skill-scanner" >&2
  exit 127
fi

if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "Skills directory not found: $SKILLS_DIR" >&2
  exit 2
fi

cmd=(
  skill-scanner scan-all "$SKILLS_DIR"
  --format sarif
  --output "$OUTPUT_FILE"
  --policy "$POLICY"
  --fail-on-severity "$FAIL_ON_SEVERITY"
)

if [[ "$RECURSIVE" == "true" ]]; then
  cmd+=(--recursive)
fi

if [[ "$CHECK_OVERLAP" == "true" ]]; then
  cmd+=(--check-overlap)
fi

if [[ "$USE_BEHAVIORAL" == "true" ]]; then
  cmd+=(--use-behavioral)
fi

if [[ "$LENIENT" == "true" ]]; then
  cmd+=(--lenient)
fi

if [[ -n "$EXTRA_ARGS" ]]; then
  # EXTRA_ARGS supports simple space-separated flags only.
  read -r -a extra <<<"$EXTRA_ARGS"
  cmd+=("${extra[@]}")
fi

echo "Running: ${cmd[*]}"
"${cmd[@]}"

echo "Skill scan complete: $OUTPUT_FILE"
