"""Formato do modelo de estados (state-model) e regras de validação (state-model-validation)."""
import copy

import pytest
from pydantic import ValidationError

import exemplos
from backend.schemas import ModeloEstados, Variavel
from backend.validacao import (
    ALCANCABILIDADE,
    CRITERIOS,
    ErroModelo,
    validar_modelo,
    validar_resposta,
)
from sistemas_exemplo import SISTEMAS, obter

CRITERIOS_3 = "1. a\n2. b\n3. c"


def base():
    """Modelo mínimo válido para 3 critérios, alterado em cada teste."""
    return {
        "analise": "Critérios 1, 2 e 3 identificados.",
        "variaveis": [{"nome": "tentativas", "tipo": "inteiro", "categoria": "estado", "valor_inicial": 0}],
        "estados": [
            {"id": "Inicio", "rotulo": "Início", "tipo": "inicial"},
            {"id": "AguardandoPin", "rotulo": "Aguardando PIN", "tipo": "intermediario"},
            {"id": "CartaoRetido", "rotulo": "Cartão retido", "tipo": "final"},
            {"id": "Autenticado", "rotulo": "Autenticado", "tipo": "final"},
        ],
        "transicoes": [
            {"id": "T1", "de": "Inicio", "evento": "inserir_cartao", "para": "AguardandoPin", "criterios": [1]},
            {"id": "T2", "de": "AguardandoPin", "evento": "pin_valido", "para": "Autenticado", "criterios": [2]},
            {"id": "T3", "de": "AguardandoPin", "evento": "pin_invalido", "para": "AguardandoPin",
             "guarda": "tentativas < 2", "acoes": ["tentativas += 1"], "criterios": [3]},
            {"id": "T4", "de": "AguardandoPin", "evento": "pin_invalido", "para": "CartaoRetido",
             "guarda": "tentativas >= 2", "acoes": ["tentativas += 1"], "criterios": [3]},
        ],
    }


def erros(dados, criterios=CRITERIOS_3, catalogo=None):
    return validar_modelo(ModeloEstados.model_validate(dados), criterios, catalogo)


def codigos(dados, **kw):
    return [e.codigo for e in erros(dados, **kw)]


def estado(dados, id_):
    return next(e for e in dados["estados"] if e["id"] == id_)


def transicao(dados, id_):
    return next(t for t in dados["transicoes"] if t["id"] == id_)


def test_base_valida():
    assert erros(base()) == []


# ---------------------------------------------------------------- formato (state-model)
def test_analise_e_o_primeiro_campo():
    assert list(ModeloEstados.model_fields)[0] == "analise"
    assert list(ModeloEstados.model_json_schema()["properties"])[0] == "analise"


def test_estado_com_rotulo_acentuado():
    m = ModeloEstados.model_validate(base())
    retido = next(e for e in m.estados if e.id == "CartaoRetido")
    assert (retido.rotulo, retido.tipo) == ("Cartão retido", "final")


@pytest.mark.parametrize("id_", ["Com itens", "ValidaçãoPin", "comItens", "1Estado", "Fim-Ok", ""])
def test_id_de_estado_invalido(id_):
    dados = base()
    estado(dados, "Autenticado")["id"] = id_
    with pytest.raises(ValidationError):
        ModeloEstados.model_validate(dados)


@pytest.mark.parametrize("evento", ["PinValido", "pin valido", "pin-valido", "ação"])
def test_evento_fora_de_snake_case(evento):
    dados = base()
    transicao(dados, "T2")["evento"] = evento
    with pytest.raises(ValidationError):
        ModeloEstados.model_validate(dados)


def test_variavel_de_estado_sem_valor_inicial():
    with pytest.raises(ValidationError, match="valor_inicial"):
        Variavel(nome="tentativas", tipo="inteiro", categoria="estado")


def test_valor_inicial_de_tipo_errado():
    with pytest.raises(ValidationError, match="não é do tipo"):
        Variavel(nome="ativo", tipo="booleano", categoria="estado", valor_inicial=3)


@pytest.mark.parametrize(
    "variavel",
    [
        {"nome": "valor", "tipo": "decimal", "categoria": "entrada"},
        {"nome": "saldo", "tipo": "decimal", "categoria": "contexto"},
        {"nome": "validade", "tipo": "data", "categoria": "contexto", "valor_inicial": "2026-12-31"},
    ],
)
def test_variaveis_de_entrada_e_contexto(variavel):
    assert Variavel.model_validate(variavel).nome == variavel["nome"]


def test_nome_de_variavel_em_snake_case():
    with pytest.raises(ValidationError):
        Variavel(nome="Saldo", tipo="decimal", categoria="contexto")


def test_lista_de_variaveis_pode_ser_vazia():
    dados = base()
    dados["variaveis"] = []
    for t in dados["transicoes"]:
        t.pop("guarda", None), t.pop("acoes", None)
    dados["transicoes"].pop()  # sem guardas, a T4 deixaria o par ambíguo
    assert ModeloEstados.model_validate(dados).variaveis == []


def test_transicao_com_guarda_acao_e_criterios():
    t = ModeloEstados.model_validate(base()).transicoes[2]
    assert (t.de, t.evento, t.para, t.guarda, t.acoes, t.criterios) == (
        "AguardandoPin", "pin_invalido", "AguardandoPin", "tentativas < 2", ["tentativas += 1"], [3]
    )


def test_transicao_auxiliar_tem_criterios_vazios():
    dados = base()
    transicao(dados, "T1")["criterios"] = []
    dados["transicoes"][1]["criterios"] = [1, 2]
    m = ModeloEstados.model_validate(dados)
    assert m.transicoes[0].criterios == []


# ---------------------------------------------------------------- inicial e finais
def test_dois_estados_iniciais():
    dados = base()
    estado(dados, "AguardandoPin")["tipo"] = "inicial"
    (erro,) = [e for e in erros(dados) if e.codigo == "inicial_nao_unico"]
    assert "Inicio" in erro.mensagem and "AguardandoPin" in erro.mensagem


def test_laco_em_estado_final():
    dados = base()
    dados["transicoes"].append({"id": "T5", "de": "CartaoRetido", "evento": "pin_valido", "para": "CartaoRetido"})
    (erro,) = [e for e in erros(dados) if e.codigo == "final_com_saida"]
    assert "'CartaoRetido' é final" in erro.mensagem


def test_nenhum_estado_final():
    dados = base()
    for e in dados["estados"]:
        if e["tipo"] == "final":
            e["tipo"] = "intermediario"
    assert "sem_estado_final" in codigos(dados)


# ---------------------------------------------------------------- alcançabilidade e término
def test_estado_inalcancavel():
    dados = base()
    dados["estados"].append({"id": "Bloqueado", "rotulo": "Bloqueado", "tipo": "final"})
    (erro,) = [e for e in erros(dados) if e.codigo == "estado_inalcancavel"]
    assert "'Bloqueado'" in erro.mensagem and "inalcançável" in erro.mensagem


def test_beco_sem_saida():
    dados = base()
    dados["estados"].append({"id": "Processando", "rotulo": "Processando", "tipo": "intermediario"})
    dados["transicoes"].append({"id": "T5", "de": "Inicio", "evento": "processar", "para": "Processando"})
    (erro,) = [e for e in erros(dados) if e.codigo == "sem_caminho_ao_final"]
    assert "'Processando' é um beco sem saída" in erro.mensagem


def test_ciclo_sem_caminho_ao_final():
    dados = base()
    dados["estados"] += [{"id": "A", "rotulo": "A", "tipo": "intermediario"},
                         {"id": "B", "rotulo": "B", "tipo": "intermediario"}]
    dados["transicoes"] += [{"id": "T5", "de": "Inicio", "evento": "ir", "para": "A"},
                            {"id": "T6", "de": "A", "evento": "ir", "para": "B"},
                            {"id": "T7", "de": "B", "evento": "ir", "para": "A"}]
    assert codigos(dados).count("sem_caminho_ao_final") == 2


# ---------------------------------------------------------------- referências
def test_variavel_nao_declarada():
    dados = base()
    transicao(dados, "T2")["guarda"] = "saldo >= 0"
    (erro,) = [e for e in erros(dados) if e.codigo == "variavel_nao_declarada"]
    assert "T2" in erro.mensagem and "'saldo'" in erro.mensagem


def test_estado_de_destino_inexistente():
    dados = base()
    transicao(dados, "T2")["para"] = "Finalizado"
    (erro,) = [e for e in erros(dados) if e.codigo == "estado_inexistente"]
    assert "T2" in erro.mensagem and "'Finalizado'" in erro.mensagem


def test_guarda_com_chamada_de_funcao():
    dados = base()
    transicao(dados, "T2")["guarda"] = "validar(tentativas)"
    assert "guarda_invalida" in codigos(dados)


def test_acao_sobre_variavel_de_entrada():
    dados = base()
    dados["variaveis"].append({"nome": "valor", "tipo": "decimal", "categoria": "entrada"})
    transicao(dados, "T2")["acoes"] = ["valor = 0"]
    (erro,) = [e for e in erros(dados) if e.codigo == "acao_sobre_nao_estado"]
    assert "entrada" in erro.mensagem


def test_acao_sobre_variavel_de_contexto():
    dados = base()
    dados["variaveis"] += [{"nome": "saldo", "tipo": "decimal", "categoria": "contexto"},
                           {"nome": "valor", "tipo": "decimal", "categoria": "entrada"}]
    transicao(dados, "T2")["acoes"] = ["saldo -= valor"]
    assert "acao_sobre_nao_estado" in codigos(dados)


def test_tipos_incompativeis_na_guarda():
    dados = base()
    dados["variaveis"].append({"nome": "ativo", "tipo": "booleano", "categoria": "contexto"})
    transicao(dados, "T2")["guarda"] = "ativo > 1"
    assert "tipo_incompativel" in codigos(dados)


def test_atribuicao_de_tipo_incompativel():
    dados = base()
    dados["variaveis"].append({"nome": "valor", "tipo": "decimal", "categoria": "entrada"})
    transicao(dados, "T2")["acoes"] = ["tentativas = valor"]
    assert "tipo_incompativel" in codigos(dados)


# ---------------------------------------------------------------- critérios
def test_criterio_inexistente():
    dados = base()
    transicao(dados, "T2")["criterios"] = [2, 99]
    (erro,) = [e for e in erros(dados, criterios="1. a\n2. b\n3. c\n4. d") if e.codigo == "criterio_inexistente"]
    assert "T2" in erro.mensagem and "99" in erro.mensagem


def test_criterio_nao_coberto():
    dados = base()
    transicao(dados, "T2")["criterios"] = []
    (erro,) = [e for e in erros(dados) if e.codigo == "criterio_nao_coberto"]
    assert erro.mensagem == "O critério 2 não está representado em nenhuma transição."


# ---------------------------------------------------------------- determinismo
def test_duas_transicoes_sem_guarda():
    dados = base()
    dados["estados"].append({"id": "Outro", "rotulo": "Outro", "tipo": "final"})
    dados["transicoes"].append({"id": "T5", "de": "AguardandoPin", "evento": "pin_valido", "para": "Outro"})
    (erro,) = [e for e in erros(dados) if e.codigo == "transicao_ambigua"]
    assert "AguardandoPin / pin_valido" in erro.mensagem


def test_guardas_sobrepostas_mostram_o_valor():
    dados = base()
    transicao(dados, "T3")["guarda"] = "tentativas < 3"
    (erro,) = [e for e in erros(dados) if e.codigo == "guardas_sobrepostas"]
    assert "tentativas = 2" in erro.mensagem


def test_guardas_complementares_entre_variaveis():
    dados = base()
    dados["variaveis"] += [{"nome": "valor", "tipo": "decimal", "categoria": "entrada"},
                           {"nome": "saldo", "tipo": "decimal", "categoria": "contexto"}]
    dados["estados"].append({"id": "Recusado", "rotulo": "Recusado", "tipo": "final"})
    transicao(dados, "T2")["guarda"] = "valor <= saldo"
    dados["transicoes"].append({"id": "T5", "de": "AguardandoPin", "evento": "pin_valido", "para": "Recusado",
                                "guarda": "valor > saldo"})
    assert erros(dados) == []


def test_sobreposicao_entre_variaveis_no_ponto_de_igualdade():
    dados = base()
    dados["variaveis"] += [{"nome": "valor", "tipo": "decimal", "categoria": "entrada"},
                           {"nome": "saldo", "tipo": "decimal", "categoria": "contexto"}]
    dados["estados"].append({"id": "Recusado", "rotulo": "Recusado", "tipo": "final"})
    transicao(dados, "T2")["guarda"] = "valor <= saldo"
    dados["transicoes"].append({"id": "T5", "de": "AguardandoPin", "evento": "pin_valido", "para": "Recusado",
                                "guarda": "valor >= saldo"})
    assert "guardas_sobrepostas" in codigos(dados)


def test_transicao_repetida():
    dados = base()
    dados["transicoes"].append({**copy.deepcopy(transicao(dados, "T1")), "id": "T5"})
    (erro,) = [e for e in erros(dados) if e.codigo == "transicao_duplicada"]
    assert "T1" in erro.mensagem and "T5" in erro.mensagem


def test_repetida_com_guarda_escrita_diferente():
    dados = base()
    dados["transicoes"].append({**copy.deepcopy(transicao(dados, "T3")), "id": "T5", "guarda": "tentativas<2"})
    assert "transicao_duplicada" in codigos(dados)


# ---------------------------------------------------------------- mensagens
def test_varios_erros_de_uma_vez_e_em_ordem():
    dados = base()
    transicao(dados, "T2")["criterios"] = []
    dados["estados"].append({"id": "Bloqueado", "rotulo": "Bloqueado", "tipo": "final"})
    lista = erros(dados)
    assert [e.codigo for e in lista] == ["estado_inalcancavel", "criterio_nao_coberto"]
    assert [e.grupo for e in lista] == [ALCANCABILIDADE, CRITERIOS]


def test_erro_tem_codigo_elementos_e_mensagem():
    dados = base()
    transicao(dados, "T2")["para"] = "Finalizado"
    erro = next(e for e in erros(dados) if e.codigo == "estado_inexistente")
    assert erro.como_dict() == {
        "codigo": "estado_inexistente",
        "elementos": ["T2", "Finalizado"],
        "mensagem": erro.mensagem,
    }


def test_validar_resposta_junta_todos_os_erros():
    dados = base()
    transicao(dados, "T2")["criterios"] = []
    dados["estados"].append({"id": "Bloqueado", "rotulo": "Bloqueado", "tipo": "final"})
    import json

    with pytest.raises(ErroModelo) as exc:
        validar_resposta(json.dumps(dados), CRITERIOS_3)
    assert len(exc.value.erros) == 2
    assert "critério 2" in str(exc.value) and "Bloqueado" in str(exc.value)


def test_erros_de_esquema_viram_erro_modelo():
    with pytest.raises(ErroModelo) as exc:
        validar_resposta('{"estados": [], "transicoes": []}')
    assert {e.codigo for e in exc.value.erros} == {"esquema_invalido"}
    assert "analise" in str(exc.value)


# ---------------------------------------------------------------- catálogo
CATALOGO = obter("login").catalogo


def login():
    return copy.deepcopy(obter("login").modelo)


def test_variavel_fora_do_catalogo():
    dados = login()
    dados["variaveis"] = [{"nome": "tentativas", "tipo": "inteiro", "categoria": "estado", "valor_inicial": 0}]
    assert "variavel_fora_do_catalogo" in codigos(dados, criterios=obter("login").criterios, catalogo=CATALOGO)


def test_inicial_divergente_do_catalogo():
    dados = login()
    estado(dados, "SemFalha")["tipo"] = "intermediario"
    estado(dados, "UmaFalha")["tipo"] = "inicial"
    (erro,) = [e for e in erros(dados, criterios=obter("login").criterios, catalogo=CATALOGO)
               if e.codigo == "inicial_divergente"]
    assert "'SemFalha'" in erro.mensagem and "'UmaFalha'" in erro.mensagem


def test_evento_fora_do_catalogo():
    dados = login()
    dados["transicoes"][0]["evento"] = "credenciais"
    assert "evento_fora_do_catalogo" in codigos(dados, criterios=obter("login").criterios, catalogo=CATALOGO)


# ---------------------------------------------------------------- referências e gabaritos (2.8)
@pytest.mark.parametrize("gabarito_id", exemplos.ids())
def test_gabaritos_passam_na_validacao(gabarito_id):
    g = exemplos.carregar(gabarito_id)
    assert erros(g["modelo"], criterios=g["criterios"]) == []


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_referencias_passam_na_validacao(sistema_id):
    d = obter(sistema_id)
    assert erros(d.modelo, criterios=d.criterios, catalogo=d.catalogo) == []


def test_gabaritos_esperados_existem():
    assert set(exemplos.ids()) == {"saque-atm", "cupom-promocional", "mfa-bloqueio", "carrinho"}
