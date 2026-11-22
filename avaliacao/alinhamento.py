"""Alinhamento de nomes entre o modelo extraído e o gabarito.

1. Normalização: minúsculas, sem acento, sem `_`, sem espaço e sem hífen.
2. Sinônimos declarados no caso.
3. Opcional: similaridade de embeddings acima de um limiar, com atribuição gulosa um-para-um.
"""
import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable

LIMIAR_SEMANTICO = 0.85
MODELO_EMBEDDINGS = "nomic-embed-text"

Embeddings = Callable[[list[str]], list[list[float]]]


def normalizar(texto: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return re.sub(r"[\s_\-]+", "", sem_acento.lower())


@dataclass
class Alinhamento:
    """Mapas do nome extraído para o nome do gabarito, por categoria."""

    estados: dict[str, str] = field(default_factory=dict)
    eventos: dict[str, str] = field(default_factory=dict)
    variaveis: dict[str, str] = field(default_factory=dict)
    nao_mapeados: dict[str, list[str]] = field(default_factory=dict)

    def inverso(self, categoria: str) -> dict[str, str]:
        """Do nome do gabarito para o nome extraído."""
        return {g: e for e, g in getattr(self, categoria).items()}


def _alinhar_categoria(
    extraidos: dict[str, set[str]],
    gabarito: dict[str, set[str]],
    embeddings: Embeddings | None,
) -> tuple[dict[str, str], list[str]]:
    """extraidos/gabarito: nome -> conjunto de formas (id, rótulo, sinônimos), já normalizadas."""
    mapa: dict[str, str] = {}
    usados: set[str] = set()
    for nome_g, formas_g in gabarito.items():
        for nome_e, formas_e in extraidos.items():
            if nome_e not in usados and formas_e & formas_g:
                mapa[nome_e] = nome_g
                usados.add(nome_e)
                break
    if embeddings:
        restantes_e = [e for e in extraidos if e not in mapa]
        restantes_g = [g for g in gabarito if g not in mapa.values()]
        mapa.update(_alinhar_semantico(restantes_e, restantes_g, embeddings))
    return mapa, [e for e in extraidos if e not in mapa]


def _cosseno(a: list[float], b: list[float]) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def _alinhar_semantico(extraidos: list[str], gabarito: list[str], embeddings: Embeddings) -> dict[str, str]:
    if not extraidos or not gabarito:
        return {}
    vetores = embeddings(extraidos + gabarito)
    ve, vg = vetores[: len(extraidos)], vetores[len(extraidos):]
    pares = sorted(
        ((_cosseno(ve[i], vg[j]), i, j) for i in range(len(extraidos)) for j in range(len(gabarito))),
        reverse=True,
    )
    mapa, usados_e, usados_g = {}, set(), set()
    for similaridade, i, j in pares:
        if similaridade < LIMIAR_SEMANTICO:
            break
        if i in usados_e or j in usados_g:
            continue
        mapa[extraidos[i]] = gabarito[j]
        usados_e.add(i)
        usados_g.add(j)
    return mapa


def alinhar(extraido: dict, gabarito: dict, sinonimos: dict | None = None,
            embeddings: Embeddings | None = None) -> Alinhamento:
    """Alinha estados (por id e rótulo), eventos e variáveis do modelo extraído aos do gabarito."""
    sinonimos = sinonimos or {}

    def formas(nome: str, *extras: str) -> set[str]:
        return {normalizar(x) for x in (nome, *extras) if x}

    def do_gabarito(categoria: str, itens: dict[str, tuple[str, ...]]) -> dict[str, set[str]]:
        sin = sinonimos.get(categoria, {})
        return {nome: formas(nome, *extras, *sin.get(nome, [])) for nome, extras in itens.items()}

    estados_g = do_gabarito("estados", {e["id"]: (e.get("rotulo", ""),) for e in gabarito["estados"]})
    estados_e = {e["id"]: formas(e["id"], e.get("rotulo", "")) for e in extraido["estados"]}
    eventos_g = do_gabarito("eventos", {t["evento"]: () for t in gabarito["transicoes"]})
    eventos_e = {t["evento"]: formas(t["evento"]) for t in extraido["transicoes"]}
    variaveis_g = do_gabarito("variaveis", {v["nome"]: () for v in gabarito.get("variaveis", [])})
    variaveis_e = {v["nome"]: formas(v["nome"]) for v in extraido.get("variaveis", [])}

    resultado = Alinhamento()
    for categoria, ext, gab in (
        ("estados", estados_e, estados_g),
        ("eventos", eventos_e, eventos_g),
        ("variaveis", variaveis_e, variaveis_g),
    ):
        mapa, faltando = _alinhar_categoria(ext, gab, embeddings)
        setattr(resultado, categoria, mapa)
        if faltando:
            resultado.nao_mapeados[categoria] = faltando
    return resultado


def embeddings_ollama(textos: list[str]) -> list[list[float]]:
    """Embeddings pelo Ollama local (usado só com --alinhamento-semantico)."""
    import ollama

    from backend.llm import host_ollama

    resposta = ollama.Client(host=host_ollama()).embed(model=MODELO_EMBEDDINGS, input=textos)
    return [list(v) for v in resposta.embeddings]
