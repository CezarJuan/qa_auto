"""Registro de provedores, Anthropic e compatível com OpenAI (llm-provider)."""
import json
from types import SimpleNamespace

import anthropic
import httpx
import httpx2
import ollama
import openai
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import backend.servico
from backend import llm, provedores
from backend.main import app
from backend.provedores import claude, openai_compat
from backend.provedores.base import Capacidades, ErroLLM, ErroTimeout, Provedor
from backend.schemas import ModeloEstados, Requisicao
from backend.servico import gerar
from sistemas_exemplo import obter

LOGIN = obter("login")
MODELO_JSON = json.dumps(LOGIN.modelo)


def req(**kw):
    base = dict(user_story=LOGIN.user_story, criterios=LOGIN.criterios, motor="ollama", sistema="login")
    return Requisicao(**{**base, **kw})


# ---------------------------------------------------------------- 1.1 / 1.2 registro
def test_registro_tem_os_quatro_provedores():
    assert list(provedores.REGISTRO) == ["ollama", "gemini", "openai_compat", "anthropic"]
    for p in provedores.REGISTRO.values():
        assert p.nome and isinstance(p.capacidades(p.modelo_padrao() or "x"), Capacidades)


def test_capacidades_por_provedor():
    assert provedores.obter("ollama").capacidades("x").deterministico
    assert provedores.obter("gemini").capacidades("x").deterministico
    anth = provedores.obter("anthropic").capacidades("claude-opus-5-5")
    assert anth.esquema and not anth.temperatura and not anth.semente


class ProvedorFalso(Provedor):
    id = "falso"
    nome = "Falso"
    variavel_modelo = "FALSO_MODEL"
    modelo_fixo = "falso-1"

    def __init__(self):
        self.chamadas = []

    def chamar(self, system, mensagens, *, modelo=None, timeout=None, api_key=None):
        self.chamadas.append({"modelo": self.modelo(modelo), "timeout": timeout})
        return MODELO_JSON


@pytest.fixture
def falso(monkeypatch):
    p = ProvedorFalso()
    monkeypatch.setitem(provedores.REGISTRO, "falso", p)
    return p


def test_chamar_llm_delega_ao_registro(falso):
    assert llm.chamar_llm("falso", "s", [], timeout=5, modelo="falso-2") == MODELO_JSON
    assert falso.chamadas == [{"modelo": "falso-2", "timeout": 5}]


def test_geracao_com_provedor_registrado(falso):
    r = gerar(req(motor="falso"))
    assert (r.provedor, r.modelo_llm) == ("falso", "falso-1")
    assert r.modelo.estados[0].id == "SemFalha"


def test_chamar_llm_provedor_desconhecido():
    with pytest.raises(ErroLLM, match="fantasma"):
        llm.chamar_llm("fantasma", "s", [])


# ---------------------------------------------------------------- 1.3 motor e modelo na requisição
@pytest.mark.parametrize("motor, ident", [("ollama", "ollama"), ("Ollama (Local)", "ollama"),
                                          ("Gemini (Cloud)", "gemini"), ("anthropic", "anthropic"),
                                          (" openai_compat ", "openai_compat")])
def test_motor_aceita_id_e_rotulo_legado(motor, ident):
    assert req(motor=motor).motor == ident


def test_motor_desconhecido():
    with pytest.raises(ValidationError, match="fantasma.*ollama, gemini, openai_compat, anthropic"):
        req(motor="fantasma")


def test_api_motor_desconhecido_sem_llm(monkeypatch):
    def falha(*a, **k):
        raise AssertionError("o LLM não deveria ser chamado")

    monkeypatch.setattr(backend.servico, "gerar", falha)
    r = TestClient(app).post("/gerar", json={**req().model_dump(), "motor": "fantasma"})
    assert r.status_code == 422 and "fantasma" in r.json()["mensagem"]


def test_modelo_vazio_vira_none():
    assert req(modelo="  ").modelo is None
    assert req(modelo=" qwen2.5:7b ").modelo == "qwen2.5:7b"


# ---------------------------------------------------------------- 1.4 modelo por requisição
def test_modelo_da_requisicao_prevalece(monkeypatch):
    usados = []

    class OllamaFalso:
        def __init__(self, host, timeout):
            pass

        def chat(self, model, **_):
            usados.append(model)
            return {"message": {"content": MODELO_JSON}}

    monkeypatch.setattr(ollama, "Client", OllamaFalso)
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    r = gerar(req(modelo="qwen2.5:7b"))
    assert usados == ["qwen2.5:7b"] and r.modelo_llm == "qwen2.5:7b"
    gerar(req())
    assert usados[-1] == "llama3.1:8b"


# ---------------------------------------------------------------- 2. Anthropic
class AnthropicFalso:
    """Cliente falso com a mesma forma de `anthropic.Anthropic`."""

    def __init__(self, resposta=None, erro=None):
        self.pedidos = []
        self.resposta, self.erro = resposta, erro
        self.messages = SimpleNamespace(create=self._criar("padrao"))
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._criar("beta")))

    def _criar(self, rota):
        def criar(**kw):
            self.pedidos.append((rota, kw))
            if self.erro:
                raise self.erro
            return self.resposta
        return criar


def resposta_anthropic(texto=MODELO_JSON, stop_reason="end_turn", categoria=None):
    return SimpleNamespace(
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=texto)],
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category=categoria) if categoria else None,
    )


@pytest.fixture
def cliente_anthropic(monkeypatch):
    falso = AnthropicFalso(resposta_anthropic())
    limites = []

    def fabrica(limite):
        limites.append(limite)
        return falso

    monkeypatch.setattr(claude, "cliente", fabrica)
    falso.limites = limites
    return falso


def test_anthropic_parametros_enviados(cliente_anthropic, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_FALLBACK_RECUSA", "0")
    texto = llm.chamar_llm("anthropic", "sistema", [{"role": "user", "content": "oi"}], timeout=42)
    assert texto == MODELO_JSON
    rota, pedido = cliente_anthropic.pedidos[0]
    assert rota == "padrao"
    assert pedido["model"] == "claude-opus-5-5" and pedido["system"] == "sistema"
    assert pedido["output_config"]["effort"] == "medium"
    assert pedido["output_config"]["format"] == {"type": "json_schema", "schema": anthropic.transform_schema(ModeloEstados)}
    assert "temperature" not in pedido and "seed" not in pedido and "thinking" not in pedido
    assert cliente_anthropic.limites == [42]


def test_anthropic_cliente_sem_novas_tentativas():
    api = claude.cliente(30)
    assert api.max_retries == 0 and api.timeout == 30


def test_anthropic_modelo_e_effort_configuraveis(cliente_anthropic, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("ANTHROPIC_EFFORT", "")
    llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}])
    _, pedido = cliente_anthropic.pedidos[0]
    assert pedido["model"] == "claude-sonnet-5-5" and "effort" not in pedido["output_config"]
    llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}], modelo="claude-haiku-5-5")
    assert cliente_anthropic.pedidos[1][1]["model"] == "claude-haiku-5-5"


# 2.4 fallback de recusa
def test_anthropic_fallback_de_recusa_por_padrao(cliente_anthropic):
    llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}])
    rota, pedido = cliente_anthropic.pedidos[0]
    assert rota == "beta" and pedido["betas"] == ["server-side-fallback-2026-07-01"]
    assert pedido["fallbacks"] == "default"


def test_anthropic_fallback_desligado(cliente_anthropic, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_FALLBACK_RECUSA", "0")
    llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}])
    rota, pedido = cliente_anthropic.pedidos[0]
    assert rota == "padrao" and "fallbacks" not in pedido and "betas" not in pedido


# 2.3 erros
REQ2 = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def status2(codigo):
    return httpx2.Response(codigo, request=REQ2)


@pytest.mark.parametrize(
    "erro, tipo, trecho",
    [
        (anthropic.RateLimitError("x", response=status2(429), body=None), ErroLLM, "limite de taxa"),
        (anthropic.OverloadedError("x", response=status2(529), body=None), ErroLLM, "sobrecarregado"),
        (anthropic.InternalServerError("x", response=status2(500), body=None), ErroLLM, "indisponível"),
        (anthropic.AuthenticationError("x", response=status2(401), body=None), ErroLLM, "ANTHROPIC_API_KEY"),
        (anthropic.BadRequestError("ruim", response=status2(400), body=None), ErroLLM, "erro 400"),
        (anthropic.APIConnectionError(request=REQ2), ErroLLM, "sem conexão"),
        (anthropic.APITimeoutError(request=REQ2), ErroTimeout, "não respondeu"),
    ],
)
def test_anthropic_erros_convertidos(monkeypatch, erro, tipo, trecho):
    monkeypatch.setattr(claude, "cliente", lambda limite: AnthropicFalso(erro=erro))
    with pytest.raises(tipo, match=trecho) as exc:
        llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}])
    assert "Anthropic" in str(exc.value)
    assert type(exc.value) is tipo


def test_anthropic_recusa(monkeypatch):
    falso = AnthropicFalso(resposta_anthropic(texto="", stop_reason="refusal", categoria="cyber"))
    monkeypatch.setattr(claude, "cliente", lambda limite: falso)
    with pytest.raises(ErroLLM, match="recusou.*cyber"):
        llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}])


def test_anthropic_recusa_nao_e_validada_como_modelo(monkeypatch):
    falso = AnthropicFalso(resposta_anthropic(texto="", stop_reason="refusal"))
    monkeypatch.setattr(claude, "cliente", lambda limite: falso)
    with pytest.raises(ErroLLM):
        gerar(req(motor="anthropic"))
    assert len(falso.pedidos) == 1  # falha do provedor encerra, sem nova tentativa de correção


# 2.5 sem credencial
def test_anthropic_sem_credencial(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    erro = TypeError("Could not resolve authentication method. Expected one of api_key...")
    monkeypatch.setattr(claude, "cliente", lambda limite: AnthropicFalso(erro=erro))
    with pytest.raises(ErroLLM, match="ANTHROPIC_API_KEY"):
        llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}])


def test_anthropic_sem_credencial_com_sdk_real(monkeypatch):
    """O SDK falha antes de qualquer requisição de rede quando não há credencial."""
    for nome in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("ANTHROPIC_CONFIG_DIR", "/nao/existe")
    with pytest.raises(ErroLLM, match="ANTHROPIC_API_KEY"):
        llm.chamar_llm("anthropic", "s", [{"role": "user", "content": "x"}], timeout=3)


def test_anthropic_extracao_nao_deterministica(cliente_anthropic):
    r = gerar(req(motor="anthropic"))
    assert r.deterministico is False and r.modelo_llm == "claude-opus-5-5"


# ---------------------------------------------------------------- 3. compatível com OpenAI
class OpenAIFalso:
    def __init__(self, texto=MODELO_JSON, erro=None, recusa=None):
        self.pedidos = []
        self.texto, self.erro, self.recusa = texto, erro, recusa
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._criar))

    def _criar(self, **kw):
        self.pedidos.append(kw)
        if self.erro:
            raise self.erro
        mensagem = SimpleNamespace(content=self.texto, refusal=self.recusa)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)])


@pytest.fixture
def servidor_compat(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "qwen2.5-7b-instruct")
    falso = OpenAIFalso()
    monkeypatch.setattr(openai_compat, "cliente", lambda limite: falso)
    return falso


def test_openai_compat_cliente_real_configurado(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.delenv("OPENAI_COMPAT_API_KEY", raising=False)
    api = openai_compat.cliente(20)
    assert str(api.base_url).rstrip("/") == "http://localhost:1234/v1"
    assert api.max_retries == 0 and api.timeout == 20 and api.api_key == openai_compat.CHAVE_SEM_USO


def test_openai_compat_parametros(servidor_compat):
    assert llm.chamar_llm("openai_compat", "sis", [{"role": "user", "content": "oi"}]) == MODELO_JSON
    pedido = servidor_compat.pedidos[0]
    assert pedido["model"] == "qwen2.5-7b-instruct"
    assert pedido["messages"][0] == {"role": "system", "content": "sis"}
    assert pedido["temperature"] == 0 and pedido["seed"] == 42


@pytest.mark.parametrize(
    "modo, esperado",
    [
        ("json_schema", {"type": "json_schema",
                         "json_schema": {"name": "modelo_estados", "schema": ModeloEstados.model_json_schema(),
                                         "strict": True}}),
        ("json_object", {"type": "json_object"}),
        ("nenhum", None),
    ],
)
def test_openai_compat_modos_de_esquema(servidor_compat, monkeypatch, modo, esperado):
    monkeypatch.setenv("OPENAI_COMPAT_MODO_ESQUEMA", modo)
    llm.chamar_llm("openai_compat", "s", [{"role": "user", "content": "x"}])
    assert servidor_compat.pedidos[0].get("response_format") == esperado


def test_openai_compat_modo_invalido(servidor_compat, monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_MODO_ESQUEMA", "xml")
    with pytest.raises(ErroLLM, match="OPENAI_COMPAT_MODO_ESQUEMA"):
        llm.chamar_llm("openai_compat", "s", [{"role": "user", "content": "x"}])


def test_openai_compat_sem_url_nao_chama(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPAT_BASE_URL", raising=False)
    falso = OpenAIFalso()
    monkeypatch.setattr(openai_compat, "cliente", lambda limite: falso)
    with pytest.raises(ErroLLM, match="OPENAI_COMPAT_BASE_URL"):
        llm.chamar_llm("openai_compat", "s", [{"role": "user", "content": "x"}])
    assert falso.pedidos == []


REQ1 = httpx.Request("POST", "http://localhost:1234/v1/chat/completions")


@pytest.mark.parametrize(
    "erro, tipo, trecho",
    [
        (openai.RateLimitError("x", response=httpx.Response(429, request=REQ1), body=None), ErroLLM, "limite de taxa"),
        (openai.InternalServerError("x", response=httpx.Response(503, request=REQ1), body=None), ErroLLM, "indisponível"),
        (openai.APIConnectionError(request=REQ1), ErroLLM, "sem conexão"),
        (openai.APITimeoutError(request=REQ1), ErroTimeout, "não respondeu"),
    ],
)
def test_openai_compat_erros(monkeypatch, servidor_compat, erro, tipo, trecho):
    monkeypatch.setattr(openai_compat, "cliente", lambda limite: OpenAIFalso(erro=erro))
    with pytest.raises(tipo, match=trecho):
        llm.chamar_llm("openai_compat", "s", [{"role": "user", "content": "x"}])


def test_openai_compat_recusa(monkeypatch, servidor_compat):
    monkeypatch.setattr(openai_compat, "cliente", lambda limite: OpenAIFalso(texto=None, recusa="não posso"))
    with pytest.raises(ErroLLM, match="recusou"):
        llm.chamar_llm("openai_compat", "s", [{"role": "user", "content": "x"}])


def test_openai_compat_determinismo_declarado(monkeypatch, servidor_compat):
    assert gerar(req(motor="openai_compat")).deterministico is False
    monkeypatch.setenv("OPENAI_COMPAT_DETERMINISTICO", "1")
    assert gerar(req(motor="openai_compat")).deterministico is True


def test_openai_compat_nuvem_pela_url(monkeypatch):
    p = provedores.obter("openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "http://localhost:11434/v1")
    assert p.nuvem is False
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "https://openrouter.ai/api/v1")
    assert p.nuvem is True
