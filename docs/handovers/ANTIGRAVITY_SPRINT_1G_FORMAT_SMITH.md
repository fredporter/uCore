# Sprint 1G · OK Assistant model selection and fallback

OK Assistant lists cloud models and sends a prompt to the selected provider only when the user selects it. A cloud failure before any output falls back to Ollama and displays that change. A failure after partial output preserves the draft. The uCode+ transport and its tests are merged. The live provider and delivery status are tracked on Cline Kanban card `80696`.

[Development board](http://127.0.0.1:3484/ucore)
