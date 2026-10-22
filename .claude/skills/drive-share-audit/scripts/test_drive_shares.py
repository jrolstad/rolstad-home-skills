# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "google-api-python-client>=2.100",
#   "google-auth-oauthlib>=1.2",
#   "pytest>=8",
# ]
# ///
"""Unit tests for drive_shares.py. Run with: uv run scripts/test_drive_shares.py"""

import json
import re
import sys
from unittest.mock import Mock

import drive_shares as ds
import httplib2
import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

ROOT = "root-id"
ME = "perm-me"


def http_error(status):
    return HttpError(httplib2.Response({"status": status}), b"")


def item(id, name, parent=ROOT, perms=(), shared=None, mime="application/pdf"):
    f = {"id": id, "name": name, "mimeType": mime, "parents": [parent] if parent else []}
    if perms:
        f["permissionIds"] = list(perms)
    f["shared"] = bool(perms) if shared is None else shared
    return f


def folder(id, name, parent=ROOT, perms=(), shared=None):
    return item(id, name, parent, perms, shared, mime=ds.FOLDER)


class FakeRequest:
    def __init__(self, resolve):
        self._resolve = resolve

    def execute(self, num_retries=0):
        return self._resolve()


class FakeBatch:
    def __init__(self, drive, callback):
        self.drive = drive
        self.callback = callback
        self.requests = []

    def add(self, request, request_id):
        self.requests.append((request_id, request))

    def execute(self):
        self.drive.batches.append([rid for rid, _ in self.requests])
        for rid, request in self.requests:
            errors = self.drive.batch_errors.get(rid)
            if errors:
                self.callback(rid, None, errors.pop(0))
            else:
                self.callback(rid, request.execute(), None)


class FakeDrive:
    """Stands in for the googleapiclient Drive v3 service."""

    def __init__(self, files=(), not_owned=(), details=None, page_size=1000, batch_errors=None):
        self.all_files = list(files)
        self.not_owned = set(not_owned)
        self.details = details or {}
        self.page_size = page_size
        self.batch_errors = batch_errors or {}
        self.batches = []
        self.list_calls = []
        self.get_calls = []

    def files(self):
        return self

    def about(self):
        return Mock(get=lambda fields: FakeRequest(lambda: {"user": {"permissionId": ME}}))

    def new_batch_http_request(self, callback):
        return FakeBatch(self, callback)

    def list(self, q, pageSize, pageToken, fields):
        self.list_calls.append({"q": q, "pageToken": pageToken, "fields": fields})

        def resolve():
            matches = [f for f in self.all_files if f["id"] not in self.not_owned]
            if f"mimeType = '{ds.FOLDER}'" in q:
                matches = [f for f in matches if f["mimeType"] == ds.FOLDER]
            parent = re.match(r"'([^']+)' in parents", q)
            if parent:
                matches = [f for f in matches if parent.group(1) in f.get("parents", [])]
            offset = int(pageToken or 0)
            resp = {"files": [dict(f) for f in matches[offset : offset + self.page_size]]}
            if offset + self.page_size < len(matches):
                resp["nextPageToken"] = str(offset + self.page_size)
            return resp

        return FakeRequest(resolve)

    def get(self, fileId, fields):
        self.get_calls.append({"fileId": fileId, "fields": fields})
        if fileId == "root":
            return FakeRequest(lambda: {"id": ROOT})
        return FakeRequest(lambda: {"id": fileId, **self.details[fileId]})


@pytest.fixture
def sleeps(monkeypatch):
    calls = []
    monkeypatch.setattr(ds.time, "sleep", calls.append)
    return calls


class TestBuildPath:
    def test_direct_child_of_root(self):
        items = {"a": item("a", "Doc")}
        assert ds.build_path("a", items, ROOT) == "/Doc"

    def test_nested_item(self):
        items = {
            "f1": folder("f1", "Outer"),
            "f2": folder("f2", "Inner", parent="f1"),
            "a": item("a", "Doc", parent="f2"),
        }
        assert ds.build_path("a", items, ROOT) == "/Outer/Inner/Doc"

    def test_parent_outside_my_folders(self):
        items = {"a": item("a", "Doc", parent="someone-elses-folder")}
        assert ds.build_path("a", items, ROOT) is None

    def test_chain_breaks_partway_up(self):
        items = {"f2": folder("f2", "Inner", parent="missing"), "a": item("a", "Doc", parent="f2")}
        assert ds.build_path("a", items, ROOT) is None

    def test_unknown_item(self):
        assert ds.build_path("nope", {}, ROOT) is None

    def test_item_without_parents(self):
        items = {"a": item("a", "Orphan", parent=None)}
        assert ds.build_path("a", items, ROOT) is None

    def test_parents_key_absent(self):
        items = {"a": {"id": "a", "name": "Orphan"}}
        assert ds.build_path("a", items, ROOT) is None

    def test_cycle_returns_none(self):
        items = {"x": folder("x", "X", parent="y"), "y": folder("y", "Y", parent="x")}
        assert ds.build_path("x", items, ROOT) is None

    def test_uses_first_parent(self):
        a = item("a", "Doc", parent=ROOT)
        a["parents"].append("other")
        assert ds.build_path("a", {"a": a}, ROOT) == "/Doc"


class TestFindDirectCandidates:
    def test_unshared_items_skipped(self):
        items = {"a": item("a", "Doc", perms=[ME, "p1"], shared=False)}
        assert ds.find_direct_candidates(items, ME) == {}

    def test_shortcuts_skipped(self):
        items = {"a": item("a", "Link", perms=[ME, "p1"], mime=ds.SHORTCUT)}
        assert ds.find_direct_candidates(items, ME) == {}

    def test_permissions_on_parent_are_inherited(self):
        items = {
            "f": folder("f", "Shared", perms=[ME, "p1"]),
            "a": item("a", "Doc", parent="f", perms=[ME, "p1"]),
        }
        assert ds.find_direct_candidates(items, ME) == {"f": {"p1"}}

    def test_extra_permission_on_child_is_direct(self):
        items = {
            "f": folder("f", "Shared", perms=[ME, "p1"]),
            "a": item("a", "Doc", parent="f", perms=[ME, "p1", "p2"]),
        }
        assert ds.find_direct_candidates(items, ME)["a"] == {"p2"}

    def test_own_permission_ignored(self):
        items = {"a": item("a", "Doc", perms=[ME], shared=True)}
        assert ds.find_direct_candidates(items, ME) == {}

    def test_parent_not_in_items_means_all_direct(self):
        items = {"a": item("a", "Doc", parent=ROOT, perms=[ME, "p1", "p2"])}
        assert ds.find_direct_candidates(items, ME) == {"a": {"p1", "p2"}}

    def test_item_without_parents(self):
        items = {"a": item("a", "Doc", parent=None, perms=[ME, "p1"])}
        assert ds.find_direct_candidates(items, ME) == {"a": {"p1"}}

    def test_shared_without_permission_ids(self):
        items = {"a": item("a", "Doc", shared=True)}
        assert ds.find_direct_candidates(items, ME) == {}

    def test_unshared_parent_contributes_nothing(self):
        items = {
            "f": folder("f", "Private", shared=False),
            "a": item("a", "Doc", parent="f", perms=[ME, "p1"]),
        }
        assert ds.find_direct_candidates(items, ME) == {"a": {"p1"}}

    def test_role_raise_on_child_is_not_reported(self):
        # Known limit: permission IDs are per grantee, not per role.
        items = {
            "f": folder("f", "Shared", perms=[ME, "p1"]),
            "a": item("a", "Doc", parent="f", perms=[ME, "p1"]),
        }
        assert "a" not in ds.find_direct_candidates(items, ME)


class TestFillMissingPermissionIds:
    def test_nothing_missing_makes_no_requests(self):
        drive = FakeDrive()
        items = {"a": item("a", "Doc", perms=[ME, "p1"]), "b": item("b", "Private")}
        ds.fill_missing_permission_ids(drive, items)
        assert drive.batches == []

    def test_fetches_only_shared_items_missing_ids(self):
        drive = FakeDrive(details={"a": {"permissions": [{"id": ME}, {"id": "p1"}]}})
        items = {
            "a": item("a", "Doc", shared=True),
            "b": item("b", "Has IDs", perms=[ME, "p2"]),
            "c": item("c", "Private"),
        }
        ds.fill_missing_permission_ids(drive, items)
        assert items["a"]["permissionIds"] == [ME, "p1"]
        assert items["b"]["permissionIds"] == [ME, "p2"]
        assert "permissionIds" not in items["c"]
        assert drive.get_calls == [{"fileId": "a", "fields": "id, permissions(id)"}]

    def test_empty_permission_list_counts_as_missing(self):
        drive = FakeDrive(details={"a": {}})
        items = {"a": item("a", "Doc", shared=True)}
        items["a"]["permissionIds"] = []
        ds.fill_missing_permission_ids(drive, items)
        assert items["a"]["permissionIds"] == []
        assert drive.batches == [["a"]]


class TestFetchBatch:
    def test_gets_each_id_with_fields(self):
        drive = FakeDrive(details={"a": {"name": "A"}, "b": {"name": "B"}})
        result = ds.fetch_batch(drive, ["a", "b"], "id, name")
        assert result == {"a": {"id": "a", "name": "A"}, "b": {"id": "b", "name": "B"}}
        assert drive.get_calls == [{"fileId": "a", "fields": "id, name"}, {"fileId": "b", "fields": "id, name"}]

    def test_no_ids(self):
        drive = FakeDrive()
        assert ds.fetch_batch(drive, [], "id") == {}
        assert drive.batches == []


class TestExecuteBatch:
    @staticmethod
    def requests_for(keys):
        return {k: lambda k=k: FakeRequest(lambda: {"key": k}) for k in keys}

    def test_returns_every_response(self, sleeps):
        result = ds.execute_batch(FakeDrive(), self.requests_for(["a", "b"]), "Did")
        assert result == {"a": {"key": "a"}, "b": {"key": "b"}}
        assert sleeps == []

    def test_splits_into_batches(self, sleeps):
        drive = FakeDrive()
        keys = [str(i) for i in range(ds.BATCH_SIZE * 2 + 50)]
        result = ds.execute_batch(drive, self.requests_for(keys), "Did")
        assert len(result) == len(keys)
        assert [len(b) for b in drive.batches] == [ds.BATCH_SIZE, ds.BATCH_SIZE, 50]

    @pytest.mark.parametrize("status", [403, 429, 500, 503])
    def test_retries_retryable_errors(self, sleeps, status):
        drive = FakeDrive(batch_errors={"b": [http_error(status), http_error(status)]})
        result = ds.execute_batch(drive, self.requests_for(["a", "b", "c"]), "Did")
        assert result == {"a": {"key": "a"}, "b": {"key": "b"}, "c": {"key": "c"}}
        assert drive.batches == [["a", "b", "c"], ["b"], ["b"]]
        assert sleeps == [1, 2]

    @pytest.mark.parametrize("status", [400, 401, 404])
    def test_raises_non_retryable_http_errors(self, sleeps, status):
        drive = FakeDrive(batch_errors={"a": [http_error(status)]})
        with pytest.raises(HttpError):
            ds.execute_batch(drive, self.requests_for(["a"]), "Did")

    def test_raises_other_exceptions(self, sleeps):
        drive = FakeDrive(batch_errors={"a": [ValueError("boom")]})
        with pytest.raises(ValueError, match="boom"):
            ds.execute_batch(drive, self.requests_for(["a"]), "Did")

    def test_gives_up_after_max_attempts(self, sleeps):
        drive = FakeDrive(batch_errors={"a": [http_error(429)] * ds.MAX_ATTEMPTS})
        with pytest.raises(RuntimeError, match="Gave up on 1 items"):
            ds.execute_batch(drive, self.requests_for(["a", "b"]), "Did")
        assert sleeps == [2**i for i in range(ds.MAX_ATTEMPTS)]

    def test_succeeds_on_last_attempt(self, sleeps):
        drive = FakeDrive(batch_errors={"a": [http_error(429)] * (ds.MAX_ATTEMPTS - 1)})
        result = ds.execute_batch(drive, self.requests_for(["a"]), "Did")
        assert result == {"a": {"key": "a"}}

    def test_logs_progress(self, sleeps, capsys):
        ds.execute_batch(FakeDrive(), self.requests_for(["a", "b"]), "Listed")
        assert "Listed 2 of 2..." in capsys.readouterr().err


class TestListFolders:
    def test_returns_owned_folders_by_id(self):
        drive = FakeDrive(
            files=[folder("f1", "One"), item("a", "Doc"), folder("f2", "Two", parent="f1"), folder("x", "Theirs")],
            not_owned=["x"],
        )
        assert set(ds.list_folders(drive)) == {"f1", "f2"}
        assert ds.OWNED in drive.list_calls[0]["q"]
        assert drive.list_calls[0]["fields"] == ds.ITEM_FIELDS

    def test_follows_pages(self):
        drive = FakeDrive(files=[folder(f"f{i}", f"F{i}") for i in range(5)], page_size=2)
        assert len(ds.list_folders(drive)) == 5
        assert [c["pageToken"] for c in drive.list_calls] == [None, "2", "4"]

    def test_no_folders(self):
        assert ds.list_folders(FakeDrive()) == {}


class TestListMyDrive:
    def test_lists_whole_tree(self, sleeps):
        drive = FakeDrive(
            files=[
                folder("f1", "Outer"),
                folder("f2", "Inner", parent="f1"),
                item("a", "Top"),
                item("b", "Mid", parent="f1"),
                item("c", "Deep", parent="f2"),
            ]
        )
        assert set(ds.list_my_drive(drive, ROOT)) == {"f1", "f2", "a", "b", "c"}

    def test_skips_folders_outside_my_drive(self, sleeps):
        drive = FakeDrive(
            files=[
                folder("mine", "Mine"),
                folder("elsewhere", "In someone else's folder", parent="theirs"),
                item("a", "Hidden", parent="elsewhere"),
            ]
        )
        assert set(ds.list_my_drive(drive, ROOT)) == {"mine"}

    def test_skips_items_owned_by_others(self, sleeps):
        drive = FakeDrive(files=[folder("f1", "Mine"), item("a", "Theirs", parent="f1")], not_owned=["a"])
        assert set(ds.list_my_drive(drive, ROOT)) == {"f1"}

    def test_follows_pages_per_folder(self, sleeps):
        files = [folder("f1", "Big")] + [item(f"a{i}", f"A{i}", parent="f1") for i in range(5)]
        drive = FakeDrive(files=files, page_size=2)
        assert set(ds.list_my_drive(drive, ROOT)) == {"f1", *(f"a{i}" for i in range(5))}
        f1_tokens = [c["pageToken"] for c in drive.list_calls if c["q"].startswith("'f1' in parents")]
        assert f1_tokens == [None, "2", "4"]

    def test_empty_drive(self, sleeps):
        assert ds.list_my_drive(FakeDrive(), ROOT) == {}


class TestSignIn:
    def test_requires_client_env(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "secret")
        with pytest.raises(SystemExit, match="GOOGLE_OAUTH_CLIENT_ID"):
            ds.sign_in()

    def test_requires_client_secret(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "id")
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
        with pytest.raises(SystemExit):
            ds.sign_in()

    def test_runs_local_flow(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "secret")
        flow_cls = Mock()
        monkeypatch.setattr(ds, "InstalledAppFlow", flow_cls)
        creds = ds.sign_in()
        config, scopes = flow_cls.from_client_config.call_args.args
        assert config["installed"]["client_id"] == "id"
        assert config["installed"]["client_secret"] == "secret"
        assert scopes == ds.SCOPES
        flow_cls.from_client_config.return_value.run_local_server.assert_called_once_with(port=0)
        assert creds is flow_cls.from_client_config.return_value.run_local_server.return_value


class TestGetCredentials:
    @pytest.fixture
    def token_path(self, tmp_path, monkeypatch):
        path = tmp_path / "nested" / "token.json"
        monkeypatch.setattr(ds, "TOKEN_PATH", path)
        return path

    @pytest.fixture
    def saved(self, monkeypatch):
        creds_cls = Mock()
        monkeypatch.setattr(ds, "Credentials", creds_cls)
        return creds_cls.from_authorized_user_file

    @pytest.fixture
    def sign_in(self, monkeypatch):
        fresh = Mock(valid=True, **{"to_json.return_value": '{"fresh": true}'})
        mock = Mock(return_value=fresh)
        monkeypatch.setattr(ds, "sign_in", mock)
        return mock

    def test_no_token_signs_in_and_saves(self, token_path, saved, sign_in):
        creds = ds.get_credentials()
        assert creds is sign_in.return_value
        saved.assert_not_called()
        assert token_path.read_text(encoding="utf-8") == '{"fresh": true}'

    def test_valid_token_reused(self, token_path, saved, sign_in):
        token_path.parent.mkdir(parents=True)
        token_path.write_text("{}", encoding="utf-8")
        saved.return_value = Mock(valid=True, **{"to_json.return_value": '{"saved": true}'})
        assert ds.get_credentials() is saved.return_value
        saved.assert_called_once_with(str(token_path), ds.SCOPES)
        sign_in.assert_not_called()
        assert token_path.read_text(encoding="utf-8") == '{"saved": true}'

    def test_expired_token_refreshed(self, token_path, saved, sign_in):
        token_path.parent.mkdir(parents=True)
        token_path.write_text("{}", encoding="utf-8")
        creds = Mock(valid=False, refresh_token="r", **{"to_json.return_value": '{"refreshed": true}'})
        creds.refresh.side_effect = lambda request: setattr(creds, "valid", True)
        saved.return_value = creds
        assert ds.get_credentials() is creds
        sign_in.assert_not_called()
        assert token_path.read_text(encoding="utf-8") == '{"refreshed": true}'

    def test_revoked_refresh_token_signs_in(self, token_path, saved, sign_in):
        token_path.parent.mkdir(parents=True)
        token_path.write_text("{}", encoding="utf-8")
        creds = Mock(valid=False, refresh_token="r")
        creds.refresh.side_effect = RefreshError("invalid_grant")
        saved.return_value = creds
        assert ds.get_credentials() is sign_in.return_value
        assert token_path.read_text(encoding="utf-8") == '{"fresh": true}'

    def test_invalid_token_without_refresh_token_signs_in(self, token_path, saved, sign_in):
        token_path.parent.mkdir(parents=True)
        token_path.write_text("{}", encoding="utf-8")
        saved.return_value = Mock(valid=False, refresh_token=None)
        assert ds.get_credentials() is sign_in.return_value
        saved.return_value.refresh.assert_not_called()


def perm(id, type="user", role="reader", email=None, **extra):
    return {"id": id, "type": type, "role": role, "emailAddress": email, **extra}


class TestMain:
    @pytest.fixture
    def drive(self):
        files = [
            folder("fa", "FolderA", perms=[ME, "p-bob"]),
            item("inherited", "doc1", parent="fa", perms=[ME, "p-bob"]),
            item("public", "doc2", parent="fa", perms=[ME, "p-bob", "p-anyone"]),
            folder("fb", "folderB", shared=False),
            item("lower", "alpha", parent="fb", perms=[ME, "p-carol"]),
            item("zeta", "Zeta", perms=[ME, "p-dave"]),
            item("missing", "Missing IDs", shared=True),
            item("ownerOnly", "Owner only", perms=[ME, "p-old-owner"]),
            item("shortcut", "Shortcut", perms=[ME, "p-erin"], mime=ds.SHORTCUT),
            item("private", "Private"),
            folder("foreign", "Elsewhere", parent="their-folder"),
            item("foreignDoc", "Hidden", parent="foreign", perms=[ME, "p-frank"]),
        ]
        details = {
            "fa": {"webViewLink": "link-fa", "permissions": [perm(ME, role="owner"), perm("p-bob", email="bob@x")]},
            "public": {
                "webViewLink": "link-public",
                "permissions": [
                    perm(ME, role="owner"),
                    perm("p-bob", email="bob@x"),
                    perm("p-anyone", type="anyone", role="writer", allowFileDiscovery=False),
                ],
            },
            "lower": {"webViewLink": "link-lower", "permissions": [perm("p-carol", role="commenter", email="c@x")]},
            "zeta": {
                "webViewLink": "link-zeta",
                "permissions": [perm("p-dave", type="domain", role="reader", domain="corp.com", displayName="Corp")],
            },
            "missing": {"webViewLink": "link-missing", "permissions": [perm(ME, role="owner"), perm("p-gus")]},
            "ownerOnly": {"webViewLink": "link-owner", "permissions": [perm("p-old-owner", role="owner")]},
        }
        return FakeDrive(files=files, details=details)

    @pytest.fixture
    def run(self, drive, monkeypatch, tmp_path, capsys, sleeps):
        out = tmp_path / "out" / "result.json"
        monkeypatch.setattr(ds, "build", lambda *a, **k: drive)
        monkeypatch.setattr(ds, "get_credentials", lambda: object())
        monkeypatch.setattr(sys, "argv", ["drive_shares.py", "--out", str(out)])
        ds.main()
        summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        return json.loads(out.read_text(encoding="utf-8")), summary, out

    def test_reports_only_direct_shares_sorted_case_insensitively(self, run):
        result, _, _ = run
        assert [i["path"] for i in result["items"]] == [
            "/FolderA",
            "/FolderA/doc2",
            "/folderB/alpha",
            "/Missing IDs",
            "/Zeta",
        ]

    def test_item_fields(self, run):
        result, _, _ = run
        by_id = {i["id"]: i for i in result["items"]}
        assert by_id["fa"]["kind"] == "folder"
        assert by_id["lower"] == {
            "id": "lower",
            "name": "alpha",
            "kind": "file",
            "path": "/folderB/alpha",
            "link": "link-lower",
            "grants": [
                {
                    "type": "user",
                    "role": "commenter",
                    "email": "c@x",
                    "name": None,
                    "domain": None,
                    "discoverable": None,
                }
            ],
        }

    def test_grants_exclude_inherited_and_owner(self, run):
        result, _, _ = run
        by_id = {i["id"]: i for i in result["items"]}
        assert by_id["public"]["grants"] == [
            {"type": "anyone", "role": "writer", "email": None, "name": None, "domain": None, "discoverable": False}
        ]
        assert by_id["zeta"]["grants"][0] == {
            "type": "domain",
            "role": "reader",
            "email": None,
            "name": "Corp",
            "domain": "corp.com",
            "discoverable": None,
        }
        assert "ownerOnly" not in by_id

    def test_missing_permission_ids_are_filled(self, run):
        result, _, _ = run
        by_id = {i["id"]: i for i in result["items"]}
        assert [g["role"] for g in by_id["missing"]["grants"]] == ["reader"]

    def test_counts_and_summary(self, run):
        result, summary, out = run
        assert result["items_scanned"] == 10
        assert result["shared_items"] == 8
        assert result["direct_share_items"] == 5
        assert set(result) == {
            "generated_at",
            "elapsed_seconds",
            "items_scanned",
            "shared_items",
            "direct_share_items",
            "items",
        }
        assert summary == {k: v for k, v in result.items() if k != "items"} | {"output": str(out)}

    def test_generated_at_is_utc_iso(self, run):
        result, _, _ = run
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00", result["generated_at"])

    def test_no_shares(self, monkeypatch, tmp_path, capsys, sleeps):
        out = tmp_path / "result.json"
        monkeypatch.setattr(ds, "build", lambda *a, **k: FakeDrive(files=[item("a", "Private")]))
        monkeypatch.setattr(ds, "get_credentials", lambda: object())
        monkeypatch.setattr(sys, "argv", ["drive_shares.py", "--out", str(out)])
        ds.main()
        result = json.loads(out.read_text(encoding="utf-8"))
        assert result["items"] == []
        assert result["direct_share_items"] == 0
        assert result["items_scanned"] == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, *sys.argv[1:]]))
