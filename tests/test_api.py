import json

import pytest
from fastapi.testclient import TestClient

import backend.servico
from backend import llm
from backend.llm import ErroLLM, ErroTimeout
from backend.main import app
from backend.schemas import Requisicao
from backend.servico import INVALIDO, TIMEOUT, VALIDO, ErroOrcamento, gerar
from sistemas_exemplo import obter

LOGIN = obter("login")
CORPO = {"user_story": LOGIN.user_story, "criterios": LOGIN.criterios, "motor": "Ollama (Local)"}


def req(**kw):
    return Requisicao(**{**CORPO, **kw})


class Relogio:
    """Relógio controlado: cada chamada falsa avança o tempo."""

    def __init__(self):
        self.agora = 0.0

    def __call__(self):
        return self.agora


@pytest.fixture
def cliente():
    return TestClient(app, raise_server_exceptions=False)


def com_provedor(monkeypatch, fake):
    """Faz a API usar um provedor falso com a assinatura real."""
    original = backend.servico.gerar

    def gerar_com_fake(r, chamar=None, relogio=None):
        kwargs = {"relogio": relogio} if relogio else {}
        return original(r, chamar=fake, **kwargs)

    monkeypatch.setattr(backend.servico, "gerar", gerar_com_fake)


# 1.2 falha interna não gera nova chamada
def test_type_error_nao_dispara_segunda_chamada():
    chamadas = []

    def fake(motor, system, msgs, api_key=None, timeout=None):
        chamadas.append(api_key)
        raise TypeError("bug interno")

    with pytest.raises(TypeError):
        gerar(req(motor="Gemini (Cloud)", api_key="minha-chave"), chamar=fake)
    assert chamadas == ["minha-chave"]


def test_type_error_vira_500_com_json(cliente, monkeypatch):
    chamadas = []

    def fake(*a, **k):
        chamadas.append(1)
        raise TypeError("bug interno")

    com_provedor(monkeypatch, fake)
    r = cliente.post("/gerar", json=CORPO)
    assert r.status_code == 500
    assert r.json()["codigo"] == "erro_interno"
    assert "Erro interno" in r.json()["mensagem"]
    assert chamadas == [1]


def test_servico_nao_engole_type_error():
    fonte = open(backend.servico.__file__, encoding="utf-8").read()
    assert "except TypeError" not in fonte


# 2.1 códigos de erro padronizados
def test_422_entrada_invalida_em_texto(cliente):
    r = cliente.post("/gerar", json={**CORPO, "criterios": ""})
    assert r.status_code == 422
    corpo = r.json()
    assert corpo["codigo"] == "entrada_invalida"
    assert isinstance(corpo["mensagem"], str)
    assert "Critérios de Aceite não pode estar vazio" in corpo["mensagem"]


def test_422_campo_ausente(cliente):
    r = cliente.post("/gerar", json={"user_story": "x"})
    assert r.status_code == 422
    assert "criterios" in r.json()["mensagem"]


def test_422_modelo_invalido(cliente, monkeypatch):
    com_provedor(monkeypatch, lambda *a, **k: "lixo")
    r = cliente.post("/gerar", json=CORPO)
    assert r.status_code == 422
    assert r.json()["codigo"] == "modelo_invalido"
    assert "3 tentativas" in r.json()["mensagem"]


def test_502_gemini_sem_api_key(cliente):
    r = cliente.post("/gerar", json={**CORPO, "motor": "Gemini (Cloud)"})
    assert r.status_code == 502
    assert r.json()["codigo"] == "falha_provedor"
    assert "GEMINI_API_KEY" in r.json()["mensagem"]


def test_502_falha_do_provedor(cliente, monkeypatch):
    def fake(*a, **k):
        raise ErroLLM("servidor fora do ar")

    com_provedor(monkeypatch, fake)
    r = cliente.post("/gerar", json=CORPO)
    assert r.status_code == 502
    assert r.json() == {"codigo": "falha_provedor", "mensagem": "servidor fora do ar"}


def test_504_orcamento(cliente, monkeypatch):
    def fake(*a, **k):
        raise ErroTimeout("demorou")

    com_provedor(monkeypatch, fake)
    r = cliente.post("/gerar", json=CORPO)
    assert r.status_code == 504
    assert r.json()["codigo"] == "orcamento_esgotado"


# 2.2 orçamento total
def test_tentativas_lentas_param_antes_do_orcamento(monkeypatch):
    monkeypatch.setenv("QA_ORCAMENTO_GERACAO", "180")
    relogio = Relogio()
    limites = []

    def fake_lento(motor, system, msgs, api_key=None, timeout=None):
        limites.append(timeout)
        relogio.agora += 100  # cada resposta inválida leva 100 s
        return "lixo"

    with pytest.raises(ErroOrcamento, match="180s"):
        gerar(req(), chamar=fake_lento, relogio=relogio)
    assert len(limites) == 2  # a terceira tentativa não cabe no orçamento
    assert limites[1] == pytest.approx(80)  # a segunda só tem o restante do orçamento
    assert relogio.agora <= 180 + 100


def test_tentativa_que_nao_cabe_nao_e_iniciada(monkeypatch):
    monkeypatch.setenv("QA_ORCAMENTO_GERACAO", "100")
    relogio = Relogio()
    chamadas = []

    def fake(*a, **k):
        chamadas.append(1)
        relogio.agora += 98
        return "lixo"

    with pytest.raises(ErroOrcamento):
        gerar(req(), chamar=fake, relogio=relogio)
    assert chamadas == [1]


def test_timeout_registrado_e_proxima_tentativa_valida():
    respostas = iter([ErroTimeout("lento"), json.dumps(LOGIN.modelo)])

    def fake(*a, **k):
        r = next(respostas)
        if isinstance(r, Exception):
            raise r
        return r

    resultado = gerar(req(sistema="login"), chamar=fake)
    assert [t.resultado for t in resultado.tentativas] == [TIMEOUT, VALIDO]
    assert "lento" in resultado.tentativas[0].erro


def test_tentativa_invalida_registrada():
    respostas = iter(["lixo", json.dumps(LOGIN.modelo)])
    resultado = gerar(req(sistema="login"), chamar=lambda *a, **k: next(respostas))
    assert [t.resultado for t in resultado.tentativas] == [INVALIDO, VALIDO]


# 2.3 contrato do /gerar
def test_contrato_gerar(cliente, monkeypatch):
    com_provedor(monkeypatch, lambda *a, **k: json.dumps(LOGIN.modelo))
    r = cliente.post("/gerar", json={**CORPO, "sistema": "login"})
    assert r.status_code == 200
    corpo = r.json()
    assert set(corpo) == {"modelo", "tentativas", "duracao", "historico", "versao_prompt", "provedor", "modelo_llm"}
    assert corpo["modelo"]["estados"][0] == {"id": "SemFalha", "rotulo": "Sem falha", "tipo": "inicial"}
    assert corpo["tentativas"] == 1
    assert corpo["duracao"] >= 0
    assert corpo["historico"][0]["resultado"] == "valido"


# /saude
def test_saude(cliente, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "segredo")
    monkeypatch.setattr(
        llm,
        "verificar_ollama",
        lambda: {"modelo": "llama3.1:8b", "acessivel": True, "disponivel": True, "instalados": [], "mensagem": ""},
    )
    corpo = cliente.get("/saude").json()
    assert corpo["status"] == "ok"
    assert corpo["ollama"]["modelo"] == "llama3.1:8b"
    assert corpo["ollama"]["disponivel"] is True
    assert corpo["gemini"]["chave_configurada"] is True
    assert "segredo" not in json.dumps(corpo)


def test_saude_informa_carregamento(cliente, monkeypatch):
    monkeypatch.setattr(llm.AQUECIMENTO, "situacao", llm.EstadoAquecimento.CARREGANDO)
    monkeypatch.setattr(
        llm,
        "verificar_ollama",
        lambda: {"modelo": "m", "acessivel": True, "disponivel": True, "instalados": ["m"], "mensagem": ""},
    )
    assert cliente.get("/saude").json()["ollama"]["situacao"] == "carregando modelo"


def test_startup_dispara_aquecimento(monkeypatch):
    disparos = []
    monkeypatch.setenv("QA_AQUECER_OLLAMA", "1")
    monkeypatch.setattr(llm, "iniciar_aquecimento", lambda: disparos.append(1))
    with TestClient(app):
        pass
    assert disparos == [1]


def test_startup_sem_aquecimento(monkeypatch):
    disparos = []
    monkeypatch.setattr(llm, "iniciar_aquecimento", lambda: disparos.append(1))
    with TestClient(app):
        pass
    assert disparos == []
