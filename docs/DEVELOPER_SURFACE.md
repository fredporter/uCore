# Developer Surface — uCore

The Developer Surface is the in-core surface for browsing and editing code
repositories. It runs at `http://localhost:5175/developer`.

## What it is

`/developer` is a three-tab repo browser:

| Tab | Purpose |
|-----|---------|
| Code | Repo cards grouped by lane (Code / Extensions / Projects) |
| Repository | File tree + read-only preview for a selected repo |
| Editor | Full editor with save for the selected file |

It is backed by the `/api/developer/repos/*` endpoints (list repos, list
files, preview, save, diff, review, stage, unstage, commit).

## Where everything else lives

The Developer Surface is intentionally minimal. Operational panels were folded
into two other surfaces:

| Concern | Surface | Route |
|---------|---------|-------|
| Chat / Ask / Plan / Act | Intelligence | `/intelligence` |
| Models, Agents, Budget, History | Intelligence | `/intelligence` |
| Services, Feeds, Skills, Snacks, Extensions, Logs, MCP | Snackbar | `/snackbar` |
| Workflow / Missions / Tasks / Editor | Workflow | `/workflow` |

## Lane separation

The Developer Surface is for system development only — code under `~/Code/*`.
User content (vaults, binders, documents, uCode BASIC) belongs in the User
Lane (Intelligence, Workflow, Vault tabs), never in the Developer Surface.

See `VAULT_BINDER_WORKFLOW_INTEGRATION.md` for the full boundary rules.

## API reference

| Endpoint | Purpose |
|----------|---------|
| `GET /api/developer/repos` | List repos under `~/Code` |
| `GET /api/developer/repos/{repo}/files` | List files in a repo |
| `GET /api/developer/repos/{repo}/file-preview?path=...` | Read a file |
| `PUT /api/developer/repos/{repo}/file-preview?path=...` | Save a file |
| `GET /api/developer/repos/{repo}/diff?path=...` | View a diff |
| `GET /api/developer/repos/{repo}/review` | Review working-tree changes |
| `GET /api/developer/repos/{repo}/status` | Staged/unstaged status |
| `POST /api/developer/repos/{repo}/stage` / `/unstage` / `/commit` | Git ops |
| `GET /api/server/agents` | Agents (Agents tab) |
| `GET /api/server/models` | Models (Models tab) |
| `GET /api/skills` | Full skill registry (Skills tab) |
| `GET /api/executables` | Skills + snacks combined |
