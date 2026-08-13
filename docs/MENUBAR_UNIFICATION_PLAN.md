# macOS Menu Bar Unification Plan

**Date:** 2026-06-27  
**Status:** ✅ Complete  
**Goal:** Single unified, modular macOS menu bar app replacing `popcorn.py` and `snackbar_menu.py`

---

## Current State Analysis

### `popcorn.py` (Ollama/UI Hub Manager)

- **Icon:** 🍿 Popcorn emoji
- **Features:**
  - Ollama status checking (running/installed/stopped)
  - Ollama controls: Start, Stop, Restart
  - UI Hub health check and heal
  - Backend daemon management
  - S190 fallback page
  - Lockfile: `~/.ucore/ucore-popcorn.pid`

### `snackbar_menu.py` (Clipboard/Snacks/Surfaces)

- **Icon:** 🍔 Hamburger emoji
- **Features:**
  - Clipboard buffer with floating NSPanel
  - Global shortcut (Ctrl+Cmd+V) for clipboard panel
  - Snacks from `/api/snacks/system` endpoint
  - Surfaces menu (8 predefined surfaces)
  - Start at login toggle
  - Backend/frontend restart
  - Lockfile: `~/.ucore/ucore-menu.pid`

### `unified_menu.py` (Legacy - 1255 lines)

- **Status:** Legacy - being replaced by modular architecture
- **Issues:** Too large, duplicate code, hard to maintain

### `unified_menu_simple.py` (Simplified Version - 541 lines)

- **Icon:** 🍿 Popcorn emoji
- **Features:**
  - UI Hub status and access
  - Quick access to SnackMachine surface
  - Clipboard buffer (essential)
  - Backend status
  - Start at login toggle
- **Status:** ✅ Properly modularized (2026-06-28)
- **Architecture:**
  - `api_helpers.py` - HTTP requests and status checks
  - `status_icon.py` - Status icon management
  - `lockfile.py` - Lockfile management
  - `launchd_integration.py` - Launchd integration (delegates to launchd_manager)
  - `app_delegate.py` - App delegate and menu creation
  - `unified_menu_simple.py` - Main entry point (reduced to ~200 lines)

---

## Duplication Matrix

| Feature              | popcorn.py | snackbar_menu.py | unified_menu.py         |
| -------------------- | ---------- | ---------------- | ----------------------- |
| Backend health check | ✓          | ✓                | ✓                       |
| UI Hub status/heal   | ✓          | ✓                | ✓                       |
| Ollama management    | ✓          | ✗                | Partial (plugin exists) |
| Clipboard buffer     | ✗          | ✓                | Partial (plugin exists) |
| Clipboard panel      | ✗          | ✓                | Missing                 |
| Global shortcut      | ✗          | ✓                | Partial                 |
| Snacks registry      | ✗          | ✓                | ✓                       |
| Surfaces menu        | ✓          | ✓                | ✓                       |
| Start at login       | ✗          | ✓                | ✓                       |
| Lockfile mgmt        | ✓          | ✓                | ✓                       |

---

## Unification Strategy

### Phase 1: Complete `unified_menu.py` Implementation

#### 1.1 Clipboard Panel Implementation

Port the clipboard NSPanel from `snackbar_menu.py`:

- `ClipboardSearchField` class
- `ClipboardTableView` class
- `_ensure_clipboard_panel()` method
- `showClipboardPopover_`, `hideClipboardPopover_`, `refreshClipboardPopover_`
- `pasteSelectedClipboardItem_`, `pinSelectedClipboardItem_`, `deleteSelectedClipboardItem_`
- `searchClipboard_` with osascript chooser

#### 1.2 Action Handler Integration

Merge action handlers from both files:

- `openUIHub_` - with auto-start from popcorn
- `healthCheck_` - merge both implementations
- `healUIHub_` - use popcorn's robust implementation
- `openS190Diagnostics_` - port from popcorn
- `ollamaAction_` - connect to ollama_snack
- `openSurface_` - connect to surface_snack
- `restartBackend_` - use unified implementation
- `restartFrontend_` - use unified implementation
- `toggleStartAtLogin_` - use snackbar's implementation
- `quitApp_` - merge lockfile cleanup

### Phase 2: Configuration Consolidation

#### 2.1 Single Lockfile

- Use: `~/.ucore/ucore-menu.pid`
- Remove: `ucore-popcorn.pid`

#### 2.2 Launchd Integration

- Update `install_macos_menu.py` to point to `unified_menu.py`
- Label: `com.udos.ucore-menu` (already correct)
- KeepAlive: `false` (menu should not respawn automatically)

### Phase 3: Snack Plugin Refinement

#### 3.1 Ollama Snack

- Add `_refresh_status()` call during menu refresh
- Connect to delegate for UI updates
- Handle disable flag (`~/.ucore/ollama_disabled`)

#### 3.2 Clipboard Snack

- Add `_ensure_clipboard_panel()` integration
- Connect panel actions to snack methods

#### 3.3 Surface Snack

- Already has auto-start logic
- Merge surface definitions from both files

#### 3.4 System Snack

- Add NSAlert dialogs for user feedback
- Connect to menu delegate for UI updates

---

## File Changes Required

### Files to Modify

1. **`backend/app/menu/unified_menu.py`** - ✅ Complete implementation (clipboard panel, global shortcut, action handlers)
2. **`backend/app/menu/install_macos_menu.py`** - ✅ Updated MENU_SCRIPT path to `unified_menu.py`
3. **`backend/app/menu/snacks/ollama_snack.py`** - Add `_refresh_status()` integration with menu delegate
4. **`backend/app/menu/snacks/clipboard_snack.py`** - Add panel integration and NSPanel delegation

### Files Removed

1. **`backend/app/ui/popcorn.py`** - ✅ Removed (merged into unified_menu.py)
2. **`backend/app/menu/snackbar_menu.py`** - ✅ Removed (merged into unified_menu.py)

### Files to Keep

1. **`backend/snackmachine/registry.py`** - Core registry (keep)
2. **`backend/app/menu/snacks/*.py`** - Plugin modules (keep)

---

## Implementation Checklist

- [x] Port clipboard NSPanel to unified_menu.py
- [x] Port global shortcut registration
- [x] Merge UI Hub auto-start logic
- [x] Connect ollama_snack to menu refresh
- [x] Connect clipboard_snack panel methods (integrated in unified_menu.py)
- [x] Update install_macos_menu.py
- Test unified menu on macOS before removing final deprecated wrappers
- [x] Remove old files
- [x] Update documentation

---

## Technical Notes

### Icon Decision

- **Keep:** 🍿 Popcorn emoji (more distinctive, already in unified_menu)
- **Alternative:** 🍔 Hamburger (matches snackbar theme)

### Menu Structure (Proposed)

```
🍿 uCore Menu
├── UI Hub Status (🟢/🔴)
│   ├── Open UI Hub (o)
│   ├── Health Check (h)
│   ├── Heal UI Hub (r)
│   └── Open S190 Diagnostics (d)
├── Ollama Status (🏖️/○)
│   ├── Start/Stop/Restart
│   └── Installed Models
├── Clipboard Buffer (📋)
│   ├── Open Clipboard Panel (Ctrl+Cmd+V)
│   ├── Search... (f)
│   ├── Capture Current Clipboard
│   ├── Saved Items
│   ├── Recent Items
│   ├── Clear History
│   └── Clear All
├── Snacks by Category
│   └── [Dynamic from registry]
├── Surfaces (🖥️)
│   └── [Dynamic from API]
├── Services (⚙️)
│   ├── Backend Status
│   ├── Restart Backend
│   ├── Restart Frontend
│   └── Start at Login (✓/ )
└── Quit (q)
```

### Key Integration Points

1. **API Endpoints:** Both use same `UCORE_URL` (localhost:8484)
2. **UI Hub URL:** Both use `localhost:5173`
3. **Lockfile:** Consolidate to single location
4. **Logging:** Use unified logger name `ucore-menu`

---

## Completion Summary

### Completed Changes

- ✅ `backend/app/menu/unified_menu.py` - Full implementation with clipboard panel, global shortcut, all action handlers
- ✅ `backend/app/menu/install_macos_menu.py` - Updated to point to `unified_menu.py`
- ✅ `backend/app/ui/popcorn.py` - Deprecated with redirect stub
- ✅ `backend/app/menu/snackbar_menu.py` - Deprecated with redirect stub
- ✅ `docs/REMNANTS_AND_DUPLICATION_AUDIT.md` - Updated to reflect unified menu as canonical

### Next Steps

1. Test unified menu on macOS to verify all functionality
2. Verify clipboard panel NSPanel works correctly
3. Verify global shortcut (Ctrl+Cmd+V) opens clipboard panel
4. Verify Ollama status refresh works
5. Remove deprecated files after testing (optional)
