# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "google-api-python-client>=2.100",
#   "google-auth-oauthlib>=1.2",
# ]
# ///
"""Find items in My Drive that carry direct (non-inherited) shares.

Lists the user's folders, then the contents of every folder in their My Drive
tree through batched requests, and treats a permission as direct when the item
has it and its parent folder does not. Only those items get a full permission
fetch.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
TOKEN_PATH = Path.home() / ".drive-share-audit" / "token.json"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "output" / "latest.json"
FOLDER = "application/vnd.google-apps.folder"
SHORTCUT = "application/vnd.google-apps.shortcut"
OWNED = "'me' in owners and trashed = false"
ITEM_FIELDS = "nextPageToken, files(id, name, mimeType, parents, shared, permissionIds)"
BATCH_SIZE = 100
MAX_ATTEMPTS = 6


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def sign_in():
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit("GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set.")
    config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    log("Opening a browser to grant read-only Drive metadata access...")
    return InstalledAppFlow.from_client_config(config, SCOPES).run_local_server(port=0)


def get_credentials():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and not creds.valid and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            # Expired or revoked refresh token (e.g. 7-day Testing-mode expiry).
            log("Saved token is expired or revoked; signing in again.")
            creds = None
    if not creds or not creds.valid:
        creds = sign_in()
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def list_folders(service):
    folders = {}
    page_token = None
    while True:
        resp = (
            service.files()
            .list(q=f"{OWNED} and mimeType = '{FOLDER}'", pageSize=1000, pageToken=page_token, fields=ITEM_FIELDS)
            .execute(num_retries=MAX_ATTEMPTS)
        )
        for f in resp.get("files", []):
            folders[f["id"]] = f
        page_token = resp.get("nextPageToken")
        if not page_token:
            return folders


def list_my_drive(service, root_id):
    """Return every owned item in the user's My Drive tree, keyed by id.

    One batched files.list per folder is about 2.5x faster than paging through
    a single files.list over all owned items, and it skips items the user owns
    inside other people's folders.
    """
    folders = list_folders(service)
    items = {fid: f for fid, f in folders.items() if build_path(fid, folders, root_id)}
    log(f"Found {len(items):,} folders in My Drive; listing their contents.")
    pending = dict.fromkeys([root_id, *items])
    while pending:
        requests = {
            fid: lambda fid=fid, token=token: service.files().list(
                q=f"'{fid}' in parents and {OWNED}", pageSize=1000, pageToken=token, fields=ITEM_FIELDS
            )
            for fid, token in pending.items()
        }
        pending = {}
        for fid, resp in execute_batch(service, requests, "Listed").items():
            for f in resp.get("files", []):
                items.setdefault(f["id"], f)
            if resp.get("nextPageToken"):
                pending[fid] = resp["nextPageToken"]
        log(f"{len(items):,} items so far; {len(pending)} folders have more pages.")
    return items


def find_direct_candidates(items, my_permission_id):
    candidates = {}
    for item in items.values():
        if not item.get("shared") or item["mimeType"] == SHORTCUT:
            continue
        parent = items.get((item.get("parents") or [None])[0])
        inherited = set(parent.get("permissionIds", [])) if parent else set()
        direct = set(item.get("permissionIds", [])) - inherited - {my_permission_id}
        if direct:
            candidates[item["id"]] = direct
    return candidates


def fill_missing_permission_ids(service, items):
    # files.list omits permissionIds on some shared items, and batched files.get
    # drops it too; permissions(id) comes back reliably.
    missing = [i["id"] for i in items.values() if i.get("shared") and not i.get("permissionIds")]
    if not missing:
        return
    log(f"{len(missing):,} shared items came back without permission IDs; fetching them.")
    for file_id, resp in fetch_batch(service, missing, "id, permissions(id)").items():
        items[file_id]["permissionIds"] = [p["id"] for p in resp.get("permissions", [])]


def fetch_batch(service, ids, fields):
    requests = {i: lambda i=i: service.files().get(fileId=i, fields=fields) for i in ids}
    return execute_batch(service, requests, "Fetched")


def execute_batch(service, requests, verb):
    """Run {key: make_request} in batches, retrying rate-limited requests."""
    results = {}
    pending = list(requests)
    for attempt in range(MAX_ATTEMPTS):
        failed = []

        def callback(request_id, response, exception):
            if exception is None:
                results[request_id] = response
            elif isinstance(exception, HttpError) and exception.resp.status in (403, 429, 500, 503):
                failed.append(request_id)
            else:
                raise exception

        for start in range(0, len(pending), BATCH_SIZE):
            batch = service.new_batch_http_request(callback=callback)
            for key in pending[start : start + BATCH_SIZE]:
                batch.add(requests[key](), request_id=key)
            batch.execute()
            log(f"{verb} {len(results):,} of {len(requests):,}...")
        if not failed:
            return results
        pending = failed
        wait = 2**attempt
        log(f"{len(failed)} requests were rate limited; retrying in {wait}s.")
        time.sleep(wait)
    raise RuntimeError(f"Gave up on {len(pending)} items after repeated rate limiting.")


def build_path(item_id, items, root_id):
    """Return the item's My Drive path, or None if the chain leaves the user's own folders."""
    parts = []
    current = items.get(item_id)
    seen = set()
    while current and current["id"] not in seen:
        seen.add(current["id"])
        parts.append(current["name"])
        parent_id = (current.get("parents") or [None])[0]
        if parent_id == root_id:
            return "/" + "/".join(reversed(parts))
        current = items.get(parent_id)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write the JSON result")
    args = parser.parse_args()

    started = time.monotonic()
    service = build("drive", "v3", credentials=get_credentials(), cache_discovery=False)
    my_permission_id = service.about().get(fields="user(permissionId)").execute()["user"]["permissionId"]
    root_id = service.files().get(fileId="root", fields="id").execute()["id"]

    items = list_my_drive(service, root_id)
    fill_missing_permission_ids(service, items)
    candidates = find_direct_candidates(items, my_permission_id)
    log(f"{len(candidates):,} items have direct grants; fetching details.")
    details = fetch_batch(
        service,
        list(candidates),
        "id, webViewLink, permissions(id, type, role, emailAddress, displayName, domain, allowFileDiscovery)",
    )

    results = []
    for item_id, direct_ids in candidates.items():
        item = items[item_id]
        detail = details[item_id]
        grants = [
            {
                "type": p["type"],
                "role": p["role"],
                "email": p.get("emailAddress"),
                "name": p.get("displayName"),
                "domain": p.get("domain"),
                "discoverable": p.get("allowFileDiscovery"),
            }
            for p in detail.get("permissions", [])
            if p["id"] in direct_ids and p["role"] != "owner"
        ]
        if not grants:
            continue
        results.append(
            {
                "id": item_id,
                "name": item["name"],
                "kind": "folder" if item["mimeType"] == FOLDER else "file",
                "path": build_path(item_id, items, root_id),
                "link": detail.get("webViewLink"),
                "grants": grants,
            }
        )
    results.sort(key=lambda r: r["path"].lower())

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.monotonic() - started, 1),
        "items_scanned": len(items),
        "shared_items": sum(1 for i in items.values() if i.get("shared")),
        "direct_share_items": len(results),
        "items": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k != "items"} | {"output": str(args.out)}))


if __name__ == "__main__":
    main()
