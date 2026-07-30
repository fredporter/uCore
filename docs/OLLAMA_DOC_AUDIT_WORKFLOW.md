# Ollama Documentation Audit Workflow

## Purpose

Use local Ollama models to review planning and governance docs for drift,
without treating model output as final truth.

Model output is advisory only. CI and deterministic validators remain the gate.

## When To Run

- before closing each extraction wave
- after major handover or architecture doc edits
- when adding new governance docs

## Inputs

Primary docs:

- docs/EXTENSION_REGISTRY_SPEC.md
- docs/RELIABILITY_SINGLE_PATH_POLICY.md
- docs/handovers/CLINE_REPO_SPLIT_HANDOFF.md
- TODO.md

Optional docs for extended review:

- docs/CLINE_GITHUB_WORKFLOWS.md
- README.md

## Standard Command

```bash
cd /Users/fredbook/Code/uCore
bash scripts/run_ollama_doc_audit.sh
```

## Required Local Prerequisites

- Ollama installed and running
- A local model present, for example `qwen2.5-coder:3b`

## Review Contract

The audit should check for:

1. hard-cut ownership consistency (uFlow/uKnowledge required)
2. preflight stop-the-line semantics (`ready=false` / `412` block)
3. no fallback-to-core instructions in active split docs
4. evidence-first wave completion language
5. alignment between TODO and architecture docs

## Output

The script writes:

- tmp/doc_audit_report.md

Use this report as a checklist, then confirm with deterministic checks:

```bash
python3 scripts/validate_docs_nonregression.py
python3 scripts/validate_capability_requirements.py
```

## Safety Rule

Never merge based on LLM summary alone.
Only merge when deterministic checks and runtime proof pass.
