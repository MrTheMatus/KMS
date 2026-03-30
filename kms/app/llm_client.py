"""Unified LLM client — OpenAI-compatible chat completions API.

Works with any provider that speaks the OpenAI protocol:
  - Ollama (local):  base_url="http://localhost:11434"
  - OpenAI:          base_url="https://api.openai.com"
  - Groq:            base_url="https://api.groq.com/openai"
  - Together:        base_url="https://api.together.xyz"
  - Mistral:         base_url="https://api.mistral.ai"
  - Azure OpenAI:    base_url="https://<name>.openai.azure.com"
  - Any OpenAI-compatible endpoint
"""

from __future__ import annotations

import json
import logging
import os
from urllib import error, request

_LOG = logging.getLogger(__name__)


class LLMClient:
    """Thin, dependency-free wrapper around /v1/chat/completions."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
        api_key: str = "",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        # Normalise: strip trailing /v1 so we can always append /v1/…
        if self.base_url.endswith("/v1"):
            self.base_url = self.base_url[:-3]
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    # ── public API ──────────────────────────────────

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Convenience: system + user prompt → assistant text."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)

    def chat(self, messages: list[dict[str, str]]) -> str:
        """POST /v1/chat/completions → assistant content string."""
        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        data = self._post("/v1/chat/completions", payload)
        choices = data.get("choices", [])
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", {})
            return msg.get("content", "") if isinstance(msg, dict) else ""
        return ""

    def is_available(self) -> bool:
        """Check connectivity + model presence via /v1/models."""
        try:
            data = self._get("/v1/models")
            models = [m.get("id", "") for m in data.get("data", [])]
            model_base = self.model.split(":")[0]
            return any(model_base in m for m in models)
        except Exception:  # noqa: BLE001
            return False

    # ── HTTP helpers ────────────────────────────────

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=body, headers=self._headers(), method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:500]
            raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"LLM connection error: {exc.reason}") from exc

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        req = request.Request(url, headers=self._headers(), method="GET")
        try:
            with request.urlopen(req, timeout=min(self.timeout, 10)) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:500]
            raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"LLM connection error: {exc.reason}") from exc

    def __repr__(self) -> str:
        return f"LLMClient(base_url={self.base_url!r}, model={self.model!r})"


# ── Factory ────────────────────────────────────────


def create_llm_client(cfg: dict) -> LLMClient | None:
    """Create LLMClient from config.  Prefers ``llm:`` section, falls back to legacy ``ollama:``.

    Returns *None* when no LLM config is present at all.
    """
    llm_cfg: dict = cfg.get("llm") or {}

    # Backward-compat: promote legacy ollama: section
    if not llm_cfg.get("base_url"):
        ollama_cfg = cfg.get("ollama") or {}
        if ollama_cfg.get("base_url"):
            llm_cfg = {
                "base_url": ollama_cfg["base_url"],
                "model": ollama_cfg.get("model", "qwen2.5:14b"),
                "api_key_env": "",
                "timeout": int(ollama_cfg.get("timeout", 120)),
            }

    if not llm_cfg.get("base_url"):
        return None

    base_url = str(llm_cfg["base_url"])
    model = str(llm_cfg.get("model", "qwen2.5:14b"))
    api_key = ""
    key_env = str(llm_cfg.get("api_key_env", "") or "")
    if key_env:
        api_key = os.environ.get(key_env, "")
    timeout = int(llm_cfg.get("timeout", 120))

    return LLMClient(base_url=base_url, model=model, api_key=api_key, timeout=timeout)
