# Setup and Troubleshooting

## Auth

The script reuses the OAuth client already set up for the `google-workspace` (workspace-mcp) server. It reads two user environment variables:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

It requests only `drive.metadata.readonly` (names, folders, sharing; never file contents) and stores its own token at `~/.drive-share-audit/token.json`, separate from workspace-mcp's token.

The first run opens a browser for Google sign-in. Later runs are silent until the token expires or is revoked; then the script opens the browser again on its own. If the client's consent screen is in **Testing** status, that happens every 7 days.

## Requirements

- `uv` on PATH. Dependencies are declared inline in the script, so `uv run` installs them automatically.

## Errors

| Error | Fix |
|-------|-----|
| `GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set.` | Set both as user environment variables, then restart the terminal. |
| `access_denied` or the browser shows "app blocked" | The Google account must be a test user on the OAuth consent screen, or the app must be in production. |
| `Gave up on N items after repeated rate limiting.` | Wait a few minutes and run again. |
| Browser never opened | Delete `~/.drive-share-audit/token.json` and run again in an interactive terminal. |
