"""Métricas de uma rodada: precisão e recall de estados e transições e propriedades satisfeitas."""
from dataclasses import dataclass, field

from .alinhamento import Alinhamento, Embeddings, alinhar
from .casos import Caso, Propriedade
from .simulacao import ErroSimulacao, simular


@dataclass
class ResultadoPropriedade:
    descricao: str
    criterio: int
    satisfeita: bool
    motivo: str = ""


@dataclass
class Qualidade:
    precisao_estados: float = 0.0
    recall_estados: float = 0.0
    precisao_transicoes: float = 0.0
    recall_transicoes: float = 0.0
    propriedades: float = 0.0
    detalhes_propriedades: list[ResultadoPropriedade] = field(default_factory=list)
    nao_mapeados: dict[str, list[str]] = field(default_factory=dict)


def _razao(a: int, b: int) -> float:
    return a / b if b else 0.0


def avaliar_propriedade(modelo: dict, propriedade: Propriedade, alinhamento: Alinhamento) -> ResultadoPropriedade:
    """Simula o modelo extraído com os eventos e dados da propriedade, traduzidos pelo alinhamento."""
    eventos_inv = alinhamento.inverso("eventos")
    variaveis_inv = alinhamento.inverso("variaveis")
    estados_inv = alinhamento.inverso("estados")

    def falha(motivo: str) -> ResultadoPropriedade:
        return ResultadoPropriedade(propriedade.descricao, propriedade.criterio, False, motivo)

    def traduzir_valores(valores: dict) -> dict | str:
        traduzidos = {}
        for nome, valor in valores.items():
            if nome not in variaveis_inv:
                return nome
            traduzidos[variaveis_inv[nome]] = valor
        return traduzidos

    passos = []
    for passo in propriedade.eventos:
        if passo.evento not in eventos_inv:
            return falha(f"evento não mapeado: {passo.evento}")
        dados = traduzir_valores(passo.dados)
        if isinstance(dados, str):
            return falha(f"variável não mapeada: {dados}")
        passos.append((eventos_inv[passo.evento], dados))
    contexto = traduzir_valores(propriedade.contexto)
    if isinstance(contexto, str):
        return falha(f"variável não mapeada: {contexto}")
    esperado = None
    if propriedade.estado_esperado:
        if propriedade.estado_esperado not in estados_inv:
            return falha(f"estado não mapeado: {propriedade.estado_esperado}")
        esperado = estados_inv[propriedade.estado_esperado]
    try:
        sim = simular(modelo, passos, contexto)
    except ErroSimulacao as e:
        return falha(str(e))
    if propriedade.recusado and not sim.ultimo_recusado:
        return falha(f"o evento '{propriedade.eventos[-1].evento}' foi aceito, mas deveria ser recusado")
    if esperado and sim.estado != esperado:
        return falha(f"terminou em {sim.estado}, esperado {esperado}")
    return ResultadoPropriedade(propriedade.descricao, propriedade.criterio, True)


def calcular(modelo: dict, caso: Caso, embeddings: Embeddings | None = None) -> Qualidade:
    """Compara o modelo extraído com o gabarito do caso."""
    gabarito = caso.gabarito
    alinhamento = alinhar(modelo, gabarito, caso.sinonimos, embeddings)

    estados_e = {e["id"] for e in modelo["estados"]}
    estados_g = {e["id"] for e in gabarito["estados"]}
    estados_ok = {alinhamento.estados[e] for e in estados_e if e in alinhamento.estados}

    triplas_g = {(t["de"], t["evento"], t["para"]) for t in gabarito["transicoes"]}
    triplas_e = {(t["de"], t["evento"], t["para"]) for t in modelo["transicoes"]}
    mapeadas = set()
    for de, evento, para in triplas_e:
        if de in alinhamento.estados and para in alinhamento.estados and evento in alinhamento.eventos:
            mapeadas.add((alinhamento.estados[de], alinhamento.eventos[evento], alinhamento.estados[para]))
    corretas = mapeadas & triplas_g

    detalhes = [avaliar_propriedade(modelo, p, alinhamento) for p in caso.propriedades]
    return Qualidade(
        precisao_estados=_razao(len(estados_ok & estados_g), len(estados_e)),
        recall_estados=_razao(len(estados_ok & estados_g), len(estados_g)),
        precisao_transicoes=_razao(len(corretas), len(triplas_e)),
        recall_transicoes=_razao(len(corretas), len(triplas_g)),
        propriedades=_razao(sum(d.satisfeita for d in detalhes), len(detalhes)),
        detalhes_propriedades=detalhes,
        nao_mapeados=alinhamento.nao_mapeados,
    )
