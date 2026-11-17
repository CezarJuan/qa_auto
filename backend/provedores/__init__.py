"""Registro de provedores de LLM.

Adicionar um provedor: criar um módulo com uma subclasse de `Provedor` e incluí-la em `REGISTRO`.
Interface, API, `/saude` e avaliação leem o registro.
"""
from .base import Capacidades, ErroLLM, ErroTimeout, Provedor
from .claude import ProvedorAnthropic
from .gemini import ProvedorGemini
from .ollama import ProvedorOllama
from .openai_compat import ProvedorOpenAICompat

REGISTRO: dict[str, Provedor] = {}

# Rótulos usados antes do registro; continuam aceitos pela API e pela avaliação
ALIASES = {"Ollama (Local)": "ollama", "Gemini (Cloud)": "gemini"}


def registrar(provedor: Provedor) -> Provedor:
    REGISTRO[provedor.id] = provedor
    return provedor


def normalizar(motor: str) -> str:
    """Id do provedor para um id ou rótulo legado; ValueError se for desconhecido."""
    ident = ALIASES.get(motor, motor)
    if ident not in REGISTRO:
        aceitos = ", ".join(REGISTRO)
        raise ValueError(f"Provedor desconhecido: {motor}. Use um destes: {aceitos}.")
    return ident


def obter(motor: str) -> Provedor:
    return REGISTRO[normalizar(motor)]


for _provedor in (ProvedorOllama(), ProvedorGemini(), ProvedorOpenAICompat(), ProvedorAnthropic()):
    registrar(_provedor)

__all__ = ["ALIASES", "REGISTRO", "Capacidades", "ErroLLM", "ErroTimeout", "Provedor", "normalizar", "obter",
           "registrar"]
