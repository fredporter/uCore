# Antigravity handover · Sprint 1A · Format Smith

**21 November 2026 · Perth**

## Coordinator prompt

> Read the workspace AGENTS.md and the Sprint 1A section of uCodePlus/docs/ASSISTANT_DELIVERY_SPRINTS.md. Record branch, commit and dirty state in each checkout you touch. First hand back browser evidence for the CI follow-up. In parallel, assign a runtime agent and a UI agent to deliver one complete Format Smith flow through existing OK Assistant. Agree on the invocation contract before the UI agent wires it in. Ask a separate verifier to test the integrated build in the host browser. Give each agent the relevant section below and its checkout path. Keep the CI follow-up and assistant changes in separate patches.

## Close the current UI review

| Item | Starting evidence |
| --- | --- |
| Merged monitoring baseline | PR #46, commit `144e1fa`. Default and working branch views were browser-checked. |
| Refresh recovery | Commit `141139a`, branch `sprint/github-actions-recovery`. The branch was pushed and Fred reported completing the PR step. Confirm the remote PR and merge state. |
| uFlow follow-up | Commit `caa3017`, branch `sprint/github-actions-follow-ups` in `~/Code/uCore-ci-recovery`. Last known local evidence is 14 targeted backend tests, 177 frontend tests and Vue type checking passed. |
| Existing localhost app | At last inspection, ports 5175 and 8484 served the older `~/Code/uCore` checkout. Codex could neither connect to localhost nor bind a review port. |

Run the review frontend and backend from the follow-up checkout on the Mac. An isolated workflow directory keeps test tasks out of the active Inbox. Use two Terminal tabs:

```bash
cd ~/Code/uCore-ci-recovery/backend
UFLOW_TASKS_DIR="$(mktemp -d)" ../../uCore/backend/.venv/bin/python \
  -m app.core.snackbar --host 127.0.0.1 --port 8584
```

```bash
cd ~/Code/uCore-ci-recovery/frontend-vue
[ -e node_modules ] || ln -s ../../uCore/frontend-vue/node_modules node_modules
VITE_PORT=5185 VITE_UCORE_URL=http://127.0.0.1:8584 npm run dev
```

Open [System → GitHub](http://localhost:5185/system?tab=github).

1. Refresh a populated branch view. Simulate a GitHub status failure in the review instance. Verify the last result, timestamp and run links stay visible with recovery guidance. Restore the response and verify the next refresh clears the warning.
2. In a failed run, select **Create follow-up**, then **Open uFlow task**. Verify the repo, branch, commit SHA and run link in the task.
3. Reload the panel and repeat for the same run. Capture the same task ID and one Inbox entry. If no suitable failed run is available, use a fixture for the run-list response and the real local task endpoint. Label the evidence accordingly.
4. Record branch, commit, URLs, screenshots and results. If review passes, confirm the recovery patch is on remote main before preparing the follow-up PR against main. If recovery was squash merged, check the proposed diff contains only follow-up changes.

## Build the first OK Assistant specialist

**Runtime agent prompt**

> Trace the existing OK Assistant request from the frontend to the Ollama transport. Start with `backend/app/services/provider_router.py`, local model discovery and capability readiness. Confirm which local Qwen model is installed with `ollama list`. Implement or configure the `format-smith` specialist through the existing model selection and invocation contract. Use the owning repository's model setup conventions. Format pasted notes as Markdown and preserve names, dates, amounts and uncertainty. Keep inference local and make missing models, timeout and invalid output actionable through the existing error path. Return the selected base tag, model setup, request and response contract, diff, and targeted tests.

**UI agent prompt**

> Start with `frontend-vue/src/skills/organisms/ChatBubblePanel.vue` and trace any shared OK Assistant state and rendering components. Make Format Smith discoverable through the existing local model or assistant selector. Let a user paste notes, send them, review rendered Markdown and recover from a failed attempt with their draft intact. Reuse existing USX controls and rendering. Use the runtime agent's agreed contract. Return changed files, component tests and exact browser steps.

**Verifier prompt**

> Run the integrated build on the Mac and record the serving checkout and commit. As a user, select Format Smith in OK Assistant and paste a short fixture with headings, bullet points, a date, an amount and an ambiguous note. Verify that the result renders as Markdown and retains the facts and ambiguity. With the base model already installed, verify inference with external network unavailable. Test missing model, timeout and invalid output with the original draft intact. Capture the UI at desktop and narrow widths and label live Ollama and mocked evidence.

## Sprint exit

- CI follow-up browser evidence and PR state are recorded.
- Format Smith can be selected, invoked and reviewed in OK Assistant. The verifier records source fidelity, rendered output, offline inference and recovery results.
- Each agent returns base and head commits or patch, changed files, exact test commands and any blockers. The coordinator returns a single status with links to evidence and outstanding checks.
- The remaining specialist roster and Concierge evaluation follow the Format Smith pilot. Keep uCode Assist, BBC BASIC qualification and OpenRouter budget work in their existing sprint lanes.
