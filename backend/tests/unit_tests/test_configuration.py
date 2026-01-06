import agent


def test_agent_package_metadata_exists() -> None:
    assert hasattr(agent, "__version__")
    assert isinstance(agent.__version__, str)
