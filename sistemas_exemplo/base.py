"""Contrato comum dos sistemas exemplo usados como alvo dos testes gerados."""
from dataclasses import dataclass, field


class ErroSistema(Exception):
    """Sistema, variante ou evento desconhecido."""


@dataclass(frozen=True)
class Catalogo:
    """Vocabulário do sistema: nome -> descrição de cada estado, evento e variável."""

    estados: dict[str, str]
    eventos: dict[str, str]
    inicial: str
    variaveis: dict[str, str] = field(default_factory=dict)


class SistemaExemplo:
    """Recebe eventos do catálogo e expõe o estado atual com um nome do catálogo."""

    catalogo: Catalogo

    @property
    def estado(self) -> str:
        raise NotImplementedError

    def disparar(self, evento: str) -> None:
        if evento not in self.catalogo.eventos:
            raise ErroSistema(f"Evento fora do catálogo: {evento}")
        self._aplicar(evento)

    def _aplicar(self, evento: str) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class Definicao:
    """Tudo o que a ferramenta precisa saber sobre um sistema exemplo."""

    nome: str
    catalogo: Catalogo
    correto: type[SistemaExemplo]
    com_bug: type[SistemaExemplo]
    user_story: str
    criterios: str
    modelo: dict
