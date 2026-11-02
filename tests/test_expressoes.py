import pytest

from backend.expressoes import (
    ErroExpressao,
    analisar_acao,
    analisar_guarda,
    avaliar_guarda,
    executar_acoes,
    formatar,
    inferir_tipo,
    variaveis_usadas,
)

TIPOS = {"valor": "decimal", "saldo": "decimal", "tentativas": "inteiro", "ativo": "booleano",
         "hoje": "data", "validade": "data"}


# guardas válidas
@pytest.mark.parametrize(
    "guarda, valores, esperado",
    [
        ("valor <= saldo e valor > 0", {"valor": 80, "saldo": 100}, True),
        ("valor <= saldo e valor > 0", {"valor": 120, "saldo": 100}, False),
        ("valor % 20 == 0", {"valor": 120}, True),
        ("valor % 20 == 0", {"valor": 101}, False),
        ("tentativas < 2 ou não ativo", {"tentativas": 5, "ativo": False}, True),
        ("não (tentativas >= 2)", {"tentativas": 1}, True),
        ("ativo == verdadeiro", {"ativo": True}, True),
        ("hoje <= validade", {"hoje": "2026-11-02", "validade": "2026-11-30"}, True),
        ("hoje <= '2026-01-01'", {"hoje": "2026-11-02"}, False),
        ("-tentativas < 0", {"tentativas": 1}, True),
    ],
)
def test_guarda_avaliada(guarda, valores, esperado):
    assert avaliar_guarda(guarda, valores) is esperado


def test_guarda_ausente_e_verdadeira():
    assert avaliar_guarda(None, {}) is True


def test_variaveis_usadas():
    assert variaveis_usadas(analisar_guarda("valor <= saldo e não ativo")) == {"valor", "saldo", "ativo"}


# guardas fora da linguagem
@pytest.mark.parametrize(
    "guarda",
    [
        "validar(valor)",
        "__import__('os').system('calc')",
        "valor * 2 > 10",
        "valor / 2 > 10",
        "conta.saldo > 0",
        "lista[0] == 1",
        "valor if ativo else 0",
        "lambda: 1",
        "valor <= ",
        "[1, 2] == valor",
    ],
)
def test_guarda_rejeitada(guarda):
    with pytest.raises(ErroExpressao):
        analisar_guarda(guarda)


def test_funcao_nunca_e_executada():
    chamadas = []
    with pytest.raises(ErroExpressao):
        avaliar_guarda("validar(valor)", {"valor": 1, "validar": lambda *_: chamadas.append(1)})
    assert chamadas == []


def test_variavel_sem_valor():
    with pytest.raises(ErroExpressao, match="saldo"):
        avaliar_guarda("valor <= saldo", {"valor": 1})


# ações
def test_acoes_em_ordem():
    assert executar_acoes(["tentativas += 1", "tentativas += 2", "saldo -= valor"],
                          {"tentativas": 0, "saldo": 100, "valor": 30}) == {"tentativas": 3, "saldo": 70, "valor": 30}


def test_atribuicao_simples():
    assert executar_acoes(["tentativas = 0"], {"tentativas": 2}) == {"tentativas": 0}


@pytest.mark.parametrize("acao", ["tentativas *= 2", "a = b = 1", "x.y = 1", "tentativas += 1; x = 2", "validar()",
                                  "tentativas = len(x)"])
def test_acao_rejeitada(acao):
    with pytest.raises(ErroExpressao):
        analisar_acao(acao)


def test_acao_analisada():
    acao = analisar_acao("tentativas += 1")
    assert (acao.alvo, acao.operador) == ("tentativas", "+=")


# tipos
@pytest.mark.parametrize("guarda", ["valor <= saldo", "tentativas < 2 e ativo", "hoje <= validade", "valor % 20 == 0"])
def test_tipos_compativeis(guarda):
    assert inferir_tipo(analisar_guarda(guarda), TIPOS) == "booleano"


@pytest.mark.parametrize("guarda", ["valor <= hoje", "ativo < 1", "tentativas e ativo", "não valor", "ativo + 1 > 0"])
def test_tipos_incompativeis(guarda):
    with pytest.raises(ErroExpressao):
        inferir_tipo(analisar_guarda(guarda), TIPOS)


def test_variavel_nao_declarada_no_tipo():
    with pytest.raises(ErroExpressao, match="saldo"):
        inferir_tipo(analisar_guarda("saldo >= valor"), {"valor": "decimal"})


# formatação canônica
@pytest.mark.parametrize(
    "guarda, canonica",
    [
        ("valor<=saldo", "valor <= saldo"),
        ("valor <= saldo and valor > 0", "valor <= saldo e valor > 0"),
        ("(a or b) e c", "(a ou b) e c"),
        ("not ativo", "não ativo"),
        ("tentativas>=2", "tentativas >= 2"),
    ],
)
def test_formatar(guarda, canonica):
    assert formatar(guarda) == canonica
