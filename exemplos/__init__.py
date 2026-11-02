"""Gabaritos: histórias com modelo de estados escrito à mão, no formato estendido.

Cada arquivo `<id>.json` tem `nome`, `historia`, `criterios` e `modelo`. Eles servem à demonstração
(exemplos sem sistema exemplo) e, mais adiante, ao conjunto de referência da avaliação.
"""
import json
from functools import cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent


def ids() -> list[str]:
    return sorted(p.stem for p in PASTA.glob("*.json"))


@cache
def _ler(gabarito_id: str) -> str:
    caminho = PASTA / f"{gabarito_id}.json"
    if not caminho.is_file():
        raise KeyError(f"Gabarito desconhecido: {gabarito_id}")
    return caminho.read_text(encoding="utf-8")


def carregar(gabarito_id: str) -> dict:
    """Devolve uma cópia nova do gabarito (quem chama pode alterá-la à vontade)."""
    return json.loads(_ler(gabarito_id))
