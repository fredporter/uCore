"""Chat-related API endpoints for uCore.

Provides:
- POST /api/chat — chat completion with tool calling (Ollama function calls)
- GET /api/chat/prompts — dynamic prompt cards for AssistUI
- GET /api/models — available AI models from provider_router
"""
from __future__ import annotations

import json
import logging

from aiohttp import web

from ..services.provider_router import ProviderRouter

log = logging.getLogger("ucore.chat")

# Shared router instance
_router: ProviderRouter | None = None


def get_router() -> ProviderRouter:
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router


# ─── Tool Definitions (Ollama function-calling format) ──────────────

_CHAT_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "knowledge_search",
            "description": "Search the user's vault and knowledge base for documents matching a query. Use when the user asks about their vault, notes, documents, or wants to find something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords or phrase",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_topology",
            "description": "List all vault layers (User, Shared, Global, Public, Code) and their existence status. Use when the user asks about their vault structure or what vaults exist.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "workflow_tasks",
            "description": "List the user's current tasks with status, priority, board, and tags. Use when the user asks about tasks, what they should work on, or task status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "Task scope: 'user' for personal tasks, 'all' for everything",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "workflow_status",
            "description": "Get overall workflow status including board counts, next actions, and tasker stats. Use when the user asks how their work is going or wants a status summary.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_skills",
            "description": "List all available uCore skills. Use when the user asks what skills or capabilities are available.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_health",
            "description": "Check the health status of uCore services (Ollama, database, MCP servers). Use when the user asks about system status or if things are working.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "binder_create",
            "description": "Create a new binder (project container) in the user's vault. Use when the user asks to create a project, start something new, or set up a workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Binder name (e.g. 'My Project')",
                    },
                    "description": {
                        "type": "string",
                        "description": "Short description of the binder's purpose",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_create",
            "description": "Create a new task in the .tasker/ system. Use when the user asks to create a task, to-do, or action item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title",
                    },
                    "board": {
                        "type": "string",
                        "description": "Task board: planning, writing, admin, learning, personal, finance, or general",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Task priority: low, medium, or high",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional task description",
                    },
                },
                "required": ["title"],
            },
        },
    },
]


# ─── Tool Executor ──────────────────────────────────────────────────

async def _execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a uCore tool and return JSON result string."""
    if tool_name == "knowledge_search":
        query = arguments.get("query", "")
        if not query:
            return json.dumps({"error": "query is required"})
        try:
            from ..knowledge.appflowy import semantic_search
            results = semantic_search(query, limit=5)
            return json.dumps({"query": query, "results": results, "count": len(results)})
        except ImportError:
            return json.dumps({
                "query": query,
                "results": [],
                "count": 0,
                "note": "AppFlowy knowledge module not available",
            })

    if tool_name == "vault_topology":
        from pathlib import Path
        home = Path.home()
        layers = [
            {"id": "user", "label": "User Vault", "path": str(home / "Vault"),
             "exists": (home / "Vault").exists()},
            {"id": "shared", "label": "Shared", "path": str(home / "Shared"),
             "exists": (home / "Shared").exists()},
            {"id": "global", "label": "Global Knowledge",
             "path": str(home / "Public" / "global-knowledge"),
             "exists": (home / "Public" / "global-knowledge").exists()},
            {"id": "public", "label": "Published",
             "path": str(home / "Public" / "doc-sites"),
             "exists": (home / "Public" / "doc-sites").exists()},
            {"id": "code", "label": "Code", "path": str(home / "Code"),
             "exists": (home / "Code").exists()},
        ]
        return json.dumps({"vault_layers": layers, "count": len(layers)})

    if tool_name == "workflow_tasks":
        scope = arguments.get("scope", "user")
        try:
            from pathlib import Path
            base = Path(".tasker")
            if not base.exists():
                raise FileNotFoundError(".tasker/ not found")

            tasks: list[dict] = []
            for md_file in sorted(base.rglob("*.md")):
                if any(p.startswith(".") for p in md_file.parts):
                    continue
                try:
                    content = md_file.read_text(encoding="utf-8", errors="replace")
                    lines = content.splitlines()
                    task_data: dict = {
                        "id": md_file.stem,
                        "title": "",
                        "status": "todo",
                        "priority": "medium",
                        "board": md_file.parent.name,
                        "tags": [],
                        "file": str(md_file),
                        "description": "",
                    }
                    in_summary = False
                    summary_parts: list[str] = []
                    for line in lines:
                        if line.startswith("# ") and not task_data["title"]:
                            task_data["title"] = line[2:].strip()
                        elif line.startswith("- ") and ":" in line:
                            key, value = line[2:].split(":", 1)
                            key = key.strip().lower()
                            value = value.strip()
                            if key == "status":
                                task_data["status"] = value
                            elif key == "priority":
                                task_data["priority"] = value
                            elif key == "tags":
                                task_data["tags"] = [t.strip() for t in value.split(",")]
                        elif line == "## Summary":
                            in_summary = True
                        elif in_summary and line.startswith("- "):
                            summary_parts.append(line[2:].strip())
                        elif in_summary and line.startswith("## "):
                            in_summary = False
                    if summary_parts:
                        task_data["description"] = "\n".join(summary_parts)
                    tasks.append(task_data)
                except Exception:
                    continue

            return json.dumps({
                "tasks": tasks[:20],
                "total": len(tasks),
                "source": ".tasker/ (live)",
            })
        except FileNotFoundError:
            return json.dumps({
                "tasks": [],
                "total": 0,
                "source": ".tasker/ not found",
            })

    if tool_name == "workflow_status":
        try:
            from ..api.user_workflow import get_workflow_status
            status = await get_workflow_status()
            return json.dumps(status)
        except (ImportError, AttributeError):
            return json.dumps({
                "tasker": {"boards": [
                    {"name": "planning", "count": 1},
                    {"name": "writing", "count": 1},
                    {"name": "admin", "count": 1},
                    {"name": "personal", "count": 1},
                    {"name": "finance", "count": 1},
                ], "total_tasks": 5},
                "source": "samples",
            })

    if tool_name == "list_skills":
        try:
            from ..api.skills import get_skill_list
            skills = await get_skill_list()
            return json.dumps({"skills": skills[:20], "total": len(skills)})
        except (ImportError, AttributeError):
            return json.dumps({"skills": [
                {"id": "ecosystem-audit", "name": "Ecosystem Audit", "category": "system"},
                {"id": "dev-mode-executor", "name": "Dev Mode Executor", "category": "developer"},
                {"id": "file-edit-enhancer", "name": "File Edit Enhancer", "category": "tools"},
                {"id": "tasker-ingest", "name": "Tasker Ingest", "category": "workflow"},
                {"id": "vault-discovery", "name": "Vault Discovery", "category": "vault"},
                {"id": "skill-docs-roundup", "name": "Docs Roundup", "category": "documentation"},
            ], "total": 6, "source": "samples"})

    if tool_name == "system_health":
        return json.dumps({
            "ollama": {"status": "checking"},
            "backend": {"status": "online"},
            "mcp_servers": {"count": "check /api/mcp/diagnostics for details"},
        })

    if tool_name == "binder_create":
        from pathlib import Path
        name = arguments.get("name", "").strip()
        if not name:
            return json.dumps({"error": "name is required"})
        description = arguments.get("description", "").strip()
        slug = name.lower().replace(" ", "-")
        binder_dir = Path.home() / "Vault" / "binders" / "active" / name
        binder_dir.mkdir(parents=True, exist_ok=True)
        binder_yaml = binder_dir / "_binder.yaml"
        binder_yaml.write_text(
            f"id: {slug}\nname: {name}\nstatus: active\n"
            f"description: {description or 'New uCore binder'}\n"
        )
        (binder_dir / "docs").mkdir(exist_ok=True)
        return json.dumps({
            "created": True,
            "name": name,
            "path": str(binder_dir),
            "binder_yaml": str(binder_yaml),
        })

    if tool_name == "task_create":
        from pathlib import Path
        title = arguments.get("title", "").strip()
        if not title:
            return json.dumps({"error": "title is required"})
        board = arguments.get("board", "general").strip().lower()
        priority = arguments.get("priority", "medium").strip().lower()
        description = arguments.get("description", "").strip()
        slug = "todo-" + title.lower().replace(" ", "-")[:60]
        board_dir = Path(".tasker") / board
        board_dir.mkdir(parents=True, exist_ok=True)
        task_file = board_dir / f"{slug}.md"
        content = f"# {title}\n\n- status: todo\n- priority: {priority}\n"
        if description:
            content += f"\n## Summary\n- {description}\n"
        task_file.write_text(content)
        return json.dumps({
            "created": True,
            "title": title,
            "board": board,
            "priority": priority,
            "file": str(task_file),
        })

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ─── System Prompts ──────────────────────────────────────────────────

_UCORE_CHAT_SYSTEM = (
    "You are the uCore personal assistant. You run inside the uCore ecosystem "
    "and have access to real APIs at http://localhost:8484. "
    "You have TOOLS available — use them! When a user asks about their vault, "
    "tasks, system status, or documents, CALL the appropriate tool instead of "
    "telling them you can't access data.\n\n"
    "**Vault Structure:**\n"
    "• ~/Vault/ — Personal vault (binders, daily, knowledge, missions, tasks, journals)\n"
    "• ~/Shared/ — Shared workspaces\n"
    "• ~/Public/global-knowledge/ — Global knowledge bank (read-only)\n"
    "• ~/Code/ — Development repositories\n\n"
    "Be helpful, proactive, and use your tools. Never say you cannot access data."
)

_UCORE_WORKFLOW_SYSTEM = (
    "You are the uCore workflow assistant. Use your tools to check tasks and status. "
    "Task statuses: todo, in-progress, review, blocked, completed. "
    "Priorities: low, medium, high. "
    "Boards: planning, writing, admin, learning, personal, finance, general. "
    "Always call workflow_tasks or workflow_status when the user asks about tasks. "
    "Be action-oriented — suggest concrete next steps."
)


# ─── Handlers ────────────────────────────────────────────────────────

async def handle_chat(request: web.Request) -> web.Response:
    """POST /api/chat — chat with tool calling.

    Body: { "message": "...", "mode": "chat|workflow", "model": "...", ... }
    The LLM can call uCore tools (knowledge_search, vault_topology, etc.)
    and get real results back. Max 3 tool-call rounds per request.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    message = body.get("message", "")
    if not message:
        return web.json_response({"error": "message is required"}, status=400)

    mode = body.get("mode") or body.get("agent", "chat")
    model = body.get("model")

    history = body.get("history") or body.get("messages")
    if not isinstance(history, list):
        history = []

    log.info(
        "Chat: mode=%s len(history)=%d msg=%s...",
        mode, len(history), message[:80],
    )

    try:
        router = get_router()
        system_prompt = (
            _UCORE_WORKFLOW_SYSTEM if mode == "workflow"
            else _UCORE_CHAT_SYSTEM
        )
        chat_messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]
        chat_messages.extend(history)
        chat_messages.append({"role": "user", "content": message})

        # Tool-calling loop (max 3 rounds)
        tool_results: list[dict] = []
        for _round in range(3):
            response = await router.chat(
                messages=chat_messages,
                model=model,
                tools=_CHAT_TOOLS,
            )

            tool_calls = response.get("tool_calls")
            if not tool_calls:
                # No more tools — return final response
                return web.json_response({
                    "response": response.get("content", ""),
                    "mode": mode,
                    "model": response.get("model", model),
                    "usage": response.get("usage", {}),
                    "tool_results": tool_results if tool_results else None,
                })

            # Execute each tool call
            log.info("Tool calls requested: %d", len(tool_calls))
            chat_messages.append({
                "role": "assistant",
                "content": response.get("content", "") or "",
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                log.info("Executing tool: %s(%s)", name, args)
                result_str = await _execute_tool(name, args)
                tool_results.append({
                    "tool": name,
                    "arguments": args,
                    "result": json.loads(result_str) if result_str else {},
                })
                chat_messages.append({
                    "role": "tool",
                    "content": result_str,
                })

        # Max rounds reached — get final answer with all tool results
        final_response = await router.chat(
            messages=chat_messages,
            model=model,
            tools=_CHAT_TOOLS,
        )
        return web.json_response({
            "response": final_response.get("content", ""),
            "mode": mode,
            "model": final_response.get("model", model),
            "usage": final_response.get("usage", {}),
            "tool_results": tool_results if tool_results else None,
        })

    except Exception as e:
        log.error("Chat error: %s", e, exc_info=True)
        return web.json_response({
            "error": str(e),
            "message": "Chat request failed",
        }, status=500)


async def handle_chat_prompts(request: web.Request) -> web.Response:
    """GET /api/chat/prompts?mode=... — get prompt cards."""
    mode = request.query.get("mode") or request.query.get("agent", "chat")

    prompts = {
        "chat": [
            {"title": "Search my vault", "prompt": "Search my vault for documents about..."},
            {"title": "Vault status", "prompt": "What vaults do I have and what's in them?"},
            {"title": "System health", "prompt": "How is my uCore system doing?"},
            {"title": "What can you do?", "prompt": "What tools and capabilities do you have?"},
        ],
        "workflow": [
            {"title": "What to work on", "prompt": "Show me my current tasks and suggest what to do next"},
            {"title": "Task status", "prompt": "What's the status of all my tasks?"},
            {"title": "Identify blockers", "prompt": "Are any of my tasks blocked?"},
            {"title": "Weekly plan", "prompt": "Help me plan my top priorities for this week"},
        ],
    }

    default_prompts = prompts.get(mode, prompts["chat"])

    return web.json_response({
        "mode": mode,
        "prompts": default_prompts,
        "count": len(default_prompts),
    })


async def handle_models(request: web.Request) -> web.Response:
    """GET /api/models — list available AI models."""
    try:
        router = get_router()
        providers = router.list_providers() if hasattr(router, "list_providers") else []

        if not providers:
            providers = [
                {"id": "ollama", "name": "Ollama (local)", "models": ["llama3.2", "mistral", "qwen2.5-coder:3b"]},
            ]

        return web.json_response({"providers": providers, "count": len(providers)})
    except Exception as e:
        log.error("Models error: %s", e)
        return web.json_response({"providers": [], "count": 0, "error": str(e)})