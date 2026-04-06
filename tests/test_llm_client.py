"""Tests for unified LLM client (kms.app.llm_client)."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest.mock import patch

import pytest

from kms.app.llm_client import LLMClient, create_llm_client


# ── Unit tests (no network) ────────────────────────────────────────


class TestLLMClientInit:
    def test_base_url_strip_trailing_slash(self):
        c = LLMClient(base_url="http://example.com/")
        assert c.base_url == "http://example.com"

    def test_base_url_strip_trailing_v1(self):
        c = LLMClient(base_url="https://api.openai.com/v1")
        assert c.base_url == "https://api.openai.com"

    def test_base_url_strip_trailing_v1_slash(self):
        c = LLMClient(base_url="https://api.openai.com/v1/")
        assert c.base_url == "https://api.openai.com"

    def test_defaults(self):
        c = LLMClient()
        assert c.base_url == "http://localhost:11434"
        assert c.model == "qwen2.5:14b"
        assert c.api_key == ""
        assert c.timeout == 120

    def test_repr(self):
        c = LLMClient(base_url="http://localhost:11434", model="qwen2.5:14b")
        r = repr(c)
        assert "localhost:11434" in r
        assert "qwen2.5:14b" in r


class TestLLMClientHeaders:
    def test_no_api_key(self):
        c = LLMClient(api_key="")
        h = c._headers()
        assert "Authorization" not in h
        assert h["Content-Type"] == "application/json"

    def test_with_api_key(self):
        c = LLMClient(api_key="sk-test123")
        h = c._headers()
        assert h["Authorization"] == "Bearer sk-test123"


# ── Factory tests ──────────────────────────────────────────────────


class TestCreateLLMClient:
    def test_from_llm_section(self):
        cfg = {
            "llm": {
                "base_url": "https://api.openai.com",
                "model": "gpt-4o-mini",
                "api_key_env": "",
            }
        }
        client = create_llm_client(cfg)
        assert client is not None
        assert client.model == "gpt-4o-mini"
        assert "openai" in client.base_url

    def test_fallback_to_ollama_section(self):
        cfg = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:14b",
            }
        }
        client = create_llm_client(cfg)
        assert client is not None
        assert client.model == "qwen2.5:14b"
        assert "11434" in client.base_url

    def test_llm_takes_priority_over_ollama(self):
        cfg = {
            "llm": {
                "base_url": "https://api.groq.com/openai",
                "model": "llama-3.1-70b",
            },
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:14b",
            },
        }
        client = create_llm_client(cfg)
        assert client is not None
        assert "groq" in client.base_url
        assert client.model == "llama-3.1-70b"

    def test_returns_none_when_no_config(self):
        client = create_llm_client({})
        assert client is None

    def test_api_key_from_env(self):
        cfg = {
            "llm": {
                "base_url": "https://api.openai.com",
                "model": "gpt-4o-mini",
                "api_key_env": "TEST_LLM_KEY",
            }
        }
        with patch.dict("os.environ", {"TEST_LLM_KEY": "sk-secret"}):
            client = create_llm_client(cfg)
            assert client is not None
            assert client.api_key == "sk-secret"


# ── Integration tests with mock HTTP server ────────────────────────


class _MockHandler(BaseHTTPRequestHandler):
    """Minimal OpenAI-compatible mock for testing."""

    def do_GET(self):  # noqa: N802
        if "/v1/models" in self.path:
            body = json.dumps(
                {
                    "data": [{"id": "test-model"}, {"id": "qwen2.5:14b"}],
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        payload = json.loads(raw)

        if "/v1/chat/completions" in self.path:
            # Echo back the last user message
            messages = payload.get("messages", [])
            user_msg = messages[-1]["content"] if messages else "empty"
            body = json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": f"Echo: {user_msg}",
                            },
                        }
                    ],
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        pass  # Suppress noisy logs


@pytest.fixture(scope="module")
def mock_llm_server():
    """Start a local HTTP server that mimics the OpenAI API."""
    server = HTTPServer(("127.0.0.1", 0), _MockHandler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


class TestLLMClientIntegration:
    def test_is_available(self, mock_llm_server):
        c = LLMClient(base_url=mock_llm_server, model="qwen2.5:14b")
        assert c.is_available() is True

    def test_is_available_wrong_model(self, mock_llm_server):
        c = LLMClient(base_url=mock_llm_server, model="nonexistent-model")
        assert c.is_available() is False

    def test_generate(self, mock_llm_server):
        c = LLMClient(base_url=mock_llm_server, model="test-model")
        result = c.generate("Hello, world!")
        assert "Echo: Hello, world!" in result

    def test_generate_with_system(self, mock_llm_server):
        c = LLMClient(base_url=mock_llm_server, model="test-model")
        result = c.generate("Test prompt", system="You are a helper")
        assert "Echo: Test prompt" in result

    def test_chat(self, mock_llm_server):
        c = LLMClient(base_url=mock_llm_server, model="test-model")
        result = c.chat(
            [
                {"role": "system", "content": "Be helpful"},
                {"role": "user", "content": "Hi"},
            ]
        )
        assert "Echo: Hi" in result

    def test_unreachable_server(self):
        c = LLMClient(base_url="http://127.0.0.1:1", model="test", timeout=1)
        assert c.is_available() is False
        with pytest.raises(RuntimeError, match="LLM connection error"):
            c.generate("test")
