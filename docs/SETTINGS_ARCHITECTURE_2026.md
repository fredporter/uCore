# Settings Architecture 2026

## Overview

The settings system has three tiers of configuration, each backed by different persistence:

1. **System Surface — Global & User Settings** (system administration)
2. **System Surface — Variables & Secrets** (data layer)
3. **Developer Surface — Developer Settings** (USX, GridCore, uSystem)

## Layer 1: Global & User Settings (System Surface)

**Location**: `http://localhost:5175/system?tab=global-settings` and `?tab=user-settings`

**Component**: `frontend-vue/src/surfaces/system/SystemSurface.vue`

**Backend**: `backend/app/surfaces/system_api.py`
- `GET /api/system/settings` — load all settings scopes
- `POST /api/system/settings` — update a scope (`{scope: "global", values: {...}}`)

### Global Settings
```typescript
interface GlobalSettings {
  theme: 'dark' | 'light' | 'auto'
  fontSize: number         // 12-24 (px)
  palette: 'default' | 'ocean' | 'forest' | 'sunset'
}
```

### User Settings
```typescript
interface UserSettings {
  displayName: string
  email: string
  defaultModel: 'Llama 3.2' | 'GPT-4o' | 'DeepSeek V3'
}
```

**Persistence**: Server-side in `~/.ucore/data/system_settings.json`. localStorage cache kept as fallback via `watch()` auto-write (keys: `ucore-theme-settings`, `ucore-user-settings`).

**Save behavior**: Explicit Save button per settings panel → POST to `/api/system/settings`.

---

## Layer 2: Variables & Secrets (System Surface)

### Variables
**Backend**: `backend/app/api/variables_api.py`
- `GET /api/variables` — user + installation variables
- `GET /api/variables/user` — user-scoped only
- `PUT /api/variables/user` — update user variables
- `GET /api/variables/install` — installation metadata (read-only)

The [system variable registry](../backend/app/core/vars.def) contains 114 entries
derived from the seed sheet. Each tab-separated record holds a dollar-prefixed
name, a type, a default field, and a domain. The bare ID must match
`[A-Z][A-Z0-9]{2,7}`. The loader rejects invalid names and duplicates.
IDs have 3–8 characters and start with a letter. `$SYSBOOT` identifies the boot timestamp,
and `$SYSBOOTS` identifies the boot source.

- User-editable domains cover profile, contact, organization, address, and scratch
  fields. The API uses string values, with an empty string for an unset scratch
  slot. Registry types describe the intended data. The default column is empty
  and the runtime computes installation and local defaults.
- `$USERID` and `$INSTALLD` are managed fields. `$ROLE` is a profile value.
  Authoritative identity, roles, and publishing capabilities come from the identity
  service. The system, workflow, BASIC, page, and internal domains reserve IDs
  for their owning runtimes.
- Legacy profile keys and padded spellings are accepted as compatibility aliases
  where editable and returned alongside canonical values. A successful write
  migrates recognized aliases to canonical keys. The existing settings keys
  `model_routing`, `local_model`, and `openrouter_model` use the same endpoint.
- Installation metadata includes hostname, platform, architecture, Python version,
  install date, and uDOS root. It is exposed through the read-only installation
  endpoint. Both stores resolve through `settings.data_dir`, normally
  `$UDOS_HOME/data`.

The [UDO Variable document kind](../../uCode/docs/specs/udo/udo-variable.md)
and BASIC program-local variables use their own schemas and naming rules.

### Secrets
**Backend**: `backend/app/api/secret_store_api.py`
- `GET /api/secrets` — list all (masked)
- `POST /api/secrets/{name}` — set a secret
- `DELETE /api/secrets/{name}` — delete a secret
- `GET /api/secrets/env` — provider matrix (store + env + .dotenv)
- `POST /api/secrets/import-env` — import from environment
- `POST /api/secrets/export-env` — export to .env file
- `GET /api/secrets/audit` — audit trail
- `POST /api/secrets/sync-github` — sync GitHub secret names

**Persistence**: AES-256-GCM encrypted store at `~/.ucore/secrets.enc`

**UI features in SystemSurface**: Inline CRUD (add, reveal, delete), Import from Env button.

---

## Layer 3: Developer Settings (Developer Surface)

**Location**: `http://localhost:5175/developer`

**Component**: `frontend-vue/src/surfaces/developer/panels/SettingsPanel.vue`

These are developer-facing controls (USX typography/spacing, GridCore grid algebra, uSystem monitoring config). The previous `SETTINGS_ARCHITECTURE_2026.md` described these in detail using React hooks — the Vue implementation follows the same data model but uses Pinia stores or component-local state with localStorage persistence.

**Storage keys**:
- `usxSettings`
- `gridCoreSettings`
- `uSystemSettings`

---

## Data Flow

```
┌──────────────────────────────┐
│ System Surface               │
│  Global Settings             │
│  User Settings               │
│  Variables (User + Install)  │
│  Secrets                     │
└─────────────┬────────────────┘
              │
              ├── Global/User: POST /api/system/settings → ~/.ucore/data/system_settings.json
              ├── Variables:  PUT /api/variables/user  → $UDOS_HOME/data/variables.json
              ├── Install:    GET /api/variables/install → read-only
              └── Secrets:    POST /api/secrets/{name} → ~/.ucore/secrets.enc

┌──────────────────────────────┐
│ Developer Surface            │
│  Settings Tab                │
└─────────────┬────────────────┘
              │
              └── localStorage only (usxSettings, gridCoreSettings, uSystemSettings)
```

---

## Migration Notes

1. **React hooks → Vue**: The original doc referenced `useGlobalSettings`, `useUSXSettings`, `useGridCoreSettings` hooks. Vue equivalents live within components or Pinia stores.
2. **localStorage → Server persistence**: Global and User settings moved from localStorage-only to server-backed with localStorage as cache. Save is now explicit (button), not auto-watch.
3. **Old hardcoded colors** → Use CSS variables from palette
4. **Old font-size values** → Use `--usx-font-size-*` variables
5. **Grid settings** → Use GridCore hooks (independent)

---

## Future Enhancements

- [ ] Settings import/export via JSON
- [ ] Settings profiles (saved configurations)
- [ ] Keyboard shortcuts for common settings
- [ ] Accessibility settings panel (contrast, focus indicators)
- [ ] S-page/P-page content modules (Wave 2)
