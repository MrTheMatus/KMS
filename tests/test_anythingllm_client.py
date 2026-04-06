"""Unit tests for AnythingLLM multipart upload builder."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from kms.app.anythingllm_client import AnythingLLMClient, _multipart_form_data_file


def test_multipart_form_data_file_contains_file_field_and_bytes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "note.md"
        p.write_text("hello vault", encoding="utf-8")
        content_type, body = _multipart_form_data_file(p)
        assert "multipart/form-data; boundary=" in content_type
        assert b'name="file"' in body
        assert b"filename=" in body
        assert b"hello vault" in body
        assert b"Content-Type: text/markdown" in body
        assert b"addToWorkspaces" not in body


def test_multipart_form_data_file_optional_workspace_slugs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "x.pdf"
        p.write_bytes(b"%PDF-1.4")
        content_type, body = _multipart_form_data_file(
            p, add_to_workspaces="my-workspace,other"
        )
        assert "multipart/form-data; boundary=" in content_type
        assert b'name="addToWorkspaces"' in body
        assert b"my-workspace,other" in body
        assert b"Content-Type: application/pdf" in body


@patch.object(AnythingLLMClient, "_post_json", return_value={"success": True})
def test_remove_embeddings_sends_deletes_only(mock_post: object) -> None:
    client = AnythingLLMClient(
        base_url="http://localhost:3001",
        api_key="k",
        workspace_slug="ws",
    )
    out = client.remove_embeddings(["custom-documents/x-json"])
    assert out["success"] is True
    mock_post.assert_called_once()
    # Bound method mock: (path, payload) — no implicit self in call_args[0]
    pos = mock_post.call_args[0]
    assert "/workspace/ws/update-embeddings" in pos[0]
    assert pos[1] == {"adds": [], "deletes": ["custom-documents/x-json"]}


def test_remove_embeddings_empty_noop() -> None:
    client = AnythingLLMClient(
        base_url="http://localhost:3001",
        api_key="k",
        workspace_slug="ws",
    )
    assert client.remove_embeddings([]) == {"success": True, "skipped": True}


@patch.object(AnythingLLMClient, "_post_json")
def test_workspace_chat_posts_chat_endpoint(mock_post: object) -> None:
    mock_post.return_value = {
        "type": "textResponse",
        "textResponse": "hello",
        "close": True,
    }
    client = AnythingLLMClient(
        base_url="http://localhost:3001",
        api_key="k",
        workspace_slug="my-ws",
    )
    out = client.workspace_chat(
        "prompt text", mode="chat", session_id="kms-merge-advisor-1"
    )
    assert out["textResponse"] == "hello"
    mock_post.assert_called_once()
    path, payload = mock_post.call_args[0]
    assert "/workspace/my-ws/chat" in path
    assert payload["message"] == "prompt text"
    assert payload["mode"] == "chat"
    assert payload["sessionId"] == "kms-merge-advisor-1"


def test_anythingllm_chat_text_response() -> None:
    from kms.app.anythingllm_client import anythingllm_chat_text_response

    assert "hi" in anythingllm_chat_text_response(
        {"textResponse": "hi", "type": "textResponse"}
    )
    assert "error" in anythingllm_chat_text_response({"error": "bad"}).lower()
