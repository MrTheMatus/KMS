"""Minimal AnythingLLM API client for document sync and workspace chat."""

from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from urllib import error, request


def _multipart_form_data_file(
    file_path: Path,
    *,
    add_to_workspaces: str | None = None,
) -> tuple[str, bytes]:
    """Build multipart/form-data body for POST /api/v1/document/upload.

    AnythingLLM expects multipart with field ``file`` (binary), not JSON paths.
    Optional ``addToWorkspaces`` is a comma-separated list of workspace slugs.
    """
    boundary = f"----KMSFormBoundary{uuid.uuid4().hex}"
    crlf = b"\r\n"
    name = file_path.name.replace('"', "_")
    file_bytes = file_path.read_bytes()
    guessed, _ = mimetypes.guess_type(str(file_path))
    part_mime = (guessed or "application/octet-stream").encode("ascii")

    chunks: list[bytes] = []
    chunks.append(f"--{boundary}".encode("ascii"))
    chunks.append(crlf)
    chunks.append(
        f'Content-Disposition: form-data; name="file"; filename="{name}"'.encode("utf-8")
    )
    chunks.append(crlf)
    chunks.append(b"Content-Type: " + part_mime)
    chunks.append(crlf)
    chunks.append(crlf)
    chunks.append(file_bytes)

    if add_to_workspaces:
        chunks.append(crlf)
        chunks.append(f"--{boundary}".encode("ascii"))
        chunks.append(crlf)
        chunks.append(b'Content-Disposition: form-data; name="addToWorkspaces"')
        chunks.append(crlf)
        chunks.append(crlf)
        chunks.append(add_to_workspaces.encode("utf-8"))

    chunks.append(crlf)
    chunks.append(f"--{boundary}--".encode("ascii"))
    chunks.append(crlf)
    body = b"".join(chunks)
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, body


class AnythingLLMClient:
    def __init__(self, *, base_url: str, api_key: str, workspace_slug: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.workspace_slug = workspace_slug

    def _headers(self, content_type: str = "application/json") -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": content_type,
        }

    def _post_json(self, path: str, payload: dict, *, timeout: int = 120) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=body, headers=self._headers(), method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AnythingLLM HTTP {exc.code}: {detail}") from exc

    def workspace_chat(
        self,
        message: str,
        *,
        mode: str = "chat",
        session_id: str | None = None,
        reset: bool = False,
        timeout: int = 600,
    ) -> dict:
        """POST ``/api/v1/workspace/{slug}/chat`` — uses **workspace default model** from AnythingLLM UI.

        Modes: ``chat`` (LLM + embeddings context), ``query`` (RAG-first), ``automatic``.
        See AnythingLLM API docs on your instance (e.g. ``/api/docs``).
        """
        payload: dict[str, object] = {
            "message": message,
            "mode": mode,
            "attachments": [],
            "reset": reset,
        }
        if session_id is not None:
            payload["sessionId"] = session_id
        return self._post_json(
            f"/api/v1/workspace/{self.workspace_slug}/chat",
            payload,
            timeout=timeout,
        )

    def upload_document_file(
        self,
        file_path: Path,
        *,
        add_to_workspaces: str | None = None,
    ) -> dict:
        """Upload file bytes via multipart/form-data (AnythingLLM requires field ``file``)."""
        path = file_path.resolve()
        if not path.is_file():
            raise FileNotFoundError(str(path))
        content_type, body = _multipart_form_data_file(
            path, add_to_workspaces=add_to_workspaces
        )
        url = f"{self.base_url}/api/v1/document/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": content_type,
        }
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=120) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AnythingLLM HTTP {exc.code}: {detail}") from exc

    def upload_document_reference(self, absolute_file_path: str) -> dict:
        """Backward-compatible alias: upload by path using multipart (not JSON path reference)."""
        return self.upload_document_file(Path(absolute_file_path))

    def update_embeddings(self, doc_locations: list[str]) -> dict:
        return self._post_json(
            f"/api/v1/workspace/{self.workspace_slug}/update-embeddings",
            {"adds": doc_locations, "deletes": []},
        )

    def remove_embeddings(self, doc_locations: list[str]) -> dict:
        """Remove documents from workspace vector index (AnythingLLM ``location`` paths)."""
        if not doc_locations:
            return {"success": True, "skipped": True}
        return self._post_json(
            f"/api/v1/workspace/{self.workspace_slug}/update-embeddings",
            {"adds": [], "deletes": doc_locations},
        )


def anythingllm_chat_text_response(data: dict[str, object]) -> str:
    """Extract user-visible text from ``/workspace/.../chat`` JSON response."""
    err = data.get("error")
    if err:
        return f"[AnythingLLM error: {err}]"
    if data.get("type") == "abort":
        return f"[AnythingLLM abort: {data.get('error') or 'unknown'}]"
    text = data.get("textResponse")
    if text is not None and str(text).strip():
        return str(text).strip()
    return json.dumps(data, ensure_ascii=False)[:2000]
