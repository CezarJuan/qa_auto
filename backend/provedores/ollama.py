"""Ollama local: chamada com JSON Schema, verificação do modelo instalado e aquecimento."""
import logging
import os
import threading

from .base import (
    TEMPERATURA,
    ErroLLM,
    ErroTimeout,
    Provedor,
    eh_timeout,
    esquema_saida,
    semente,
    timeout_segundos,
)

log = logging.getLogger(__name__)

MODELO_PADRAO = "llama3.1:8b"
HOST_PADRAO = "http://localhost:11434"
KEEP_ALIVE_PADRAO = "30m"
TIMEOUT_VERIFICACAO_SEGUNDOS = 3


def host() -> str:
    return os.getenv("OLLAMA_HOST") or HOST_PADRAO


def modelo_configurado() -> str:
    return os.getenv("OLLAMA_MODEL") or MODELO_PADRAO


def chamar(system: str, mensagens: list[dict], timeout: float | None = None, modelo: str | None = None) -> str:
    import ollama

    modelo = modelo or modelo_configurado()
    limite = timeout or timeout_segundos()
    try:
        client = ollama.Client(host=host(), timeout=limite)
        resp = client.chat(
            model=modelo,
            messages=[{"role": "system", "content": system}, *mensagens],
            format=esquema_saida(),
            options={"temperature": TEMPERATURA, "seed": semente()},
        )
        return resp["message"]["content"]
    except Exception as e:  # noqa: BLE001
        if eh_timeout(e):
            raise ErroTimeout(f"O Ollama não respondeu em {limite:.0f}s: {e}") from e
        raise ErroLLM(
            f"Erro ao chamar o Ollama (o servidor está rodando e o modelo '{modelo}' foi baixado?): {e}"
        ) from e


def verificar() -> dict:
    """Confere se o servidor do Ollama responde e se o modelo configurado está instalado."""
    import ollama

    modelo = modelo_configurado()
    try:
        resposta = ollama.Client(host=host(), timeout=TIMEOUT_VERIFICACAO_SEGUNDOS).list()
    except Exception as e:  # noqa: BLE001
        return {
            "modelo": modelo,
            "acessivel": False,
            "disponivel": False,
            "instalados": [],
            "mensagem": f"Ollama inacessível em {host()}: {e}",
        }
    instalados = sorted(m.model for m in resposta.models if m.model)
    disponivel = modelo in instalados
    if disponivel:
        mensagem = f"Modelo '{modelo}' disponível."
    else:
        lista = ", ".join(instalados) or "nenhum"
        mensagem = (
            f"O modelo configurado '{modelo}' não está instalado no Ollama. "
            f"Modelos disponíveis: {lista}. Ajuste OLLAMA_MODEL ou rode 'ollama pull {modelo}'."
        )
    return {"modelo": modelo, "acessivel": True, "disponivel": disponivel, "instalados": instalados,
            "mensagem": mensagem}


class EstadoAquecimento:
    """Situação do carregamento do modelo do Ollama na memória."""

    NAO_INICIADO = "nao_iniciado"
    CARREGANDO = "carregando modelo"
    PRONTO = "pronto"
    FALHOU = "falhou"
    IGNORADO = "ignorado"

    def __init__(self) -> None:
        self.situacao = self.NAO_INICIADO
        self.mensagem = ""


AQUECIMENTO = EstadoAquecimento()


def aquecer(estado: EstadoAquecimento = AQUECIMENTO, verificar_fn=None) -> None:
    """Pede ao Ollama para carregar o modelo e mantê-lo na memória por QA_OLLAMA_KEEP_ALIVE."""
    import ollama

    verificacao = (verificar_fn or verificar)()
    if not verificacao["disponivel"]:
        estado.situacao = EstadoAquecimento.IGNORADO
        estado.mensagem = verificacao["mensagem"]
        return
    estado.situacao = EstadoAquecimento.CARREGANDO
    estado.mensagem = f"Carregando '{verificacao['modelo']}' na memória."
    keep_alive = os.getenv("QA_OLLAMA_KEEP_ALIVE") or KEEP_ALIVE_PADRAO
    try:
        client = ollama.Client(host=host(), timeout=timeout_segundos())
        client.generate(model=verificacao["modelo"], prompt="", keep_alive=keep_alive)
    except Exception as e:  # noqa: BLE001
        estado.situacao = EstadoAquecimento.FALHOU
        estado.mensagem = f"Falha ao carregar o modelo: {e}"
        log.warning(estado.mensagem)
        return
    estado.situacao = EstadoAquecimento.PRONTO
    estado.mensagem = f"Modelo '{verificacao['modelo']}' carregado (keep_alive={keep_alive})."


def iniciar_aquecimento(estado: EstadoAquecimento = AQUECIMENTO) -> threading.Thread:
    """Dispara o aquecimento em segundo plano para não atrasar a subida da API."""
    estado.situacao = EstadoAquecimento.CARREGANDO
    estado.mensagem = "Verificando o Ollama."
    thread = threading.Thread(target=aquecer, args=(estado,), daemon=True)
    thread.start()
    return thread


class ProvedorOllama(Provedor):
    id = "ollama"
    nome = "Ollama (Local)"
    variavel_modelo = "OLLAMA_MODEL"
    modelo_fixo = MODELO_PADRAO

    def saude(self) -> dict:
        info = super().saude()
        info.update(verificar())
        info["configurado"] = True
        info["situacao"] = AQUECIMENTO.situacao
        info["aquecimento"] = AQUECIMENTO.mensagem
        return info

    def chamar(self, system, mensagens, *, modelo=None, timeout=None, api_key=None) -> str:
        return chamar(system, mensagens, timeout=timeout, modelo=modelo)
