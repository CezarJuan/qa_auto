"""Extração do modelo com LLM (extracao-modelo): prompt, parâmetros do provedor, retry e contrato."""
import json
from types import SimpleNamespace

import ollama
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import backend.servico
from backend import llm
from backend.main import app
from backend.prompts import (
    SYSTEM_PROMPT,
    VERSAO_PROMPT,
    exemplo_resolvido,
    montar_prompt_correcao,
    montar_user_prompt,
)
from backend.schemas import ModeloEstados, Requisicao
from backend.servico import gerar, gerar_modelo
from backend.validacao import ErroModelo, validar_modelo
from sistemas_exemplo import Catalogo, obter

LOGIN = obter("login")
CATALOGO = LOGIN.catalogo


def req(**kw):
    base = dict(user_story=LOGIN.user_story, criterios=LOGIN.criterios, motor="Ollama (Local)", sistema="login")
    return Requisicao(**{**base, **kw})


def sem_criterio_2():
    """Modelo do Login em que nenhuma transição cita o critério 2."""
    modelo = json.loads(json.dumps(LOGIN.modelo))
    for t in modelo["transicoes"]:
        t["criterios"] = [n for n in t["criterios"] if n != 2]
    return json.dumps(modelo)


# ---------------------------------------------------------------- entrada
def test_criterios_sem_numeracao_recusados():
    with pytest.raises(ValidationError, match="Numere"):
        req(criterios="- faz x\n- faz y")


def test_sistema_desconhecido_recusado():
    with pytest.raises(ValidationError, match="fantasma"):
        req(sistema="fantasma")


@pytest.fixture
def sem_llm(monkeypatch):
    def falha(*a, **k):
        raise AssertionError("o LLM não deveria ser chamado")

    monkeypatch.setattr(backend.servico, "gerar", falha)
    return TestClient(app)


def test_api_criterios_sem_numeracao_sem_llm(sem_llm):
    r = sem_llm.post("/gerar", json={"user_story": "x", "criterios": "- a", "motor": "Ollama (Local)"})
    assert r.status_code == 422 and "Numere" in r.text


def test_api_sistema_desconhecido_sem_llm(sem_llm):
    r = sem_llm.post("/gerar", json={"user_story": "x", "criterios": "1. a", "motor": "Ollama (Local)",
                                     "sistema": "fantasma"})
    assert r.status_code == 422 and "fantasma" in r.text


# ---------------------------------------------------------------- 3.1 saída restrita ao esquema
class OllamaFalso:
    chamada: dict = {}

    def __init__(self, host, timeout):
        pass

    def chat(self, model, messages, format, options):
        OllamaFalso.chamada = {"format": format, "options": options}
        return {"message": {"content": "{}"}}


def test_ollama_recebe_esquema_temperatura_zero_e_semente(monkeypatch):
    monkeypatch.setattr(ollama, "Client", OllamaFalso)
    monkeypatch.setenv("QA_SEMENTE", "7")
    llm._chamar_ollama("s", [])
    assert OllamaFalso.chamada["format"] == ModeloEstados.model_json_schema()
    assert OllamaFalso.chamada["options"] == {"temperature": 0, "seed": 7}


def test_semente_padrao():
    assert llm.semente() == 42


def test_gemini_recebe_esquema_e_temperatura_zero(monkeypatch):
    from google import genai

    enviado = {}

    class Modelos:
        def generate_content(self, model, contents, config):
            enviado["config"] = config
            return SimpleNamespace(text="{}")

    class ClienteFalso:
        def __init__(self, api_key, http_options):
            self.models = Modelos()

    monkeypatch.setattr(genai, "Client", ClienteFalso)
    llm._chamar_gemini("s", [{"role": "user", "content": "x"}], api_key="chave")
    config = enviado["config"]
    assert config.temperature == 0
    assert config.seed == 42
    assert config.response_json_schema == ModeloEstados.model_json_schema()
    assert config.response_mime_type == "application/json"


def test_esquema_comeca_pela_analise():
    assert list(llm.esquema_saida()["properties"])[0] == "analise"


# ---------------------------------------------------------------- 3.2 prompt
def test_prompt_versionado():
    assert VERSAO_PROMPT == "extracao-v2"


@pytest.mark.parametrize(
    "secao",
    ["## Linguagem das guardas", "## Linguagem das ações", "## Exemplo resolvido", '"analise"', "e`, `ou`, `não`"],
)
def test_prompt_de_sistema_tem_as_secoes(secao):
    assert secao in SYSTEM_PROMPT


def test_exemplo_resolvido_e_um_modelo_valido():
    modelo = ModeloEstados.model_validate(exemplo_resolvido())
    criterios = "1. Senha correta.\n2. Senha incorreta.\n3. Três erros bloqueiam."
    assert validar_modelo(modelo, criterios) == []
    assert modelo.variaveis and any(t.guarda for t in modelo.transicoes)


def test_exemplo_resolvido_nao_e_caso_de_teste_da_avaliacao():
    """Os canônicos do 5W2H ficam fora do prompt (reservados para o conjunto de teste)."""
    for palavra in ("saque", "cupom", "código de verificação"):
        assert palavra not in SYSTEM_PROMPT.split("## Exemplo resolvido")[1].lower()


def test_prompt_com_criterios_numerados():
    prompt = montar_user_prompt("Como x", "1. a\n2. b\n3. c")
    assert "Critérios de aceite:\n1. a\n2. b\n3. c" in prompt
    assert "Catálogo" not in prompt


def test_prompt_contem_catalogo():
    prompt = montar_user_prompt("us", "1. a", CATALOGO)
    assert f"Estado inicial: {CATALOGO.inicial}" in prompt
    for nome in [*CATALOGO.estados, *CATALOGO.eventos]:
        assert nome in prompt


def test_catalogo_sem_variaveis_proibe_declarar():
    assert "Não declare variáveis" in montar_user_prompt("us", "1. a", CATALOGO)


def test_catalogo_com_variaveis_lista_cada_uma():
    catalogo = Catalogo(estados={"A": "a"}, eventos={"e": "e"}, inicial="A",
                        variaveis={"saldo": "Saldo da conta", "valor": "Valor pedido"})
    prompt = montar_user_prompt("us", "1. a", catalogo)
    assert "- saldo: Saldo da conta" in prompt and "- valor: Valor pedido" in prompt
    assert "Não declare variáveis" not in prompt


# ---------------------------------------------------------------- 3.3 correção guiada
def test_correcao_reenvia_modelo_anterior_e_erros():
    respostas = iter([sem_criterio_2(), json.dumps(LOGIN.modelo)])
    chamadas = []

    def fake(motor, system, msgs, **_):
        chamadas.append([dict(m) for m in msgs])
        return next(respostas)

    assert gerar_modelo(req(), chamar=fake).estados[0].id == "SemFalha"
    assert len(chamadas) == 2
    anterior, correcao = chamadas[1][-2], chamadas[1][-1]
    assert anterior == {"role": "assistant", "content": sem_criterio_2()}
    assert "O critério 2 não está representado" in correcao["content"]
    assert "[criterio_nao_coberto]" in correcao["content"]


def test_correcao_envia_todos_os_erros():
    modelo = json.loads(sem_criterio_2())
    modelo["estados"].append({"id": "Orfao", "rotulo": "Órfão", "tipo": "final"})
    respostas = iter([json.dumps(modelo), json.dumps(LOGIN.modelo)])
    chamadas = []

    def fake(motor, system, msgs, **_):
        chamadas.append(list(msgs))
        return next(respostas)

    gerar_modelo(req(), chamar=fake)
    texto = chamadas[1][-1]["content"]
    assert texto.index("Orfao") < texto.index("critério 2")  # alcançabilidade antes de critérios


def test_erro_de_catalogo_volta_ao_llm():
    fora = json.loads(json.dumps(LOGIN.modelo))
    fora["transicoes"][0]["evento"] = "credenciais"
    respostas = iter([json.dumps(fora), json.dumps(LOGIN.modelo)])
    chamadas = []

    def fake(motor, system, msgs, **_):
        chamadas.append(list(msgs))
        return next(respostas)

    gerar_modelo(req(), chamar=fake)
    assert "senha_incorreta" in chamadas[0][0]["content"]
    assert "credenciais" in chamadas[1][-1]["content"]


def test_limite_de_tentativas_devolve_erros_da_ultima():
    with pytest.raises(ErroModelo) as exc:
        gerar(req(), chamar=lambda *a, **k: sem_criterio_2())
    assert "3 tentativas" in str(exc.value)
    assert [e.codigo for e in exc.value.erros] == ["criterio_nao_coberto"]


def test_prompt_correcao_lista_codigos():
    from backend.validacao import ErroValidacao

    texto = montar_prompt_correcao([ErroValidacao("x", (), "primeiro"), ErroValidacao("y", (), "segundo")])
    assert "- [x] primeiro\n- [y] segundo" in texto


# ---------------------------------------------------------------- 3.4 versão, provedor e modelo
def test_resultado_informa_versao_provedor_e_modelo(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b")
    r = gerar(req(), chamar=lambda *a, **k: json.dumps(LOGIN.modelo))
    assert (r.versao_prompt, r.provedor, r.modelo_llm) == ("extracao-v2", "Ollama (Local)", "qwen2.5:7b")


def test_resultado_com_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-teste")
    r = gerar(req(motor="Gemini (Cloud)"), chamar=lambda *a, **k: json.dumps(LOGIN.modelo))
    assert (r.provedor, r.modelo_llm) == ("Gemini (Cloud)", "gemini-teste")


def com_provedor(monkeypatch, fake):
    original = backend.servico.gerar
    monkeypatch.setattr(backend.servico, "gerar", lambda r, **k: original(r, chamar=fake))


def test_contrato_gerar_com_versao(monkeypatch):
    com_provedor(monkeypatch, lambda *a, **k: json.dumps(LOGIN.modelo))
    corpo = TestClient(app).post("/gerar", json=req().model_dump()).json()
    assert corpo["versao_prompt"] == "extracao-v2"
    assert corpo["provedor"] == "Ollama (Local)"
    assert corpo["modelo_llm"] == "llama3.1:8b"
    assert corpo["modelo"]["analise"]
    assert corpo["historico"][0]["resultado"] == "valido"


def test_422_com_erros_da_ultima_tentativa(monkeypatch):
    com_provedor(monkeypatch, lambda *a, **k: sem_criterio_2())
    r = TestClient(app).post("/gerar", json=req().model_dump())
    assert r.status_code == 422
    corpo = r.json()
    assert corpo["codigo"] == "modelo_invalido"
    assert corpo["erros"] == [{"codigo": "criterio_nao_coberto", "elementos": ["2"],
                               "mensagem": "O critério 2 não está representado em nenhuma transição."}]
