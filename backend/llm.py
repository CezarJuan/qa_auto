"""Fachada dos provedores de LLM (registro em backend/provedores) e da saúde do Ollama.

Mantém a assinatura `chamar_llm(motor, system, mensagens, api_key=None, timeout=None, modelo=None)`
usada pelo serviço e pelos testes.
"""
import logging

from dotenv import load_dotenv

load_dotenv()

from . import provedores  # noqa: E402  (o .env precisa estar carregado antes)
from .provedores import ollama as _ollama  # noqa: E402
from .provedores.base import (  # noqa: E402,F401
    SEMENTE_PADRAO,
    TEMPERATURA,
    TIMEOUT_PADRAO_SEGUNDOS,
    ErroLLM,
    ErroTimeout,
    esquema_saida,
    semente,
    timeout_segundos,
)
from .provedores.gemini import MODELO_PADRAO as MODELO_GEMINI_PADRAO  # noqa: E402,F401
from .provedores.gemini import chamar as _chamar_gemini_impl  # noqa: E402
from .provedores.gemini import modelo_configurado as modelo_gemini  # noqa: E402,F401
from .provedores.ollama import (  # noqa: E402,F401
    AQUECIMENTO,
    HOST_PADRAO as HOST_OLLAMA_PADRAO,
    KEEP_ALIVE_PADRAO,
    MODELO_PADRAO as MODELO_OLLAMA_PADRAO,
    EstadoAquecimento,
)
from .provedores.ollama import host as host_ollama  # noqa: E402,F401
from .provedores.ollama import modelo_configurado as modelo_ollama  # noqa: E402,F401

log = logging.getLogger(__name__)


def nome_do_modelo(motor: str, modelo: str | None = None) -> str:
    """Modelo efetivo: o da requisição ou o configurado para o provedor."""
    return provedores.obter(motor).modelo(modelo)


def capacidades(motor: str, modelo: str | None = None) -> provedores.Capacidades:
    provedor = provedores.obter(motor)
    return provedor.capacidades(provedor.modelo(modelo))


def _chamar_gemini(system, mensagens, api_key=None, timeout=None, modelo=None) -> str:
    return _chamar_gemini_impl(system, mensagens, api_key=api_key, timeout=timeout, modelo=modelo)


def _chamar_ollama(system, mensagens, timeout=None, modelo=None) -> str:
    return _ollama.chamar(system, mensagens, timeout=timeout, modelo=modelo)


def chamar_llm(motor: str, system: str, mensagens: list[dict], api_key: str | None = None,
               timeout: float | None = None, modelo: str | None = None) -> str:
    try:
        provedor = provedores.obter(motor)
    except ValueError as e:
        raise ErroLLM(str(e)) from e
    return provedor.chamar(system, mensagens, modelo=modelo, timeout=timeout, api_key=api_key)


# ---------------------------------------------------------------- saúde e aquecimento do Ollama
def verificar_ollama() -> dict:
    return _ollama.verificar()


def aquecer_ollama(estado: EstadoAquecimento = AQUECIMENTO) -> None:
    _ollama.aquecer(estado)


def iniciar_aquecimento(estado: EstadoAquecimento = AQUECIMENTO):
    return _ollama.iniciar_aquecimento(estado)


def saude_provedores() -> dict[str, dict]:
    """Uma entrada por provedor do registro, sem segredos."""
    return {ident: p.saude() for ident, p in provedores.REGISTRO.items()}
