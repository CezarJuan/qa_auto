"""Casos de referência (reference-cases) e avaliação da extração (extraction-evaluation)."""
import copy
import csv
import json
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from avaliacao.__main__ import main
from avaliacao.alinhamento import alinhar, normalizar
from avaliacao.casos import (
    PASTA_PADRAO,
    ErroCaso,
    carregar_caso,
    carregar_conjunto,
    satisfaz,
    verificar_composicao,
)
from avaliacao.executor import (
    COLUNAS,
    Configuracao,
    ErroVazamento,
    comparar,
    executar,
    verificar_vazamento,
)
from avaliacao.metricas import calcular
from avaliacao.simulacao import simular
from backend.schemas import ModeloEstados
from backend.servico import ErroOrcamento, ResultadoGeracao, Tentativa

CASOS = {c.id: c for c in carregar_conjunto()}


def caso(id_):
    return CASOS[id_]


def propriedade(id_caso, descricao):
    return next(p for p in caso(id_caso).propriedades if p.descricao == descricao)


def saque_errado_do_explore():
    """Modelo que o explore registrou: um único PIN errado já retém o cartão."""
    modelo = copy.deepcopy(caso("saque-atm").gabarito)
    modelo["transicoes"] = [t for t in modelo["transicoes"] if t["evento"] != "pin_invalido"]
    modelo["transicoes"].append({"id": "T9", "de": "AguardandoPin", "evento": "pin_invalido",
                                 "para": "CartaoRetido", "guarda": None, "acoes": [], "criterios": [3]})
    return modelo


def carrinho_errado_do_explore():
    """Modelo que o explore registrou: dá para finalizar com o carrinho vazio."""
    modelo = copy.deepcopy(caso("carrinho").gabarito)
    modelo["transicoes"].append({"id": "T9", "de": "CarrinhoVazio", "evento": "finalizar_compra",
                                 "para": "Pagamento", "guarda": None, "acoes": [], "criterios": [3]})
    return modelo


# ---------------------------------------------------------------- 1.1 esquema e carregador
def escrever(pasta: Path, dados: dict) -> Path:
    caminho = pasta / f"{dados['id']}.yaml"
    caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
    return caminho


def caso_minimo(**kw):
    dados = {
        "id": "porta",
        "dominio": "teste",
        "conjunto": "desenvolvimento",
        "historia": "Como usuário, quero abrir a porta.",
        "criterios": {1: "Abrir leva a Aberta.", 2: "Fechar leva a Fechada."},
        "gabarito": {
            "analise": "1 e 2.",
            "variaveis": [],
            "estados": [{"id": "Fechada", "rotulo": "Fechada", "tipo": "inicial"},
                        {"id": "Aberta", "rotulo": "Aberta", "tipo": "intermediario"},
                        {"id": "Trancada", "rotulo": "Trancada", "tipo": "final"}],
            "transicoes": [
                {"id": "T1", "de": "Fechada", "evento": "abrir", "para": "Aberta", "criterios": [1]},
                {"id": "T2", "de": "Aberta", "evento": "fechar", "para": "Fechada", "criterios": [2]},
                {"id": "T3", "de": "Fechada", "evento": "trancar", "para": "Trancada", "criterios": []},
            ],
        },
        "propriedades": [
            {"criterio": 1, "descricao": "abre", "eventos": [{"evento": "abrir"}], "estado_esperado": "Aberta"},
            {"criterio": 2, "descricao": "fecha", "eventos": [{"evento": "abrir"}, {"evento": "fechar"}],
             "estado_esperado": "Fechada"},
        ],
    }
    dados.update(kw)
    return dados


def test_caso_completo_saque():
    c = caso("saque-atm")
    assert c.gabarito and c.criterios == {1: c.criterios[1], 2: c.criterios[2], 3: c.criterios[3], 4: c.criterios[4]}
    assert {p.criterio for p in c.propriedades} == {1, 2, 3, 4}


def test_caso_minimo_carrega(tmp_path):
    assert carregar_caso(escrever(tmp_path, caso_minimo())).id == "porta"


def test_caso_sem_propriedade_para_um_criterio(tmp_path):
    dados = caso_minimo()
    dados["criterios"][3] = "Trancar."
    dados["gabarito"]["transicoes"][2]["criterios"] = [3]
    with pytest.raises(ErroCaso, match="porta.*critério\\(s\\) 3"):
        carregar_caso(escrever(tmp_path, dados))


def test_gabarito_invalido_e_recusado(tmp_path):
    dados = caso_minimo()
    dados["gabarito"]["transicoes"][0]["para"] = "Fantasma"
    with pytest.raises(ErroCaso, match="gabarito inválido"):
        carregar_caso(escrever(tmp_path, dados))


def test_propriedade_que_o_gabarito_nao_satisfaz(tmp_path):
    dados = caso_minimo()
    dados["propriedades"][0]["estado_esperado"] = "Trancada"
    with pytest.raises(ErroCaso, match="não satisfaz 'abre'"):
        carregar_caso(escrever(tmp_path, dados))


def test_id_igual_ao_nome_do_arquivo(tmp_path):
    caminho = tmp_path / "outro.yaml"
    caminho.write_text(yaml.safe_dump(caso_minimo(), allow_unicode=True), encoding="utf-8")
    with pytest.raises(ErroCaso, match="nome do arquivo"):
        carregar_caso(caminho)


def test_propriedade_sem_expectativa(tmp_path):
    dados = caso_minimo()
    del dados["propriedades"][0]["estado_esperado"]
    with pytest.raises(ErroCaso):
        carregar_caso(escrever(tmp_path, dados))


# ---------------------------------------------------------------- 1.2 / 1.3 conjunto
def test_casos_migrados_usam_a_fonte_unica():
    import exemplos
    from sistemas_exemplo import obter

    for gabarito_id in ("saque-atm", "cupom-promocional", "mfa-bloqueio", "carrinho"):
        assert caso(gabarito_id).gabarito == exemplos.carregar(gabarito_id)["modelo"]
    assert caso("login").gabarito == obter("login").modelo
    assert caso("login").sistema == "login"


def test_composicao_do_conjunto():
    casos = list(CASOS.values())
    verificar_composicao(casos)
    assert len(casos) >= 15 and len({c.dominio for c in casos}) >= 5
    assert {"saque-atm", "cupom-promocional", "mfa-bloqueio"} <= {c.id for c in casos if c.conjunto == "teste"}
    assert caso("login").conjunto == "desenvolvimento"


def test_composicao_insuficiente():
    with pytest.raises(ErroCaso, match="ao menos 15 casos"):
        verificar_composicao([caso("saque-atm")])


def test_filtro_por_conjunto_e_ids():
    assert {c.conjunto for c in carregar_conjunto(conjunto="teste")} == {"teste"}
    assert [c.id for c in carregar_conjunto(ids=["login"])] == ["login"]
    with pytest.raises(ErroCaso, match="fantasma"):
        carregar_conjunto(ids=["fantasma"])


@pytest.mark.parametrize("id_caso", sorted(CASOS))
def test_todo_gabarito_satisfaz_suas_propriedades(id_caso):
    c = caso(id_caso)
    assert all(satisfaz(c.gabarito, p)[0] for p in c.propriedades)


# ---------------------------------------------------------------- 2.1 simulação
def test_pin_errado_uma_vez_nao_retem_o_cartao():
    p = propriedade("saque-atm", "Um PIN errado não retém o cartão")
    assert satisfaz(caso("saque-atm").gabarito, p) == (True, "")
    ok, motivo = satisfaz(saque_errado_do_explore(), p)
    assert not ok and "CartaoRetido" in motivo


def test_tres_pins_retem_nos_dois_modelos():
    p = propriedade("saque-atm", "Três PINs errados retêm o cartão")
    assert satisfaz(caso("saque-atm").gabarito, p)[0]
    assert satisfaz(saque_errado_do_explore(), p)[0]  # só a propriedade de 1 PIN separa os dois


def test_finalizar_carrinho_vazio_e_recusado():
    p = propriedade("carrinho", "Finalizar com o carrinho vazio é recusado")
    assert satisfaz(caso("carrinho").gabarito, p)[0]
    ok, motivo = satisfaz(carrinho_errado_do_explore(), p)
    assert not ok and "deveria ser recusado" in motivo


def test_simulacao_com_contexto_dados_e_acoes():
    sim = simular(caso("saque-atm").gabarito,
                  [("inserir_cartao", {}), ("pin_invalido", {}), ("pin_valido", {}),
                   ("solicitar_saque", {"valor": 120})],
                  {"saldo": 100})
    assert sim.estado == "SaqueRecusado"
    assert [p.aceito for p in sim.passos] == [True, True, True, True]


def test_evento_recusado_mantem_o_estado():
    sim = simular(caso("carrinho").gabarito, [("remover_item", {})])
    assert sim.estado == "CarrinhoVazio" and sim.ultimo_recusado


def test_dados_de_entrada_nao_persistem():
    # valor só vale para o evento em que chegou: a segunda solicitação sem valor não pode ser avaliada
    from avaliacao.simulacao import ErroSimulacao

    gabarito = copy.deepcopy(caso("saque-atm").gabarito)
    gabarito["estados"][4]["tipo"] = "intermediario"  # SaqueRecusado deixa de ser final só para o teste
    gabarito["transicoes"].append({"id": "T9", "de": "SaqueRecusado", "evento": "solicitar_saque",
                                   "para": "SaqueRealizado", "guarda": "valor <= saldo", "acoes": [],
                                   "criterios": []})
    with pytest.raises(ErroSimulacao, match="valor"):
        simular(gabarito, [("inserir_cartao", {}), ("pin_valido", {}),
                           ("solicitar_saque", {"valor": 130}), ("solicitar_saque", {})], {"saldo": 100})


# ---------------------------------------------------------------- 2.2 / 2.3 alinhamento
def extraido_mfa(**renomes):
    modelo = copy.deepcopy(caso("mfa-bloqueio").gabarito)
    for velho, novo in renomes.items():
        for e in modelo["estados"]:
            if e["id"] == velho:
                e["id"] = novo
        for t in modelo["transicoes"]:
            t["de"] = novo if t["de"] == velho else t["de"]
            t["para"] = novo if t["para"] == velho else t["para"]
    return modelo


def test_sinonimo_usuario_logado():
    gabarito = caso("mfa-bloqueio").gabarito
    extraido = extraido_mfa(Autenticado="UsuarioLogado")
    for e in extraido["estados"]:
        e["rotulo"] = e["id"]
    sinonimos = {"estados": {"Autenticado": ["UsuarioLogado"]}}
    assert alinhar(extraido, gabarito, sinonimos).estados["UsuarioLogado"] == "Autenticado"
    assert "UsuarioLogado" in alinhar(extraido, gabarito, {}).nao_mapeados["estados"]


def test_normalizacao():
    assert normalizar("Código_Correto") == normalizar("codigo correto") == normalizar("CODIGO-CORRETO")


def test_alinha_pelo_rotulo():
    extraido = extraido_mfa(Bloqueado="EstadoX")
    rotulo = next(e for e in extraido["estados"] if e["id"] == "EstadoX")
    rotulo["rotulo"] = "Acesso bloqueado"
    assert alinhar(extraido, caso("mfa-bloqueio").gabarito).estados["EstadoX"] == "Bloqueado"


def test_alinhamento_um_para_um():
    extraido = extraido_mfa()
    extraido["estados"].append({"id": "Autenticado2", "rotulo": "Autenticado", "tipo": "final"})
    mapa = alinhar(extraido, caso("mfa-bloqueio").gabarito).estados
    assert list(mapa.values()).count("Autenticado") == 1


def test_alinhamento_semantico_com_embeddings_falsos():
    extraido = extraido_mfa(Bloqueado="Travado")
    for e in extraido["estados"]:
        e["rotulo"] = e["id"]
    vetores = {"Travado": [1.0, 0.0], "Bloqueado": [0.99, 0.05]}

    def embeddings(textos):
        return [vetores.get(t, [0.0, 1.0]) for t in textos]

    assert "Travado" not in alinhar(extraido, caso("mfa-bloqueio").gabarito).estados
    assert alinhar(extraido, caso("mfa-bloqueio").gabarito, embeddings=embeddings).estados["Travado"] == "Bloqueado"


def test_alinhamento_semantico_respeita_o_limiar():
    extraido = extraido_mfa(Bloqueado="Travado")
    for e in extraido["estados"]:
        e["rotulo"] = e["id"]
    vetores = {"Travado": [1.0, 0.0], "Bloqueado": [0.5, 0.86]}
    mapa = alinhar(extraido, caso("mfa-bloqueio").gabarito,
                   embeddings=lambda ts: [vetores.get(t, [0.0, 1.0]) for t in ts]).estados
    assert "Travado" not in mapa


# ---------------------------------------------------------------- 3.1 métricas
def test_estado_extra_precisao_08_recall_10():
    extraido = extraido_mfa()
    extraido["estados"].append({"id": "Inventado", "rotulo": "Inventado", "tipo": "intermediario"})
    q = calcular(extraido, caso("mfa-bloqueio"))
    assert (q.recall_estados, q.precisao_estados) == (1.0, 0.8)


def test_gabarito_contra_si_mesmo_tem_tudo_1():
    q = calcular(caso("cupom-promocional").gabarito, caso("cupom-promocional"))
    assert (q.precisao_estados, q.recall_estados, q.precisao_transicoes, q.recall_transicoes, q.propriedades) == (
        1.0, 1.0, 1.0, 1.0, 1.0)


def test_transicao_com_destino_errado():
    q = calcular(saque_errado_do_explore(), caso("saque-atm"))
    assert q.recall_transicoes < 1.0
    assert q.propriedades < 1.0


def test_guarda_escrita_diferente_nao_penaliza_transicao():
    modelo = copy.deepcopy(caso("saque-atm").gabarito)
    modelo["transicoes"][4]["guarda"] = "saldo >= valor e valor % 20 == 0"
    q = calcular(modelo, caso("saque-atm"))
    assert q.recall_transicoes == 1.0 and q.propriedades == 1.0


def test_evento_nao_mapeado_falha_a_propriedade():
    modelo = copy.deepcopy(caso("saque-atm").gabarito)
    for t in modelo["transicoes"]:
        if t["evento"] == "pin_invalido":
            t["evento"] = "digitar_errado"
    q = calcular(modelo, caso("saque-atm"))
    motivos = {d.motivo for d in q.detalhes_propriedades if not d.satisfeita}
    assert "evento não mapeado: pin_invalido" in motivos


def test_variavel_nao_mapeada_falha_a_propriedade():
    modelo = copy.deepcopy(caso("saque-atm").gabarito)
    modelo["variaveis"][2]["nome"] = "dinheiro"
    for t in modelo["transicoes"]:
        if t["guarda"]:
            t["guarda"] = t["guarda"].replace("saldo", "dinheiro")
    q = calcular(modelo, caso("saque-atm"))
    assert any(d.motivo == "variável não mapeada: saldo" for d in q.detalhes_propriedades)


# ---------------------------------------------------------------- 3.2 – 3.4 executor
def gerador(modelos_por_caso: dict | None = None, falhar: Exception | None = None):
    """Provedor falso: devolve o gabarito do caso (ou o modelo pedido) sem chamar LLM."""
    chamadas = []

    def gerar(req):
        chamadas.append(req)
        if falhar:
            raise falhar
        alvo = next(c for c in CASOS.values() if c.historia == req.user_story)
        modelo = (modelos_por_caso or {}).get(alvo.id, alvo.gabarito)
        return ResultadoGeracao(ModeloEstados.model_validate(modelo), [Tentativa("valido", 1.5)], 1.5)

    gerar.chamadas = chamadas
    return gerar


def rodar(tmp_path, gerar, **kw):
    config = Configuracao(provedor="ollama", modelo="qwen2.5:7b", rodadas=kw.pop("rodadas", 3),
                          conjunto=kw.pop("conjunto", "teste"), casos=kw.pop("casos", None))
    return executar(config, saida=tmp_path, gerar=gerar, agora=datetime(2026, 11, 2, 15, 30),
                    mensagem=lambda *_: None, **kw)


def test_executa_rodadas_por_caso_de_teste(tmp_path):
    gerar = gerador()
    pasta = rodar(tmp_path, gerar)
    teste = [c for c in CASOS.values() if c.conjunto == "teste"]
    assert len(gerar.chamadas) == 3 * len(teste)
    assert pasta.name == "20261102-1530_ollama_qwen2.5-7b_extracao-v2"
    assert {r.motor for r in gerar.chamadas} == {"Ollama (Local)"}


def test_modelo_configurado_durante_a_execucao(tmp_path, monkeypatch):
    import os

    vistos = []
    base = gerador()

    def gerar(req):
        vistos.append(os.environ.get("OLLAMA_MODEL"))
        return base(req)

    rodar(tmp_path, gerar, casos=["saque-atm"], rodadas=1)
    assert vistos == ["qwen2.5:7b"]
    assert os.environ.get("OLLAMA_MODEL") is None  # restaurado depois


def test_subconjunto_com_casos(tmp_path):
    gerar = gerador()
    rodar(tmp_path, gerar, casos=["login", "saque-atm"], conjunto="ambos", rodadas=2)
    assert len(gerar.chamadas) == 4
    assert {r.sistema for r in gerar.chamadas} == {"login", None}


def test_arquivos_de_saida(tmp_path):
    pasta = rodar(tmp_path, gerador(), casos=["saque-atm", "mfa-bloqueio"], rodadas=2)
    assert sorted(p.name for p in (pasta / "rodadas").iterdir()) == [
        "mfa-bloqueio_1.json", "mfa-bloqueio_2.json", "saque-atm_1.json", "saque-atm_2.json"]
    with (pasta / "resumo.csv").open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert list(linhas[0]) == COLUNAS and len(linhas) == 4
    assert {l["propriedades"] for l in linhas} == {"1.0"}
    relatorio = (pasta / "relatorio.md").read_text(encoding="utf-8")
    for secao in ("## Total", "## Por caso", "## Propriedades que mais falharam", "## Elementos não mapeados",
                  "Taxa de validade na primeira tentativa"):
        assert secao in relatorio
    assert "±" in relatorio
    config = json.loads((pasta / "config.json").read_text(encoding="utf-8"))
    assert config["modelo"] == "qwen2.5:7b" and config["casos_avaliados"] == ["mfa-bloqueio", "saque-atm"]


def test_relatorio_lista_propriedades_que_falharam(tmp_path):
    pasta = rodar(tmp_path, gerador({"saque-atm": saque_errado_do_explore()}), casos=["saque-atm"], rodadas=1)
    relatorio = (pasta / "relatorio.md").read_text(encoding="utf-8")
    assert "Um PIN errado não retém o cartão" in relatorio


def test_rodada_com_timeout_tem_metricas_zeradas(tmp_path):
    erro = ErroOrcamento("orçamento esgotado")
    erro.tentativas = [Tentativa("timeout", 180.0, "lento"), Tentativa("timeout", 175.0, "lento")]
    pasta = rodar(tmp_path, gerador(falhar=erro), casos=["saque-atm"], rodadas=1)
    rodada = json.loads((pasta / "rodadas" / "saque-atm_1.json").read_text(encoding="utf-8"))
    assert rodada["timeout"] is True and rodada["valido"] is False
    assert rodada["tentativas"] == 2
    assert rodada["precisao_estados"] == rodada["recall_estados"] == rodada["propriedades"] == 0.0


def test_erro_inesperado_nao_interrompe(tmp_path):
    pasta = rodar(tmp_path, gerador(falhar=RuntimeError("quebrou")), casos=["saque-atm", "login"],
                  conjunto="ambos", rodadas=1)
    assert len(list((pasta / "rodadas").iterdir())) == 2
    assert "RuntimeError: quebrou" in (pasta / "relatorio.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------- 3.3 vazamento
TESTE = [c for c in CASOS.values() if c.conjunto == "teste"]


def test_exemplo_de_prompt_vazado_e_recusado(tmp_path):
    with pytest.raises(ErroVazamento, match="mfa-bloqueio"):
        rodar(tmp_path, gerador(), exemplos_do_prompt=["login", "mfa-bloqueio"])
    assert not list(tmp_path.iterdir())  # nada é gravado


def test_texto_de_caso_de_teste_no_prompt_e_recusado():
    texto = "Exemplo:\n" + caso("pagamento-boleto").criterios[2]
    with pytest.raises(ErroVazamento, match="pagamento-boleto"):
        verificar_vazamento(TESTE, "x", exemplos_do_prompt=[], texto_prompt=texto)


def test_prompt_atual_nao_vaza():
    verificar_vazamento(TESTE, "extracao-v2")


def test_caso_de_desenvolvimento_pode_ser_exemplo():
    verificar_vazamento(TESTE, "x", exemplos_do_prompt=["login", "carrinho"], texto_prompt="")


# ---------------------------------------------------------------- 3.5 comparação
def test_comparar_duas_execucoes(tmp_path):
    a = rodar(tmp_path, gerador(), casos=["saque-atm"], rodadas=2)
    config = Configuracao(provedor="ollama", modelo="llama3.1:8b", rodadas=2, conjunto="teste", casos=["saque-atm"])
    b = executar(config, saida=tmp_path, gerar=gerador({"saque-atm": saque_errado_do_explore()}),
                 agora=datetime(2026, 11, 2, 16, 0), mensagem=lambda *_: None)
    texto = comparar([a, b])
    assert "ollama/qwen2.5:7b/extracao-v2" in texto and "ollama/llama3.1:8b/extracao-v2" in texto
    linha = next(l for l in texto.splitlines() if l.startswith("| Propriedades satisfeitas"))
    celulas = [c.strip() for c in linha.strip("|").split("|")]
    assert celulas[1] == "1.00" and float(celulas[2]) < 1.0 and celulas[3].startswith("-")
    for metrica in ("Precisão de estados", "Recall de transições", "Validade", "Duração (s)"):
        assert metrica in texto


def test_comparar_exige_duas(tmp_path):
    with pytest.raises(ValueError):
        comparar([tmp_path])


# ---------------------------------------------------------------- linha de comando
def test_cli_casos(capsys):
    assert main(["casos"]) == 0
    assert "conjunto válido" in capsys.readouterr().out


def test_cli_comparar(tmp_path, capsys):
    a = rodar(tmp_path, gerador(), casos=["saque-atm"], rodadas=1)
    b = executar(Configuracao(provedor="gemini", modelo="gemini-x", rodadas=1, casos=["saque-atm"]),
                 saida=tmp_path, gerar=gerador(), agora=datetime(2026, 11, 2, 17, 0), mensagem=lambda *_: None)
    saida = tmp_path / "comparacao.md"
    assert main(["comparar", str(a), str(b), "--saida", str(saida)]) == 0
    assert "gemini/gemini-x" in saida.read_text(encoding="utf-8")


def test_cli_caso_desconhecido(capsys):
    assert main(["executar", "--provedor", "ollama", "--modelo", "x", "--casos", "fantasma"]) == 2
    assert "fantasma" in capsys.readouterr().err


def test_benchmark_existe():
    assert PASTA_PADRAO.is_dir() and len(list(PASTA_PADRAO.glob("*.yaml"))) == 15
