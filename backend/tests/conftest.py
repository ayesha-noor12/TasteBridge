import pytest


@pytest.fixture(autouse=True)
def _safe_env(monkeypatch, tmp_path):
    """Tests always run in mock mode with the LLM off and a throwaway cache."""
    monkeypatch.setenv("QLOO_MODE", "mock")
    monkeypatch.setenv("LLM_MODE", "off")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
