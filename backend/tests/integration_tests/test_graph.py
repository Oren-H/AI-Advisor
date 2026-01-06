import sys
import types
from typing import Any, AsyncGenerator, Dict

import pytest
from fastapi.testclient import TestClient


def _install_fake_agent_module() -> None:
    """
    Install a fake agent module at 'agent.graph.agent' to bypass import-time issues
    and external dependencies when importing app.main.
    """
    fake_mod = types.ModuleType("agent.graph.agent")

    class _FakeAgent:
        def invoke(self, *_: Any, **__: Any) -> Dict[str, Any]:
            class _Msg:
                def __init__(self, content: str) -> None:
                    self.content = content
            return {"messages": [_Msg("Hello from fake agent")]}

        async def astream_events(self, *_: Any, **__: Any) -> AsyncGenerator[Dict[str, Any], None]:
            # Simulate a minimal token stream then end
            yield {"event": "on_chat_model_stream", "data": {"chunk": types.SimpleNamespace(content="Hi")}}

    def get_course_advisor_agent():
        return _FakeAgent()

    fake_mod.get_course_advisor_agent = get_course_advisor_agent  # type: ignore[attr-defined]
    sys.modules["agent.graph.agent"] = fake_mod


def _patch_lifespan_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    # After importing app, patch cache loaders to avoid filesystem/network
    import backend.app.main as api_mod

    monkeypatch.setattr(api_mod.db_cache, "load_course_df", lambda: None, raising=True)
    monkeypatch.setattr(api_mod.db_cache, "load_course_db", lambda: None, raising=True)
    monkeypatch.setattr(api_mod.db_cache, "load_bulletin_documents", lambda: [], raising=True)
    monkeypatch.setattr(api_mod.db_cache, "load_bulletin_db", lambda: None, raising=True)


def _get_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    _install_fake_agent_module()
    from backend.app.main import app  # type: ignore
    _patch_lifespan_loads(monkeypatch)
    return TestClient(app)


def test_health_check(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _get_client(monkeypatch)
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["graph_ready"] is True


def test_chat_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _get_client(monkeypatch)
    resp = client.post("/chat", json={"message": "hello", "user_profile": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert "conversation_id" in body
    assert body["response"] == "Hello from fake agent"


def test_chat_stream_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _get_client(monkeypatch)
    resp = client.post("/chat/stream", json={"message": "stream please", "user_profile": {}})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
