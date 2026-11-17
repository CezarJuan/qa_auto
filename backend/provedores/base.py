"""Contrato comum dos provedores de LLM: erros, configuração compartilhada e capacidades."""
import os
from dataclasses import dataclass

from ..schemas import ModeloEstados

TEMPERATURA = 0
SEMENTE_PADRAO = 42
TIMEOUT_PADRAO_SEGUNDOS = 180


class ErroLLM(Exception):
    """Falha ao se comunicar com o motor LLM (chave, rede, serviço fora do ar...)."""


class ErroTimeout(ErroLLM):
    """O provedor não respondeu dentro do tempo limite da chamada."""


def timeout_segundos() -> int:
    return int(os.getenv("QA_TIMEOUT_LLM", TIMEOUT_PADRAO_SEGUNDOS))


def semente() -> int:
    return int(os.getenv("QA_SEMENTE", SEMENTE_PADRAO))


def esquema_saida() -> dict:
    """JSON Schema do modelo de estados, usado para restringir a saída dos provedores."""
    return ModeloEstados.model_json_schema()


def eh_timeout(erro: Exception) -> bool:
    import httpx

    if isinstance(erro, (httpx.TimeoutException, TimeoutError)):
        return True
    texto = str(erro).lower()
    return any(m in texto for m in ("timed out", "timeout", "deadline_exceeded", "deadline exceeded"))


@dataclass(frozen=True)
class Capacidades:
    """O que o provedor aceita para este modelo."""

    esquema: bool
    temperatura: bool
    semente: bool

    @property
    def deterministico(self) -> bool:
        return self.temperatura and self.semente


class Provedor:
    """Base dos provedores. Cada um implementa `chamar` e, se precisar, `capacidades` e `saude`."""

    id: str = ""
    nome: str = ""
    nuvem: bool = False
    variavel_modelo: str = ""
    modelo_fixo: str = ""

    def modelo_padrao(self) -> str:
        return os.getenv(self.variavel_modelo) or self.modelo_fixo

    def modelo(self, modelo: str | None = None) -> str:
        """Modelo da requisição, se houver; senão o configurado no ambiente."""
        return modelo or self.modelo_padrao()

    def capacidades(self, modelo: str) -> Capacidades:
        return Capacidades(esquema=True, temperatura=True, semente=True)

    def configurado(self) -> tuple[bool, str]:
        return True, ""

    def saude(self) -> dict:
        """Situação do provedor, sem segredos."""
        ok, mensagem = self.configurado()
        modelo = self.modelo_padrao()
        return {
            "id": self.id,
            "nome": self.nome,
            "nuvem": self.nuvem,
            "modelo": modelo,
            "configurado": ok,
            "deterministico": self.capacidades(modelo).deterministico,
            "mensagem": mensagem,
        }

    def chamar(self, system: str, mensagens: list[dict], *, modelo: str | None = None,
               timeout: float | None = None, api_key: str | None = None) -> str:
        raise NotImplementedError
