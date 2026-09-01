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

from ..services.budget_manager import BudgetManager
from ..services.provider_router import ProviderRouter

log = logging.getLogger("ucore.chat")

# Shared router instance
_router: ProviderRouter | None = None


def get_router() -> ProviderRouter:
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router


def _normalise_tool_calls(response: dict) -> list[dict]:
    """Accept native tool calls and the JSON fallback emitted by small models."""
    native = response.get("tool_calls")
    if isinstance(native, list) and native:
        return native

    content = response.get("content")
    if not isinstance(content, str):
        return []
    candidate = content.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            candidate = "\n".join(lines[1:-1]).strip()
            if candidate.lower().startswith("json\n"):
                candidate = candidate[5:].strip()
    try:
        payload = json.loads(candidate)
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []
    name = payload.get("name")
    arguments = payload.get("arguments", {})
    known_tools = {
        tool["function"]["name"] for tool in _CHAT_TOOLS
    }
    if name not in known_tools or not isinstance(arguments, (dict, str)):
        return []
    return [{"function": {"name": name, "arguments": arguments}}]


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
            "description": "List all vault types (User, Shared, Public) and their existence status. Use when the user asks about their vault structure or what vaults exist.",
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
    {
        "type": "function",
        "function": {
            "name": "scrape_web",
            "description": "Fetch and extract article content from a web URL. Use when the user asks to research a URL, fetch content from the web, or gather information from a website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to scrape (must start with http:// or https://)",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_vault",
            "description": "Save content to the user's personal vault (~/Vault/). Use when the user asks to save research, notes, summaries, or any content to their vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Document title (used as filename)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to save (markdown format)",
                    },
                    "folder": {
                        "type": "string",
                        "description": "Optional subfolder within ~/Vault/ (e.g. 'research', 'notes')",
                    },
                },
                "required": ["title", "content"],
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
            from ..knowledge.vault import semantic_search
            results = semantic_search(query, limit=5)
            return json.dumps({"query": query, "results": results, "count": len(results)})
        except ImportError:
            return json.dumps({
                "query": query,
                "results": [],
                "count": 0,
                "note": "Vault knowledge module not available",
            })

    if tool_name == "vault_topology":
        from pathlib import Path
        home = Path.home()
        layers = [
            {"id": "user", "label": "User Vault", "path": str(home / "Vault"),
             "exists": (home / "Vault").exists()},
            {"id": "shared", "label": "Shared Vaults", "path": str(home / "Shared"),
             "exists": (home / "Shared").exists()},
            {"id": "public", "label": "Public Vaults",
             "path": str(home / "Public"),
             "exists": (home / "Public").exists()},
        ]
        return json.dumps({"vault_layers": layers, "count": len(layers)})

    if tool_name == "workflow_tasks":
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
                {"id": "backup", "name": "Backup", "category": "maintenance"},
                {"id": "vault_discovery", "name": "Vault Discovery", "category": "knowledge"},
                {"id": "workflow_audit", "name": "Workflow Audit", "category": "workflow"},
            ], "total": 3, "source": "samples"})

    if tool_name == "system_health":
        return json.dumps({
            "ollama": {"status": "checking"},
            "backend": {"status": "online"},
            "mcp_gateway": {"mode": "external stdio client"},
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

    if tool_name == "scrape_web":
        url = arguments.get("url", "").strip()
        if not url or not url.startswith(("http://", "https://")):
            return json.dumps({"error": "Valid URL starting with http:// or https:// is required"})
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=15)
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; uCore-Scraper/1.0)",
                "Accept": "text/html,application/xhtml+xml",
            }
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as resp:
                    if not resp.ok:
                        return json.dumps({"error": f"HTTP {resp.status}", "url": url})
                    html = await resp.text(errors="replace")
            title = _html_title(html, url)
            description = _html_desc(html)
            text = _html_body_text(html)
            return json.dumps({
                "url": url, "title": title,
                "description": description,
                "text": text[:6000], "text_length": len(text),
            })
        except Exception as e:
            return json.dumps({"error": str(e), "url": url})


    if tool_name == "save_to_vault":
        from pathlib import Path
        title = arguments.get("title", "").strip()
        content = arguments.get("content", "").strip()
        folder = arguments.get("folder", "").strip()
        if not title or not content:
            return json.dumps({"error": "title and content are required"})
        vault_dir = Path.home() / "Vault"
        if folder:
            vault_dir = vault_dir / folder
        vault_dir.mkdir(parents=True, exist_ok=True)
        # Sanitize filename
        safe_name = "".join(c for c in title if c.isalnum() or c in " _-").strip()[:80]
        safe_name = safe_name.replace(" ", "-")
        if not safe_name:
            safe_name = "untitled"
        file_path = vault_dir / f"{safe_name}.md"
        timestamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
        full_content = f"# {title}\\n\\nsaved: {timestamp}\\n\\n{content}\\n"
        file_path.write_text(full_content, encoding="utf-8")
        return json.dumps({
            "saved": True,
            "title": title,
            "file": str(file_path),
            "vault_path": f"~/{file_path.relative_to(Path.home())}",
            "size": len(full_content),
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
    "• ~/Vault/ — User Vault (personal workspace: binders, missions, tasks, journals)\n"
    "• ~/Shared/ — Shared Vaults (team collaboration)\n"
    "• ~/Public/ — Public Vaults (reference, templates, knowledge bank)\n\n"
    "Note: ~/Code/ is NOT a vault — it is the Developer Lane for system development.\n\n"
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

_UCORE_ASK_PLAN_SYSTEM = (
    "You are a research and planning assistant for uCore, the local-first "
    "knowledge operating system. Your role is to RESEARCH and PLAN — never "
    "execute actions or modify files. "
    "\n\n"
    "## Your Capabilities\n"
    "- Research: Analyze vault documents, code repositories, and knowledge bases.\n"
    "- Plan: Produce structured, actionable plans with clear steps.\n"
    "- Synthesize: Combine information from multiple sources into coherent summaries.\n"
    "- Cite: Always reference your sources (vault paths, repo files, skill names).\n"
    "\n"
    "## Available Knowledge Sources\n"
    "### Document Vaults\n"
    "- ~/Vault/    — User personal vault (documents, notes, binders, journals)\n"
    "- ~/Shared/   — Team shared workspaces\n"
    "- ~/Public/   — Public reference, templates, global knowledge\n"
    "\n"
    "### Code Repositories\n"
    "- ~/Code/uCore/ — Core system (backend, frontend, MCP, skills, snacks)\n"
    "- ~/Code/uCode/ — Grid runtime, uCode BASIC, terminal, teletext\n"
    "- ~/Code/*/     — Extension and project repos\n"
    "\n"
    "### Available Skills & Tools\n"
    "- knowledge_search: Search vaults and knowledge base\n"
    "- vault_topology: List vault types and their status\n"
    "- workflow_tasks: List current tasks with status and priority\n"
    "- list_skills: List all available uCore skills\n"
    "- system_health: Check health of uCore services\n"
    "\n"
    "## Output Format (Plan Mode)\n"
    "When producing a plan, use this structure:\n"
    "```plan\n"
    "## Summary\\nBrief overview of the plan\\n\\n"
    "## Steps\\n"
    "- [ ] Step 1: Description (tool: tool_name)\\n"
    "- [ ] Step 2: Description (tool: tool_name)\\n"
    "## Sources\\n"
    "- Vault: ~/Vault/path/to/doc.md\\n"
    "- Repo: ~/Code/uCore/backend/app/...\\n"
    "## Notes\\nAdditional context or caveats\\n"
    "```\n"
    "\n"
    "## Rules\n"
    "1. NEVER execute actions or modify files.\n"
    "2. Always cite your sources with full paths.\n"
    "3. If you need more information, ask the user.\n"
    "4. Be specific and actionable in your plans.\n"
    "5. Stay within the user vault and knowledge scope."
)

_UCORE_ACT_SYSTEM = (
    "You are an action-oriented assistant for uCore. You can RESEARCH and "
    "EXECUTE safe operations within the user vault. "
    "\n\n"
    "## Your Capabilities\n"
    "- Research: Search vaults, repos, and knowledge bases.\n"
    "- Scrape: Fetch and extract content from web URLs.\n"
    "- Summarize: Create concise summaries of documents or scraped content.\n"
    "- Save to Vault: Write research results, summaries, and documents to ~/Vault/.\n"
    "- Plan: Create structured plans before acting.\n"
    "\n"
    "## Safety Rules\n"
    "1. Only write within ~/Vault/ (personal vault).\n"
    "2. Never modify code repositories unless explicitly instructed.\n"
    "3. Always confirm with the user before executing any action.\n"
    "4. Report what you did and where you saved results.\n"
    "5. All web scraping is read-only.\n"
    "\n"
    "## Available Tools\n"
    "Use the function calling interface to:\n"
    "- knowledge_search(query): Search vaults for documents\n"
    "- vault_topology(): List all vault types\n"
    "- list_skills(): List available skills\n"
    "- workflow_tasks(scope): List user tasks\n"
    "- system_health(): Check service health"
)



# ─── Handlers ────────────────────────────────────────────────────────


def _html_title(html: str, url: str) -> str:
    """Extract title from HTML using simple string operations."""
    # Try og:title meta tag
    for line in html.split(">"):
        if "og:title" in line and "content=" in line:
            start = line.find("content=") + 9
            end_char = line[start - 1:start] if start > 0 else ""
            end = line.find(end_char, start) if end_char else -1
            if end > start:
                return line[start:end].strip()
            return line[start:].split("<")[0].strip()
    # Fallback to <title> tag
    lower = html.lower()
    ti = lower.find("<title")
    if ti >= 0:
        end_tag = lower.find(">", ti)
        close = lower.find("</title>", end_tag)
        if end_tag >= 0 and close > end_tag:
            return html[end_tag + 1:close].strip()
    return url

def _html_desc(html: str) -> str:
    """Extract meta description from HTML using simple string operations."""
    for line in html.split(">"):
        if "og:description" in line and "content=" in line:
            start = line.find("content=") + 9
            end_char = line[start - 1:start] if start > 0 else ""
            end = line.find(end_char, start) if end_char else -1
            if end > start:
                return line[start:end].strip()
            return line[start:].split("<")[0].strip()
    # Try name="description"
    for line in html.split(">"):
        if "name=" in line and "description" in line and "content=" in line:
            start = line.find("content=") + 9
            end_char = line[start - 1:start] if start > 0 else ""
            end = line.find(end_char, start) if end_char else -1
            if end > start:
                return line[start:end].strip()
            return line[start:].split("<")[0].strip()
    return ""

def _html_body_text(html: str) -> str:
    """Extract readable text from HTML body using simple string operations."""
    # Remove script/style/nav/header/footer/aside sections
    import re
    raw = re.sub(r"<(script|style|nav|header|footer|aside)[^>]*>.*?</(script|style|nav|header|footer|aside)>",
                 " ", html, flags=re.I | re.S)
    # Strip all tags
    text = re.sub(r"<[^>]+>", " ", raw)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:6000]

def _select_system_prompt(mode: str) -> str:
    """Select the appropriate system prompt based on chat mode."""
    if mode == "plan":
        return _UCORE_ASK_PLAN_SYSTEM
    if mode == "act":
        return _UCORE_ACT_SYSTEM
    if mode == "workflow":
        return _UCORE_WORKFLOW_SYSTEM
    return _UCORE_CHAT_SYSTEM


def _check_budget_for_mode(mode: str) -> tuple:
    """Check if budget allows this mode. Returns (allowed, reason)."""
    if mode not in ("plan", "act"):
        return True, ""
    try:
        bm = BudgetManager.get()
        est_cost = 0.001 if mode == "plan" else 0.01
        allowed = bm.can_spend("docgen", estimated_cost=est_cost)
        if not allowed:
            reason = "Daily budget exhausted. Switching to Ollama (free)."
            return False, reason
        return True, ""
    except Exception:
        return True, ""


def _parse_plan_steps(response_text: str) -> list[dict] | None:
    """Parse structured plan steps from LLM output.
    Looks for ```plan code blocks or markdown checklists."""
    import re
    steps = []
    plan_match = re.search(r"```plan\n(.*?)```", response_text, re.DOTALL)
    if plan_match:
        plan_text = plan_match.group(1)
        for line in plan_text.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]"):
                step_text = line[5:].strip()
                tool_match = re.search(r"\(tool:\s*(\w+)\)", step_text)
                tool = tool_match.group(1) if tool_match else None
                if tool_match:
                    step_text = re.sub(r"\s*\(tool:\s*\w+\)", "", step_text).strip()
                steps.append({
                    "description": step_text, "tool": tool,
                    "done": line.startswith("- [x]"),
                })
    if not steps:
        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]"):
                steps.append({
                    "description": line[5:].strip(),
                    "tool": None,
                    "done": line.startswith("- [x]"),
                })
    return steps if steps else None



async def handle_chat(request: web.Request) -> web.Response:
    """POST /api/chat — chat completion with mode-aware routing.

    Body: { "message": "...", "mode": "chat|plan|act|workflow", "model": "..." }
    Modes:
      chat     — Quick chat, Ollama local default
      plan     — Research and planning, OpenRouter free tier, no execution
      act      — Research + execute safe vault operations (scrape, save)
      workflow — Task-focused chat with system context
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

        # Budget check for plan/act modes
        budget_ok = True
        budget_warning = None
        if mode in ("plan", "act"):
            budget_ok, budget_warning = _check_budget_for_mode(mode)

        # Plan mode: direct response, no tool loop
        if mode == "plan":
            system_prompt = _UCORE_ASK_PLAN_SYSTEM
            if not budget_ok and not model:
                model = "ollama/qwen2.5-coder:3b"
            if not model:
                model = "cognitivecomputations/dolphin-mixtral-8x7b"
            try:
                plan_messages: list[dict] = [
                    {"role": "system", "content": system_prompt},
                ]
                plan_messages.extend(history)
                plan_messages.append({"role": "user", "content": message})
                plan_response = await router.chat(
                    messages=plan_messages, model=model,
                    temperature=0.3,
                )
                response_text = plan_response.get("content", "")
                plan_steps = _parse_plan_steps(response_text)
                return web.json_response({
                    "response": response_text,
                    "mode": mode,
                    "model": plan_response.get("model", model),
                    "usage": plan_response.get("usage", {}),
                    "plan_steps": plan_steps,
                    "budget": {
                        "ok": budget_ok,
                        "warning": budget_warning,
                    },
                })
            except Exception as e:
                log.error("Plan mode error: %s", e, exc_info=True)
                return web.json_response({
                    "error": str(e),
                    "message": "Plan request failed. Is OpenRouter API key configured?",
                }, status=500)

        system_prompt = _select_system_prompt(mode)
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

            tool_calls = _normalise_tool_calls(response)
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


async def handle_chat_modes(request: web.Request) -> web.Response:
    """GET /api/chat/modes — return available chat modes and budget status."""
    budget_status = {"ok": True, "daily_remaining": None, "warning": None}
    try:
        bm = BudgetManager.get()
        status = bm.get_status()
        budget_status["daily_remaining"] = status.get("daily_remaining", 0)
        budget_status["ok"] = (
            budget_status["daily_remaining"] is not None
            and budget_status["daily_remaining"] > 0.001
        )
        budget_status["circuit_breaker"] = status.get("circuit_breaker", False)
    except Exception:
        pass

    return web.json_response({
        "modes": [
            {
                "id": "chat",
                "label": "Chat",
                "icon": "chat",
                "description": "Quick chat with your assistant. Uses local Ollama by default.",
                "cost": "free",
                "available": True,
            },
            {
                "id": "plan",
                "label": "Plan",
                "icon": "psychology",
                "description": "Research and plan using vaults, repos, and OpenRouter free models.",
                "cost": "free",
                "available": True,
                "models": [
                    "cognitivecomputations/dolphin-mixtral-8x7b",
                    "microsoft/phi-3-medium-128k-instruct",
                ],
            },
            {
                "id": "act",
                "label": "Act",
                "icon": "play_arrow",
                "description": "Execute safe vault operations (scrape, summarize, save to vault).",
                "cost": "budget",
                "available": budget_status["ok"],
                "budget_required": True,
            },
        ],
        "budget": budget_status,
    })


async def handle_models(request: web.Request) -> web.Response:
    """GET /api/models — list available AI models."""
    try:
        router = get_router()
        providers = router.list_providers() if hasattr(router, "list_providers") else []

        if not providers:
            providers = [
                {"id": "ollama", "name": "Ollama (local)", "models": [
                    "llama3.2", "mistral", "qwen2.5-coder:3b"]},
            ]

        return web.json_response({"providers": providers, "count": len(providers)})
    except Exception as e:
        log.error("Models error: %s", e)
        return web.json_response({"providers": [], "count": 0, "error": str(e)})
