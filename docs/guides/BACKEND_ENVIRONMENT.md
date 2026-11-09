# Backend environment ownership and recovery

uCore owns `backend/.venv`, a real Python 3.12 environment ignored by Git. The root `.venv` compatibility link may point to that owned environment. It must never lead to `Code/.venv` or another product. `backend/pyproject.toml` declares runtime requirements, including encryption and the minimal macOS Cocoa bindings; committed `backend/uv.lock` pins dependency artifacts. The root workspace lock is unrelated.

From the uCore repository:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/backend/.venv" uv --no-cache sync --project backend --locked --extra dev
backend/.venv/bin/python scripts/check_backend_environment.py
pnpm dev:backend
```

Use Python 3.12 and install uv before running setup. Setup refuses a symlinked backend environment. If migrating an old symlink, stop the owning service, remove **only the symlink** after verifying its target, then run the command above. Do not delete the shared target. uv caches interpreter metadata: bypass that cache during migration so it cannot select an old symlink target. The explicit environment path and read-only guard check ownership and actual AES-GCM operation.

Lifecycle: setup creates/synchronizes the environment; existing uCore LaunchAgents own running processes; normal service restart loads updated code. No new service is added. The environment is reproducible and may be removed/rebuilt when uCore is stopped. Current owned environment is approximately 282 MB before native Cocoa additions, rather than the full shared collection of unrelated packages.

Startup scripts and the package backend command require the owned interpreter and refuse system-Python fallback. The backend LaunchAgent points directly to the owned interpreter, uses canonical UDOS_HOME log paths, disables user-site imports and turns off debug. Other products' environments are not a source of backend dependencies.

Secrets require encryption. Missing crypto, a missing key for an existing encrypted store, or a decryption failure blocks access/saving instead of silently starting an empty store. Encrypted writes replace atomically with owner-only permissions. A legacy plaintext store migrates only after an encrypted round-trip check; differing existing credentials win and legacy alternatives are retained in an encrypted backup entry. Back up the encryption key together with the encrypted store through your existing secure backup process. Never copy either into the repository.

For validation, run tests with UDOS_HOME, data roots, Vault/Shared/Public and uFlow task roots pointed to temporary directories. API tests require loopback sockets. Do not run release tests against live personal data. A working Git executable must be on PATH for Git fixtures; the standalone Command Line Tools Git works on this workstation at `/Library/Developer/CommandLineTools/usr/bin/git`. The full Xcode IDE is not a project requirement. It and its Xcode-specific support data were removed at the user’s request; standalone tools remain. No Xcode licence was accepted by this repair.
