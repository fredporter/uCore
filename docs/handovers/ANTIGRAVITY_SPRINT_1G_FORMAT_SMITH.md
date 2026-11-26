# Sprint 1G · OK Assistant model selection and fallback

OK Assistant lists cloud models and sends a prompt to the selected provider only when the user selects it. A cloud failure before any output falls back to Ollama and displays that change. A failure after partial output preserves the draft. The uCode+ transport and its tests are merged. The live provider and delivery status are tracked on Cline Kanban card `80696`.

[Development board](http://127.0.0.1:3484/ucore)

The default cloud route is [OpenRouter Free Models](https://openrouter.ai/openrouter/free). If the provider is throttled or unavailable before sending output, OK Assistant switches to the configured local model. Use the [operator scenarios](ANTIGRAVITY_SPRINT_1F_FORMAT_SMITH.md) to verify both fallback and interrupted replies.
