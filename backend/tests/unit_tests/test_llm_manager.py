import types
import pytest

from typing import Any


class _FakeLLMBase:
    def __init__(self, model: str, api_key: str | None = None, temperature: float = 0.7, **_: Any) -> None:
        self.model = model
        self.api_key = api_key
        self.temperature = temperature

    def with_structured_output(self, *_: Any, **__: Any) -> "_FakeLLMBase":
        return self


class _FakeOpenAI(_FakeLLMBase):
    pass


class _FakeAnthropic(_FakeLLMBase):
    pass


class _FakeCerebras(_FakeLLMBase):
    pass


def _patch_llms(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch LLM classes used inside LLMManager to avoid real SDK usage
    import agent.llm_manager as llm_mod

    monkeypatch.setattr(llm_mod, "ChatOpenAI", _FakeOpenAI, raising=True)
    monkeypatch.setattr(llm_mod, "ChatAnthropic", _FakeAnthropic, raising=True)
    monkeypatch.setattr(llm_mod, "ChatCerebras", _FakeCerebras, raising=True)


def test_get_llm_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_llms(monkeypatch)
    # Provide dummy API keys so construction always succeeds
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("CEREBRAS_API_KEY", "test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    from agent.llm_manager import LLMManager

    mgr = LLMManager()
    a = mgr.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.3)
    b = mgr.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.3)
    c = mgr.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.5)

    assert a is b
    assert a is not c

    info = mgr.get_cache_info()
    assert info["cached_instances"] >= 2
    assert any("openai" in key for key in info["cache_keys"])


def test_anthropic_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_llms(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    from pydantic import BaseModel
    from agent.llm_manager import LLMManager

    class DummySchema(BaseModel):
        value: int

    mgr = LLMManager()
    model = mgr.get_llm(
        model_provider="anthropic",
        model="claude-sonnet-4-5-20250929",
        temperature=0.2,
        use_structured_output=True,
        structured_output_class=DummySchema,
    )
    assert isinstance(model, _FakeAnthropic)


def test_cerebras_disallows_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_llms(monkeypatch)
    monkeypatch.setenv("CEREBRAS_API_KEY", "test")

    from agent.llm_manager import LLMManager

    mgr = LLMManager()
    with pytest.raises(ValueError):
        mgr.get_llm(
            model_provider="cerebras",
            model="llama3.1-8b",
            use_structured_output=True,
        )


