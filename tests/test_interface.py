from pathlib import Path

import pytest
import requests
from streamlit.testing.v1 import AppTest

import demo_data
import exemplos
from backend.servico import espera_maxima
from sistemas_exemplo import obter

APP = str(Path(__file__).resolve().parent.parent / "app.py")
SAQUE = "Saque em caixa eletrônico"
LOGIN = "Login bancário"
AVISO_DEMO = "Demonstração: modelo de referência, sem LLM"


class RespostaFalsa:
    def __init__(self, dados=None, status_code=200, texto=None):
        self.dados = dados
        self.status_code = status_code
        self.text = texto if texto is not None else ""

    def json(self):
        if self.dados is None:
            raise requests.JSONDecodeError("Expecting value", self.text, 0)
        return self.dados


def resposta_gerar(modelo, tentativas=1, duracao=1.5):
    return RespostaFalsa({"modelo": modelo, "tentativas": tentativas, "duracao": duracao, "historico": []})


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    return at


@pytest.fixture
def backend_falso(monkeypatch):
    """Substitui o POST ao backend; guarda o que foi enviado e o timeout usado."""
    estado = {"resposta": resposta_gerar(obter("login").modelo), "enviado": {}, "chamadas": 0}

    def post(url, json, timeout):
        estado["chamadas"] += 1
        estado["enviado"] = dict(json)
        estado["timeout"] = timeout
        if isinstance(estado["resposta"], Exception):
            raise estado["resposta"]
        return estado["resposta"]

    monkeypatch.setattr(requests, "post", post)
    return estado


def modo_real(at):
    at.toggle[0].set_value(False).run()
    return at


def gerar(at):
    at.button(key="gerar").click().run()
    assert not at.exception
    return at


def codigos(at):
    return "\n".join(c.value for c in at.code)


def textos(elementos):
    return "\n".join(e.value for e in elementos)


def downloads(at):
    return at.get("download_button")


# dados
def test_exemplos_sem_artefatos_fixos():
    for exemplo in demo_data.EXEMPLOS.values():
        assert set(exemplo) == {"sistema", "gabarito", "user_story", "criterios"}
        assert demo_data.modelo_de_referencia(next(n for n, e in demo_data.EXEMPLOS.items() if e is exemplo))
    assert "assert True" not in Path(demo_data.__file__).read_text(encoding="utf-8")


def test_exemplos_canonicos_disponiveis():
    nomes = set(demo_data.EXEMPLOS)
    assert {LOGIN, SAQUE, "Cupom Promocional", "Autenticação MFA", "Carrinho de Compras"} <= nomes


# 3.5 exemplos em 1 clique
@pytest.mark.parametrize("nome", list(demo_data.EXEMPLOS))
def test_carregar_exemplo_preenche_sem_gerar(app, backend_falso, nome):
    app.selectbox(key="exemplo").select(nome).run()
    assert not app.exception
    exemplo = demo_data.EXEMPLOS[nome]
    assert app.text_area(key="user_story").value == exemplo["user_story"]
    assert app.text_area(key="criterios").value == exemplo["criterios"]
    assert app.selectbox(key="sistema_alvo").value == (exemplo["sistema"] or "")
    assert "resultado" not in app.session_state
    assert backend_falso["chamadas"] == 0


def test_exemplo_continua_editavel(app):
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    app.text_area(key="criterios").set_value("1. outro").run()
    assert app.text_area(key="criterios").value == "1. outro"


# seletor
def test_carregar_exemplo_seleciona_sistema(app):
    assert app.selectbox(key="sistema_alvo").value == "login"
    app.selectbox(key="exemplo").select(SAQUE).run()
    assert app.selectbox(key="sistema_alvo").value == "saque"


# artefatos
def test_demo_gera_artefatos_do_modelo_de_referencia(app):
    gerar(app)
    assert "Feature: Login bancário" in codigos(app)
    assert 'scenarios("login.feature")' in codigos(app)
    assert len(downloads(app)) == 2
    assert app.session_state["resultado"]["artefatos"].nome_script == "test_login.py"


# 2.3 novo corpo do /gerar
def test_modo_real_com_backend_falso(app, backend_falso):
    backend_falso["resposta"] = resposta_gerar(obter("login").modelo, tentativas=2, duracao=42.0)
    modo_real(app)
    gerar(app)
    assert backend_falso["enviado"]["sistema"] == "login"
    assert "Feature: Login bancário" in codigos(app)
    assert len(downloads(app)) == 2
    assert app.session_state["resultado"]["tentativas"] == 2
    assert any("2 tentativa(s) em 42.0s" in c.value for c in app.caption)


def test_modo_real_sem_sistema_gera_esqueleto(app, backend_falso):
    modo_real(app)
    app.selectbox(key="sistema_alvo").select("").run()
    gerar(app)
    assert backend_falso["enviado"]["sistema"] is None
    assert any("esqueletos" in i.value for i in app.info)
    assert 'scenarios("cenarios.feature")' in codigos(app)
    assert not [b for b in app.button if b.key == "executar"]


def test_exemplo_usa_pipeline_real_fora_da_demo(app, backend_falso):
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    modo_real(app)
    gerar(app)
    assert backend_falso["chamadas"] == 1
    assert backend_falso["enviado"]["criterios"] == demo_data.EXEMPLOS["Cupom Promocional"]["criterios"]


# 2.4 espera e tratamento de erros
def test_front_espera_o_orcamento(app, backend_falso, monkeypatch):
    monkeypatch.setenv("QA_ORCAMENTO_GERACAO", "100")
    modo_real(app)
    gerar(app)
    assert backend_falso["timeout"] == espera_maxima() == 115


def test_erro_500_em_texto_puro(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa(status_code=500, texto="Internal Server Error")
    modo_real(app)
    gerar(app)
    assert "Erro interno no servidor (status 500)" in textos(app.error)
    assert "resultado" not in app.session_state


def test_erro_json_mostra_mensagem(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa(
        {"codigo": "orcamento_esgotado", "mensagem": "O orçamento de 180s se esgotou."}, status_code=504
    )
    modo_real(app)
    gerar(app)
    assert "O orçamento de 180s se esgotou. (status 504)" in textos(app.error)


def test_backend_desligado(app, backend_falso):
    backend_falso["resposta"] = requests.ConnectionError("recusado")
    modo_real(app)
    gerar(app)
    erro = textos(app.error)
    assert "indisponível" in erro and "uvicorn backend.main:app" in erro


def test_resposta_200_inesperada(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa(texto="<html>proxy</html>")
    modo_real(app)
    gerar(app)
    assert "formato inesperado" in textos(app.error)


# 3.1 numeração dos critérios
def test_criterios_sem_numero_sao_numerados_e_enviados(app, backend_falso):
    modo_real(app)
    app.text_area(key="criterios").set_value("Senha correta entra\nSenha errada mostra erro\nTrês erros bloqueiam").run()
    previa = textos(app.markdown)
    assert "1\\. Senha correta entra" in previa and "3\\. Três erros bloqueiam" in previa
    gerar(app)
    assert backend_falso["enviado"]["criterios"] == (
        "1. Senha correta entra\n2. Senha errada mostra erro\n3. Três erros bloqueiam"
    )


# 3.3 importação de arquivo e edição posterior
ARQUIVO = (
    "# História\nComo cliente, quero sacar.\n\n# Critérios\n"
    "1. cada tentativa inválida incrementa o contador\n2. três erros retêm o cartão\n"
).encode("utf-8")


def test_importacao_preenche_os_campos(app):
    app.get("file_uploader")[0].upload("req.md", ARQUIVO, "text/markdown").run()
    assert not app.exception
    assert app.text_area(key="user_story").value == "Como cliente, quero sacar."
    assert "1. cada tentativa inválida incrementa o contador" in app.text_area(key="criterios").value
    assert "req.md" in textos(app.success)


def test_edicao_apos_importar_prevalece(app, backend_falso):
    modo_real(app)
    app.get("file_uploader")[0].upload("req.md", ARQUIVO, "text/markdown").run()
    app.text_area(key="criterios").set_value("1. cada tentativa inválida incrementa\n2. critério editado").run()
    gerar(app)
    assert backend_falso["enviado"]["criterios"] == "1. cada tentativa inválida incrementa\n2. critério editado"
    assert app.text_area(key="criterios").value.endswith("critério editado")


def test_arquivo_sem_historia(app):
    app.get("file_uploader")[0].upload("req.md", b"# Criterios\n1. a\n", "text/markdown").run()
    erro = textos(app.error)
    assert "história de usuário não foi encontrada" in erro
    assert "# História" in erro  # mostra o formato aceito
    assert app.text_area(key="user_story").value == obter("login").user_story


# 3.4 campos obrigatórios e limite
def test_envio_sem_criterios_bloqueado(app, backend_falso):
    modo_real(app)
    app.text_area(key="criterios").set_value("   ").run()
    gerar(app)
    assert "critérios de aceite são obrigatórios" in textos(app.error)
    assert backend_falso["chamadas"] == 0


def test_envio_acima_do_limite_bloqueado(app, backend_falso):
    modo_real(app)
    app.text_area(key="criterios").set_value("1. " + "x" * 2097).run()
    gerar(app)
    erro = textos(app.error)
    assert "2100" in erro and "2000" in erro
    assert backend_falso["chamadas"] == 0


# 4.2 código Mermaid copiável
def test_codigo_mermaid_disponivel(app):
    gerar(app)
    assert "stateDiagram-v2" in codigos(app)
    assert "(CA3)" in codigos(app)


# 5.1 aviso da demonstração
def test_aviso_demo_em_todas_as_abas(app):
    gerar(app)
    assert sum(AVISO_DEMO in i.value for i in app.info) == 6


def test_modo_real_sem_aviso_demo(app, backend_falso):
    modo_real(app)
    gerar(app)
    assert not any(AVISO_DEMO in i.value for i in app.info)


def test_rotulo_da_latencia_segue_a_origem_do_resultado(app):
    gerar(app)
    app.toggle[0].set_value(False).run()
    html = " ".join(m.value for m in app.markdown)
    assert "Latência (Demo)" in html and "Latência (Real)" not in html


# 5.2 demonstração restrita
def test_demo_recusa_texto_livre(app):
    app.text_area(key="user_story").set_value("Como cliente, quero pagar um boleto.").run()
    app.text_area(key="criterios").set_value("1. Boleto vencido é recusado.").run()
    gerar(app)
    aviso = textos(app.warning)
    assert "texto livre" in aviso and "Desative" in aviso
    assert "resultado" not in app.session_state
    assert not app.get("download_button")


def test_demo_recusa_exemplo_editado(app):
    app.text_area(key="criterios").set_value(obter("login").criterios + "\n4. Novo critério.").run()
    gerar(app)
    assert "editado" in textos(app.warning)
    assert "resultado" not in app.session_state


def test_demo_recusa_exemplo_sem_referencia(monkeypatch):
    monkeypatch.setitem(demo_data.EXEMPLOS, "Boleto", {
        "sistema": None, "gabarito": None, "user_story": "Como cliente, quero pagar um boleto.",
        "criterios": "1. Boleto vencido é recusado.",
    })
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    at.selectbox(key="exemplo").select("Boleto").run()
    gerar(at)
    assert "não tem modelo de referência" in textos(at.warning)
    assert "resultado" not in at.session_state


# 4.4 gabaritos na demonstração
@pytest.mark.parametrize("nome, gabarito", [("Cupom Promocional", "cupom-promocional"),
                                            ("Autenticação MFA", "mfa-bloqueio"),
                                            ("Carrinho de Compras", "carrinho")])
def test_demo_exibe_gabarito_como_esqueleto(app, nome, gabarito):
    app.selectbox(key="exemplo").select(nome).run()
    gerar(app)
    assert not app.warning
    assert app.session_state["resultado"]["modelo"] == exemplos.carregar(gabarito)["modelo"]
    assert sum(AVISO_DEMO in i.value for i in app.info) == 6
    assert any("esqueletos" in i.value for i in app.info)
    assert 'scenarios("cenarios.feature")' in codigos(app)


# 4.3 análise, variáveis e tentativas
def test_aba_analise_mostra_analise_e_variaveis(app):
    app.selectbox(key="exemplo").select("Cupom Promocional").run()
    gerar(app)
    modelo = app.session_state["resultado"]["modelo"]
    assert any(modelo["analise"] in m.value for m in app.markdown)
    tabelas = [d.value for d in app.dataframe]
    variaveis = next(t for t in tabelas if "Categoria" in t.columns)
    assert list(variaveis["Nome"]) == ["data_atual", "validade", "valor_compra", "cupom_usado"]


def test_aba_analise_sem_variaveis(app):
    gerar(app)
    assert any("não declara variáveis" in c.value for c in app.caption)


def test_tentativas_do_modo_real(app, backend_falso):
    backend_falso["resposta"] = RespostaFalsa({
        "modelo": obter("login").modelo, "tentativas": 2, "duracao": 9.0,
        "historico": [{"resultado": "invalido", "duracao": 4.0, "erro": "critério 2 sem transição"},
                      {"resultado": "valido", "duracao": 5.0, "erro": ""}],
    })
    modo_real(app)
    gerar(app)
    tentativas = next(d.value for d in app.dataframe if "Tentativa" in d.value.columns)
    assert list(tentativas["Resultado"]) == ["❌ Inválido", "✅ Válido"]
    assert "critério 2 sem transição" in list(tentativas["Erros"])


def test_transicoes_mostram_guarda_e_acoes(app):
    app.selectbox(key="exemplo").select("Autenticação MFA").run()
    gerar(app)
    transicoes = next(d.value for d in app.dataframe if "Guarda" in d.value.columns)
    assert "tentativas < 2" in list(transicoes["Guarda"])
    assert "tentativas += 1" in list(transicoes["Ações"])


def test_demo_exibe_exemplo_nao_editado(app):
    gerar(app)
    assert not app.warning
    assert app.session_state["resultado"]["modelo"] == obter("login").modelo


# execução
def test_executar_mostra_veredito_e_nova_geracao_descarta(app):
    gerar(app)
    app.button(key="executar").click().run()
    assert not app.exception
    assert any("Bug detectado" in s.value for s in app.success)
    assert len(app.dataframe) >= 3  # transições + duas variantes
    assert any("Esperado ContaBloqueada, obtido DuasFalhas" in m.value for m in app.markdown)

    gerar(app)
    assert "execucao" not in app.session_state
    assert not app.success


def test_executar_saque(app):
    app.selectbox(key="exemplo").select(SAQUE).run()
    gerar(app)
    app.button(key="executar").click().run()
    assert any("Bug detectado" in s.value for s in app.success)
