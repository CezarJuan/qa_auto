"""Sistemas exemplo: alvos reais para executar os testes gerados."""
from .base import Catalogo, Definicao, ErroSistema, SistemaExemplo
from .login import LOGIN
from .saque import SAQUE

SISTEMAS: dict[str, Definicao] = {"login": LOGIN, "saque": SAQUE}
VARIANTES = ("correto", "bug")


def obter(sistema_id: str) -> Definicao:
    try:
        return SISTEMAS[sistema_id]
    except KeyError:
        raise ErroSistema(f"Sistema exemplo desconhecido: {sistema_id}") from None


def criar(sistema_id: str, variante: str = "correto") -> SistemaExemplo:
    definicao = obter(sistema_id)
    if variante not in VARIANTES:
        raise ErroSistema(f"Variante desconhecida: {variante}")
    return definicao.correto() if variante == "correto" else definicao.com_bug()


__all__ = ["Catalogo", "Definicao", "ErroSistema", "SISTEMAS", "SistemaExemplo", "VARIANTES", "criar", "obter"]
