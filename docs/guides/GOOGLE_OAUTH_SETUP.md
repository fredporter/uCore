# Google credentials: first-time setup

This is an installation administrator step. Ordinary users subsequently choose their own accounts and lists through Connections or the User Setup Story. Never put a Google password, access token or refresh token into the client credential fields.

## Create a Desktop OAuth app

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create/select a project you control.
2. Enable the APIs for collections you plan to connect:

   | uCore collection | Google API |
   | --- | --- |
   | Tasks | Google Tasks API |
   | Contacts | People API |
   | Notes | Google Drive API (`drive.file`, app-owned Markdown) |
   | Calendar | Google Calendar API |
   | Mail | Gmail API |

3. Configure Google Auth Platform / OAuth consent: app identity, support contact, audience and data access. For an external app in Testing, add the Google accounts you will use as test users. Workspace administrators may restrict access. Follow [Google’s consent configuration guide](https://developers.google.com/workspace/guides/configure-oauth-consent).
4. Create an OAuth client with application type **Desktop app**. Copy its client ID and, when provided, client secret. Do not use a service account, API key or Web application client for this flow. See [Google’s Desktop OAuth guide](https://developers.google.com/identity/protocols/oauth2/native-app).

uCore uses authorization code with PKCE and a loopback callback. The callback shown in Advanced uses the backend’s actual configured port, normally `http://127.0.0.1:8484/api/connections/google/callback`. Keep uCore running on the same computer as the system browser during sign-in. No public callback, hosted redirect or manual authorization-code paste is required.

## Runtime prerequisite

The backend package declares `cryptography` as a required dependency. OAuth will not save credentials when AES-GCM is unavailable. Install/synchronize the backend dependencies in a **product-owned** uCore Python environment before using OAuth.

Use `backend/.venv/bin/python scripts/check_backend_environment.py` to verify ownership, Python 3.12 and encryption. The reproducible repair command is `UV_PROJECT_ENVIRONMENT="$PWD/backend/.venv" uv --no-cache sync --project backend --locked --extra dev`. Run it from the uCore repository. The no-cache option prevents stale interpreter metadata from selecting a former shared environment after a symlink repair. Setup refuses a symlinked backend environment.

## Save in Advanced

1. Open Settings and enable Show Advanced.
2. Open Configuration → Google OAuth.
3. Paste the Desktop app Client ID and Client secret. Save credentials.
4. Check configuration confirms encrypted storage and locally available credentials. This is **not** a network verification or proof that Google has accepted the client.
5. Open Connections and follow the [first sync quickstart](QUICKSTART.md#connect-a-small-collection-first).

Saved values are not returned to this form. Client secret is cleared from the form after a save attempt; leaving it blank retains the existing secret. Enter the same client ID when updating an existing configuration. Replacing the app identity requires explicit Advanced Secrets management and reconnecting accounts; the guided form rejects accidental replacement.

The underlying secret names are `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`. Existing `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` aliases are accepted. OAuth app credentials are installation-wide; account refresh tokens are separate for each connection and stored automatically in the encrypted server vault. They are not saved in browser storage, profile answers or repository source. Encryption must be available before OAuth settings can be saved or sign-in started.

## Consent and scope

Choose collection types before signing in. uCore requests their API scopes plus identity/email. Current scopes permit the supported write operations even when your connection is initially pull-only; pull-only is a uCore sync setting, not a Google read-only permission grant. Begin with Tasks alone if you only need Tasks. Contacts, mail and calendar add further access and may introduce Google verification or organization-policy requirements.

For an external project in **Testing**, refresh tokens for these data scopes normally expire after seven days. Repeated reconnects can therefore be expected during development. Production availability depends on Google’s audience, scope and verification rules; changing a label inside uCore cannot remove those requirements. See [Google’s OAuth token expiry documentation](https://developers.google.com/identity/protocols/oauth2/).

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| App credentials needed | Save the Desktop app credentials in Advanced; check encrypted storage is available. |
| Google rejects client / redirect | Verify Desktop app type and correct project/client ID. Check the callback displayed by uCore and that backend is running locally. |
| Access blocked / user not allowed | Check consent audience, test-user list and Workspace administrator policy. Follow Google’s verification process where required. |
| Missing API / permission | Enable the relevant API, select the collection in uCore, save, then sign in again. |
| Sign-in expired | Start again from Choose Google account; state is one-use and expires after ten minutes. A backend restart also clears pending sign-ins. |
| Connected but no records | Discover lists, select the intended list/group, save and sync. Sign-in alone does not import data. |
| Previously working account needs authorization | Reconnect; check revoked access and Testing-mode token expiry. |
| Create/export needs review | Link the pending export to its existing remote record before retrying, to avoid duplicates. |

Disconnect removes the local connection token and disables sync while retaining local collection data. For provider-side revocation, remove the app grant through your Google account’s security settings. Do not paste credentials or tokens into bug reports; report the operation, status and sanitized error instead.

Documentation checked against official Google guidance on 9 November 2026. Real-account round-trip verification remains a separate user-authorized setup step.
