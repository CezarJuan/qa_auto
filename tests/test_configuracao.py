import re
import threading
from pathlib import Path
from types import SimpleNamespace

import ollama
import pytest

from backend import llm
from backend.llm import TIMEOUT_PADRAO_SEGUNDOS, _chamar_ollama, timeout_segundos
from backend.servico import MARGEM_FRONT_SEGUNDOS, ORCAMENTO_PADRAO_SEGUNDOS, espera_maxima, orcamento_segundos

RAIZ = Path(__file__).resolve().parent.parent


class OllamaFalso:
    """Cliente falso: registra chamadas e simula modelos instalados."""

    usado: dict = {}
    instalados: list[str] = ["llama3.1:8b"]
    acessivel = True
    falha_generate: Exception | None = None

    def __init__(self, host, timeout):
        OllamaFalso.usado.setdefault("clientes", []).append({"host": host, "timeout": timeout})
        OllamaFalso.usado["timeout"] = timeout

    def chat(self, model, **_):
        OllamaFalso.usado["modelo"] = model
        return {"message": {"content": "{}"}}

    def list(self):
        if not OllamaFalso.acessivel:
            raise ConnectionError("conexão recusada")
        return SimpleNamespace(models=[SimpleNamespace(model=m) for m in OllamaFalso.instalados])

    def generate(self, model, prompt, keep_alive):
        OllamaFalso.usado["aquecimento"] = {"modelo": model, "prompt": prompt, "keep_alive": keep_alive}
        if OllamaFalso.falha_generate:
            raise OllamaFalso.falha_generate
        return {}


@pytest.fixture(autouse=True)
def ollama_falso(monkeypatch):
    OllamaFalso.usado = {}
    OllamaFalso.instalados = ["llama3.1:8b"]
    OllamaFalso.acessivel = True
    OllamaFalso.falha_generate = None
    monkeypatch.setattr(ollama, "Client", OllamaFalso)


# tempo limite por chamada
def test_timeout_padrao():
    assert timeout_segundos() == TIMEOUT_PADRAO_SEGUNDOS == 180


def test_timeout_configurado(monkeypatch):
    monkeypatch.setenv("QA_TIMEOUT_LLM", "45")
    _chamar_ollama("s", [])
    assert OllamaFalso.usado["timeout"] == 45


def test_timeout_explicito_prevalece(monkeypatch):
    monkeypatch.setenv("QA_TIMEOUT_LLM", "45")
    _chamar_ollama("s", [], timeout=12)
    assert OllamaFalso.usado["timeout"] == 12


# modelo
def test_modelo_ollama_padrao():
    _chamar_ollama("s", [])
    assert OllamaFalso.usado["modelo"] == "llama3.1:8b"


def test_modelo_ollama_configurado(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "outro")
    _chamar_ollama("s", [])
    assert OllamaFalso.usado["modelo"] == "outro"


# orçamento e espera do front
def test_orcamento_padrao():
    assert orcamento_segundos() == ORCAMENTO_PADRAO_SEGUNDOS


@pytest.mark.parametrize("segundos", ["60", "180", "360"])
def test_front_espera_o_orcamento_mais_margem(monkeypatch, segundos):
    monkeypatch.setenv("QA_ORCAMENTO_GERACAO", segundos)
    assert espera_maxima() == int(segundos) + MARGEM_FRONT_SEGUNDOS


# .env.example
def test_env_example_completo_e_sem_segredo():
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    valores = dict(re.findall(r"^([A-Z_]+)=(.*)$", texto, flags=re.MULTILINE))
    for nome in (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "OLLAMA_MODEL",
        "OLLAMA_HOST",
        "QA_TIMEOUT_LLM",
        "QA_ORCAMENTO_GERACAO",
        "QA_OLLAMA_KEEP_ALIVE",
        "ANTHROPIC_MODEL",
        "OPENAI_COMPAT_MODEL",
    ):
        assert nome in valores, nome
    for chave in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_COMPAT_API_KEY"):
        assert valores[chave].strip() == "", chave
    assert ":" in valores["OLLAMA_MODEL"]  # modelo com tag explícita
    assert valores["ANTHROPIC_MODEL"] == "claude-opus-5-5"


def test_env_example_cobre_variaveis_lidas_pelo_codigo():
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    codigo = "\n".join(p.read_text(encoding="utf-8") for p in (RAIZ / "backend").rglob("*.py"))
    lidas = set(re.findall(r'os\.getenv\("((?:QA|OLLAMA|GEMINI|ANTHROPIC|OPENAI_COMPAT)_[A-Z_]+)"', codigo))
    lidas.add("ANTHROPIC_MODEL")  # lidas por Provedor.modelo_padrao via variavel_modelo
    lidas.add("OPENAI_COMPAT_MODEL")
    lidas.discard("QA_VARIANTE")  # usada só pelo script de teste gerado, não pela aplicação
    lidas.discard("ANTHROPIC_AUTH_TOKEN")  # credencial alternativa da Anthropic, só consultada
    assert lidas, "nenhuma variável encontrada"
    assert {v for v in lidas if f"{v}=" not in texto} == set()


# verificação do modelo configurado
def test_verificacao_modelo_instalado():
    v = llm.verificar_ollama()
    assert v["acessivel"] and v["disponivel"]
    assert v["modelo"] == "llama3.1:8b"


def test_verificacao_modelo_sem_tag_instalada(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")
    v = llm.verificar_ollama()
    assert v["acessivel"] and not v["disponivel"]
    assert "'llama3.1'" in v["mensagem"]
    assert "llama3.1:8b" in v["mensagem"]
    assert v["instalados"] == ["llama3.1:8b"]


def test_verificacao_ollama_desligado():
    OllamaFalso.acessivel = False
    v = llm.verificar_ollama()
    assert not v["acessivel"] and not v["disponivel"]
    assert "inacessível" in v["mensagem"]


# aquecimento
def test_aquecimento_carrega_o_modelo(monkeypatch):
    monkeypatch.setenv("QA_OLLAMA_KEEP_ALIVE", "10m")
    estado = llm.EstadoAquecimento()
    llm.aquecer_ollama(estado)
    assert OllamaFalso.usado["aquecimento"] == {"modelo": "llama3.1:8b", "prompt": "", "keep_alive": "10m"}
    assert estado.situacao == llm.EstadoAquecimento.PRONTO


def test_aquecimento_padrao_30_minutos():
    llm.aquecer_ollama(llm.EstadoAquecimento())
    assert OllamaFalso.usado["aquecimento"]["keep_alive"] == "30m"


def test_aquecimento_ignorado_sem_modelo(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "inexistente:1b")
    estado = llm.EstadoAquecimento()
    llm.aquecer_ollama(estado)
    assert "aquecimento" not in OllamaFalso.usado
    assert estado.situacao == llm.EstadoAquecimento.IGNORADO
    assert "inexistente:1b" in estado.mensagem


def test_aquecimento_com_falha():
    OllamaFalso.falha_generate = RuntimeError("sem memória")
    estado = llm.EstadoAquecimento()
    llm.aquecer_ollama(estado)
    assert estado.situacao == llm.EstadoAquecimento.FALHOU
    assert "sem memória" in estado.mensagem


def test_estado_carregando_durante_o_aquecimento(monkeypatch):
    liberar, chamou = threading.Event(), threading.Event()

    def generate_lento(self, model, prompt, keep_alive):
        chamou.set()
        liberar.wait(5)
        return {}

    monkeypatch.setattr(OllamaFalso, "generate", generate_lento)
    estado = llm.EstadoAquecimento()
    thread = llm.iniciar_aquecimento(estado)
    assert chamou.wait(5)
    assert estado.situacao == llm.EstadoAquecimento.CARREGANDO == "carregando modelo"
    liberar.set()
    thread.join(5)
    assert estado.situacao == llm.EstadoAquecimento.PRONTO
