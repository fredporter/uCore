#!/usr/bin/env bash
set -euo pipefail

# Enforce planning governance:
# - Durable active planning belongs to uFlow, outside this repository.
# - Archived planning is allowed under docs/archive/plans/
# - Exception tag for temporary active task notes elsewhere:
#   - <!-- planning-governance: allow-active-tasks -->
# - Disallowed elsewhere: unchecked checklist tasks and task/backlog tables.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

allowed_file() {
  local path="$1"
  [[ "$path" == docs/archive/plans/* ]] && return 0
  [[ "$path" == docs/archive/* ]] && return 0
  [[ "$path" == docs/archived/* ]] && return 0
  [[ "$path" == docs/legacy/* ]] && return 0
  return 1
}

planning_candidate() {
  local path="$1"
  local base
  base="$(basename "$path")"

  [[ "$path" == docs/* ]] || return 1

  if [[ "$base" =~ (PLAN|TASK|SPRINT|TODO|CHECKLIST|HANDOVER|ROADMAP|PHASE) ]]; then
    return 0
  fi

  return 1
}

violations=0

while IFS= read -r file; do
  [[ -f "$file" ]] || continue
  if ! planning_candidate "$file"; then
    continue
  fi

  if allowed_file "$file"; then
    continue
  fi

  if grep -qiF '<!-- planning-governance: allow-active-tasks -->' "$file"; then
    echo "[ALLOW] Exception tag found in $file"
    continue
  fi

  found=0

  if grep -nE '^[[:space:]]*[-*][[:space:]]+\[[[:space:]]\][[:space:]]+' "$file" >/tmp/ucore_plan_check_1.txt 2>/dev/null; then
    if [[ -s /tmp/ucore_plan_check_1.txt ]]; then
      found=1
      echo "[FAIL] Unchecked task checklist found in $file"
      cat /tmp/ucore_plan_check_1.txt
    fi
  fi

  if grep -nE '^\|[[:space:]]*Task[[:space:]]*\|[[:space:]]*(Status|Priority)[[:space:]]*\|[[:space:]]*Description[[:space:]]*\|' "$file" >/tmp/ucore_plan_check_2.txt 2>/dev/null; then
    if [[ -s /tmp/ucore_plan_check_2.txt ]]; then
      found=1
      echo "[FAIL] Task table header found in $file"
      cat /tmp/ucore_plan_check_2.txt
    fi
  fi

  if [[ "$found" -eq 1 ]]; then
    violations=$((violations + 1))
  fi
done < <(git ls-files '*.md')

rm -f /tmp/ucore_plan_check_1.txt /tmp/ucore_plan_check_2.txt

if [[ "$violations" -gt 0 ]]; then
  echo "---"
  echo "Planning governance check failed in $violations file(s)."
  echo "Durable active tasks belong in uFlow; repository Markdown may contain only completed evidence or archived plans."
  exit 1
fi

echo "Planning governance check passed."
