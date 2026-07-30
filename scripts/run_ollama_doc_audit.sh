#!/usr/bin/env bash
set -euo pipefail

MODEL="${OLLAMA_MODEL:-qwen2.5-coder:3b}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/tmp"
OUT_FILE="$OUT_DIR/doc_audit_report.md"

mkdir -p "$OUT_DIR"

DOCS=(
  "$ROOT/docs/EXTENSION_REGISTRY_SPEC.md"
  "$ROOT/docs/RELIABILITY_SINGLE_PATH_POLICY.md"
  "$ROOT/docs/handovers/CLINE_REPO_SPLIT_HANDOFF.md"
  "$ROOT/TODO.md"
)

if ! command -v ollama >/dev/null 2>&1; then
  echo "[FAIL] ollama is not installed or not in PATH"
  exit 1
fi

{
  cat <<'EOF'
You are auditing repository governance docs for consistency and anti-regression.
Return strict markdown with these sections:

1) Findings (severity ordered)
2) Conflicts Between Docs
3) Missing Controls
4) Suggested Edits (exact target file + bullet)
5) Pass/Fail Recommendation

Rules:
- Focus on hard-cut ownership, preflight stop-the-line, and evidence gates.
- Flag any fallback-to-core language in active split docs.
- Do not invent files.
EOF
  echo
  echo "Repository docs to audit:"
  for f in "${DOCS[@]}"; do
    echo "--- FILE: $f ---"
    cat "$f"
    echo
  done
} | ollama run "$MODEL" \
  | perl -pe 's/\x1b\[[0-9;]*[A-Za-z]//g; s/\x08//g' \
  > "$OUT_FILE"

echo "Doc audit written to: $OUT_FILE"
