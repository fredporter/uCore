# Sprint 1G – OK Assistant Model Selector & Routing Integration

**Date:** $(date +%Y-%m-%d)

## Goal
Connect the newly‑added `ucode_plus` OpenRouter client to OK Assistant:
1. Extend the model selector UI to list the OpenRouter models alongside local ones.
2. Route chat requests to the OpenRouter client when a cloud model is chosen.
3. Implement safe fallback to a local model on unrecoverable OpenRouter errors.
4. Add end‑to‑end verification (mocked during CI, live test with a real key).

## Owner
- **Fred Porter** (<fredporter@users.noreply.github.com>)

## Tasks
- [ ] **Branch creation** – `sprint/ok-assistant-openrouter-integration` from `main`.
- [ ] **Model selector UI** – modify the frontend Vue component that builds the model dropdown (likely `frontend-vue/src/components/ModelSelector.vue`). Add entries from `ucode_plus/ucode_plus.json` with a cloud icon and a tooltip showing provider.
- [ ] **Backend routing** – in the chat handling module (e.g., `frontend-vue/src/store/chat.ts` or the server‑side API), detect if the selected model ID exists in the OpenRouter list and call `ucode_plus/client.run_chat`.
- [ ] **Fallback logic** – reuse the `OpenRouterError` signal to trigger a local model fallback (configurable fallback model in the same JSON).
- [ ] **User notification** – surface a system message in the chat UI when a fallback occurs (e.g., *"OpenRouter model unavailable, switched to local model 'format‑smith‑lite'."*).
- [ ] **Live verification script** – small helper script (`scripts/verify_openrouter.py`) that reads the API key from the env, sends a short prompt to a test model, and prints the streamed result. Add it to CI as an optional step (run only when `OPENROUTER_API_KEY` secret is present).
- [ ] **Documentation** – extend `ucode_plus/README.md` with a section on how the OK Assistant integrates and how to enable/disable the cloud models via config.
- [ ] **CI updates** – add a job that runs the live verification script when a secret is provided; guard it with `if: env.OPENROUTER_API_KEY != ''`.
- [ ] **Open PR #54 merge** – once integration passes review, merge PR #54 to bring the client into `main`.
- [ ] **Open PR for integration** – open PR (e.g., `#55`) from the branch created in step 1 and request review.

## Verification (TODO)
- Run the live verification script with a real key.
- Manually select an OpenRouter model in the OK Assistant UI and confirm streamed response.
- Induce a 429 error (mock) and verify fallback to local model.
- CI passes on both mocked and live steps.

## References
- PR #54: https://github.com/fredporter/uCore/pull/54
- OpenRouter streaming docs: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request?explorer=true
- Existing model selector component location (search `ModelSelector` in `frontend-vue/src`).
