import types
from types import SimpleNamespace
import pytest
import sys


def test_lookup_major_smoke() -> None:
    # Import inside test to avoid import-time failures elsewhere
    try:
        from agent.graph.agent import lookup_major  # type: ignore
    except Exception:
        pytest.skip("agent.graph.agent is not importable in this environment")
        return

    out = lookup_major("Electrical Engineering")
    assert "Major requirements for" in out


def test_lookup_school_wide_requirements_smoke() -> None:
    try:
        from agent.graph.agent import lookup_school_wide_requirements, SchoolWideRequirementInput  # type: ignore
    except Exception:
        pytest.skip("agent.graph.agent is not importable in this environment")
        return

    inp = SchoolWideRequirementInput(query="nontechnical_requirements")
    out = lookup_school_wide_requirements(inp)
    assert isinstance(out, str)
    assert len(out) > 0


def test_lookup_course_uses_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        import agent.graph.agent as agent_mod  # type: ignore
    except Exception:
        pytest.skip("agent.graph.agent is not importable in this environment")
        return

    import pandas as pd

    df = pd.DataFrame(
        [
            {"course_code": "COMS1001", "name": "Intro CS"},
            {"course_code": "ELEN1201", "name": "Circuits"},
        ]
    )

    monkeypatch.setattr(agent_mod.db_cache, "get_course_df", lambda: df, raising=True)
    out = agent_mod.lookup_course("COMS1001")
    assert "course_results" in out
    assert len(out["course_results"]) == 1
    assert out["course_results"][0]["name"] == "Intro CS"


def test_search_courses_calls_filter_and_query(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        import agent.graph.agent as agent_mod  # type: ignore
    except Exception:
        pytest.skip("agent.graph.agent is not importable in this environment")
        return

    called = {"filters": False, "query": False}

    def fake_generate_filters(prompt: str):
        called["filters"] = True
        assert "ml" in prompt
        return {"dept": "COMS"}

    def fake_query(query: str, filters, k: int, unique_courses_only: bool, **_):
        called["query"] = True
        assert filters == {"dept": "COMS"}
        return [{"course_code": "COMS4771"}][:k]

    monkeypatch.setattr(agent_mod, "generate_filters_from_prompt", fake_generate_filters, raising=True)
    monkeypatch.setattr(agent_mod, "query_courses_with_filters", fake_query, raising=True)

    result = agent_mod.search_courses(agent_mod.SearchCoursesInput(query="ml", limit=1, unique_courses_flag=True))
    assert result["total_count"] == 1
    assert result["courses"][0]["course_code"] == "COMS4771"
    assert called["filters"] and called["query"]


def test_search_bulletin_uses_vector_db(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        import agent.graph.agent as agent_mod  # type: ignore
    except Exception:
        pytest.skip("agent.graph.agent is not importable in this environment")
        return

    class _FakeDoc:
        def __init__(self, page_content: str, metadata: dict) -> None:
            self.page_content = page_content
            self.metadata = metadata

    class _FakeDB:
        def similarity_search(self, q: str, k: int = 3):
            return [
                _FakeDoc("reqs", {"page": 1}),
                _FakeDoc("more reqs", {"page": 2}),
            ][:k]

    monkeypatch.setattr(agent_mod.db_cache, "get_bulletin_db", lambda: _FakeDB(), raising=True)

    out = agent_mod.search_bulletin(agent_mod.SearchBulletinInput(agentic_query="EE reqs", limit=2))
    assert "results" in out
    assert len(out["results"]) == 2
    assert out["results"][0]["page_content"] == "reqs"


