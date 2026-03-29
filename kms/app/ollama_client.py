"""Minimal Ollama API client for local LLM inference."""

from __future__ import annotations

import json
import logging
from urllib import error, request

_LOG = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:14b"


class OllamaClient:
    """Thin wrapper around Ollama REST API (generate endpoint)."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Call /api/generate and return the full response text."""
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        return self._post("/api/generate", payload).get("response", "")

    def chat(self, messages: list[dict[str, str]]) -> str:
        """Call /api/chat and return the assistant message content."""
        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        data = self._post("/api/chat", payload)
        msg = data.get("message", {})
        return msg.get("content", "") if isinstance(msg, dict) else ""

    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            url = f"{self.base_url}/api/tags"
            req = request.Request(url, method="GET")
            with request.urlopen(req, timeout=5) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            # Check if our model is available (match with or without tag)
            model_base = self.model.split(":")[0]
            return any(model_base in m for m in models)
        except Exception:  # noqa: BLE001
            return False

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Ollama connection error: {exc.reason}") from exc
