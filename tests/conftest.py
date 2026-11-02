import pytest

VARIAVEIS_LOCAIS = (
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "OLLAMA_MODEL",
    "OLLAMA_HOST",
    "QA_TIMEOUT_LLM",
    "QA_ORCAMENTO_GERACAO",
    "QA_OLLAMA_KEEP_ALIVE",
)


@pytest.fixture(autouse=True)
def ambiente_isolado(monkeypatch):
    """O .env local é carregado na importação; os testes não podem depender dele."""
    for nome in VARIAVEIS_LOCAIS:
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("QA_AQUECER_OLLAMA", "0")
