import json
import base64
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import Gmail_MAIN as gm


def _build_service_stub(messages=None, full_msg=None):
    # Minimal Gmail API stub used by fetch/get
    class MessagesAPI:
        def __init__(self, messages, full_msg):
            self._messages = messages or []
            self._full_msg = full_msg

        def list(self, userId=None, labelIds=None, maxResults=None):
            return SimpleNamespace(execute=lambda: {"messages": self._messages})

        def get(self, userId=None, id=None, format=None):
            return SimpleNamespace(execute=lambda: self._full_msg)

    class UsersAPI:
        def __init__(self, messages, full_msg):
            self._messages_api = MessagesAPI(messages, full_msg)

        def messages(self):
            return self._messages_api

    class Service:
        def __init__(self, messages, full_msg):
            self._users = UsersAPI(messages, full_msg)

        def users(self):
            return self._users

    return Service(messages, full_msg)


@patch("Gmail_MAIN.build")
@patch("Gmail_MAIN.Credentials")
def test_authenticate_gmail_uses_existing_token(mock_creds, mock_build, monkeypatch, tmp_path):
    # token.json exists and is valid
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    mock_creds.from_authorized_user_file.return_value = SimpleNamespace(valid=True)

    monkeypatch.chdir(tmp_path)
    gm.authenticate_gmail()

    mock_creds.from_authorized_user_file.assert_called_once()
    mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds.from_authorized_user_file.return_value)


@patch("Gmail_MAIN.build")
@patch("Gmail_MAIN.InstalledAppFlow")
@patch("Gmail_MAIN.Credentials")
def test_authenticate_gmail_runs_oauth_when_no_token(mock_creds, mock_flow, mock_build, monkeypatch, tmp_path):
    # No token.json => run flow and write token.json
    monkeypatch.chdir(tmp_path)
    flow = SimpleNamespace(run_local_server=lambda port=0: SimpleNamespace(to_json=lambda: "{}"))
    mock_flow.from_client_secrets_file.return_value = flow

    gm.authenticate_gmail()

    # flow invoked, token written, build called
    assert (tmp_path / "token.json").exists()
    mock_build.assert_called_once()


def test_fetch_gmail_messages_calls_list_with_label(monkeypatch):
    service = _build_service_stub(messages=[{"id": "1"}, {"id": "2"}], full_msg=None)
    out = gm.fetch_gmail_messages(service)
    assert out == [{"id": "1"}, {"id": "2"}]  # shape preserved


def test_get_email_content_decodes_plain_text_and_timestamp(monkeypatch):
    # Build a fake Gmail message
    body_text = "Hello world"
    encoded = base64.urlsafe_b64encode(body_text.encode("utf-8")).decode("ascii")
    ts_ms = int(datetime(2025, 8, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    full_msg = {
        "internalDate": str(ts_ms),
        "snippet": "snippet",
        "payload": {
            "headers": [{"name": "Subject", "value": "Subject line"}],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": encoded}}
            ],
        },
    }
    service = _build_service_stub(messages=[], full_msg=full_msg)

    result = gm.get_email_content(service, "abc123")
    assert result["data"]["subject"] == "Subject line"
    assert result["data"]["snippet"] == "snippet"
    assert result["data"]["body"] == body_text
    assert result["time"].isoformat().startswith("2025-08-01T12:00:00+00:00")


@patch.object(gm, "s3")
def test_upload_to_s3_key_structure(mock_s3):
    # time components embedded in key; ensures hour-partitioning logic
    when = datetime(2025, 8, 16, 9, 5, 0, tzinfo=timezone.utc)
    email_obj = {"id": "abc", "subject": "x"}
    gm.upload_to_s3(email_obj, when)

    called = mock_s3.put_object.call_args.kwargs
    assert called["Bucket"]  # set by env in conftest
    key = called["Key"]
    assert key.startswith("emails/raw/2025/08/16/09/")
    assert key.endswith("/abc.json")
    # body must be JSON
    json.loads(called["Body"])


@patch("Gmail_MAIN.upload_to_s3")
@patch("Gmail_MAIN.get_email_content")
@patch("Gmail_MAIN.fetch_gmail_messages")
@patch("Gmail_MAIN.authenticate_gmail")
def test_main_happy_path(mock_auth, mock_fetch, mock_get, mock_upload):
    mock_auth.return_value = "SERVICE"
    mock_fetch.return_value = [{"id": "m1"}, {"id": "m2"}]
    mock_get.side_effect = [
        {"data": {"id": "m1"}, "time": datetime(2025, 8, 16, tzinfo=timezone.utc)},
        {"data": {"id": "m2"}, "time": datetime(2025, 8, 16, tzinfo=timezone.utc)},
    ]

    gm.main()

    mock_auth.assert_called_once()
    mock_fetch.assert_called_once_with("SERVICE")
    assert mock_get.call_count == 2
    assert mock_upload.call_count == 2
