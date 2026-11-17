import pytest

VARIAVEIS_LOCAIS = (
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "OLLAMA_MODEL",
    "OLLAMA_HOST",
    "QA_TIMEOUT_LLM",
    "QA_ORCAMENTO_GERACAO",
    "QA_OLLAMA_KEEP_ALIVE",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_EFFORT",
    "ANTHROPIC_FALLBACK_RECUSA",
    "OPENAI_COMPAT_BASE_URL",
    "OPENAI_COMPAT_API_KEY",
    "OPENAI_COMPAT_MODEL",
    "OPENAI_COMPAT_MODO_ESQUEMA",
    "OPENAI_COMPAT_DETERMINISTICO",
)


@pytest.fixture(autouse=True)
def ambiente_isolado(monkeypatch):
    """O .env local é carregado na importação; os testes não podem depender dele."""
    for nome in VARIAVEIS_LOCAIS:
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("QA_AQUECER_OLLAMA", "0")
