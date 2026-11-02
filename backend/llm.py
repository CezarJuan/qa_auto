"""Clientes LLM: Gemini e Ollama com a mesma assinatura, verificação e aquecimento do Ollama."""
import logging
import os
import threading

from dotenv import load_dotenv

from .schemas import ModeloEstados

load_dotenv()

log = logging.getLogger(__name__)

TEMPERATURA = 0
SEMENTE_PADRAO = 42
TIMEOUT_PADRAO_SEGUNDOS = 180
MODELO_OLLAMA_PADRAO = "llama3.1:8b"
MODELO_GEMINI_PADRAO = "gemini-3.8-flash"
HOST_OLLAMA_PADRAO = "http://localhost:11434"
KEEP_ALIVE_PADRAO = "30m"
TIMEOUT_VERIFICACAO_SEGUNDOS = 3


class ErroLLM(Exception):
    """Falha ao se comunicar com o motor LLM (chave, rede, serviço fora do ar...)."""


class ErroTimeout(ErroLLM):
    """O provedor não respondeu dentro do tempo limite da chamada."""


def timeout_segundos() -> int:
    return int(os.getenv("QA_TIMEOUT_LLM", TIMEOUT_PADRAO_SEGUNDOS))


def semente() -> int:
    return int(os.getenv("QA_SEMENTE", SEMENTE_PADRAO))


def esquema_saida() -> dict:
    """JSON Schema do modelo de estados, usado para restringir a saída dos dois provedores."""
    return ModeloEstados.model_json_schema()


def nome_do_modelo(motor: str) -> str:
    return modelo_gemini() if motor == "Gemini (Cloud)" else modelo_ollama()


def modelo_ollama() -> str:
    return os.getenv("OLLAMA_MODEL") or MODELO_OLLAMA_PADRAO


def modelo_gemini() -> str:
    return os.getenv("GEMINI_MODEL") or MODELO_GEMINI_PADRAO


def host_ollama() -> str:
    return os.getenv("OLLAMA_HOST") or HOST_OLLAMA_PADRAO


def _eh_timeout(erro: Exception) -> bool:
    import httpx

    if isinstance(erro, (httpx.TimeoutException, TimeoutError)):
        return True
    texto = str(erro).lower()
    return any(m in texto for m in ("timed out", "timeout", "deadline_exceeded", "deadline exceeded"))


def _chamar_gemini(
    system: str, mensagens: list[dict], api_key: str | None = None, timeout: float | None = None
) -> str:
    from google import genai
    from google.genai import types

    chave = api_key or os.getenv("GEMINI_API_KEY")
    if not chave:
        raise ErroLLM(
            "GEMINI_API_KEY não configurada. Defina-a no arquivo .env ou informe na barra lateral."
        )
    modelo = modelo_gemini()
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in mensagens
    ]
    limite = timeout or timeout_segundos()
    try:
        client = genai.Client(
            api_key=chave,
            http_options=types.HttpOptions(timeout=int(limite * 1000)),
        )
        resp = client.models.generate_content(
            model=modelo,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=TEMPERATURA,
                seed=semente(),
                response_mime_type="application/json",
                response_json_schema=esquema_saida(),
            ),
        )
        return resp.text or ""
    except Exception as e:  # noqa: BLE001
        if _eh_timeout(e):
            raise ErroTimeout(f"O Gemini não respondeu em {limite:.0f}s: {e}") from e
        raise ErroLLM(f"Erro ao chamar o Gemini: {e}") from e


def _chamar_ollama(system: str, mensagens: list[dict], timeout: float | None = None) -> str:
    import ollama

    modelo = modelo_ollama()
    limite = timeout or timeout_segundos()
    try:
        client = ollama.Client(host=host_ollama(), timeout=limite)
        resp = client.chat(
            model=modelo,
            messages=[{"role": "system", "content": system}, *mensagens],
            format=esquema_saida(),
            options={"temperature": TEMPERATURA, "seed": semente()},
        )
        return resp["message"]["content"]
    except Exception as e:  # noqa: BLE001
        if _eh_timeout(e):
            raise ErroTimeout(f"O Ollama não respondeu em {limite:.0f}s: {e}") from e
        raise ErroLLM(
            f"Erro ao chamar o Ollama (o servidor está rodando e o modelo '{modelo}' foi baixado?): {e}"
        ) from e


def chamar_llm(
    motor: str,
    system: str,
    mensagens: list[dict],
    api_key: str | None = None,
    timeout: float | None = None,
) -> str:
    if motor == "Gemini (Cloud)":
        return _chamar_gemini(system, mensagens, api_key=api_key, timeout=timeout)
    if motor == "Ollama (Local)":
        return _chamar_ollama(system, mensagens, timeout=timeout)
    raise ErroLLM(f"Motor desconhecido: {motor}")


# ---------------------------------------------------------------- saúde e aquecimento do Ollama
def verificar_ollama() -> dict:
    """Confere se o servidor do Ollama responde e se o modelo configurado está instalado."""
    import ollama

    modelo = modelo_ollama()
    try:
        resposta = ollama.Client(host=host_ollama(), timeout=TIMEOUT_VERIFICACAO_SEGUNDOS).list()
    except Exception as e:  # noqa: BLE001
        return {
            "modelo": modelo,
            "acessivel": False,
            "disponivel": False,
            "instalados": [],
            "mensagem": f"Ollama inacessível em {host_ollama()}: {e}",
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
    return {
        "modelo": modelo,
        "acessivel": True,
        "disponivel": disponivel,
        "instalados": instalados,
        "mensagem": mensagem,
    }


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


def aquecer_ollama(estado: EstadoAquecimento = AQUECIMENTO) -> None:
    """Pede ao Ollama para carregar o modelo e mantê-lo na memória por QA_OLLAMA_KEEP_ALIVE."""
    import ollama

    verificacao = verificar_ollama()
    if not verificacao["disponivel"]:
        estado.situacao = EstadoAquecimento.IGNORADO
        estado.mensagem = verificacao["mensagem"]
        return
    estado.situacao = EstadoAquecimento.CARREGANDO
    estado.mensagem = f"Carregando '{verificacao['modelo']}' na memória."
    keep_alive = os.getenv("QA_OLLAMA_KEEP_ALIVE") or KEEP_ALIVE_PADRAO
    try:
        client = ollama.Client(host=host_ollama(), timeout=timeout_segundos())
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
    thread = threading.Thread(target=aquecer_ollama, args=(estado,), daemon=True)
    thread.start()
    return thread
