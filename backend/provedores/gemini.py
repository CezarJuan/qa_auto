"""Gemini (Google): chamada com JSON Schema, temperatura 0 e semente."""
import os

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

MODELO_PADRAO = "gemini-3.8-flash"


def modelo_configurado() -> str:
    return os.getenv("GEMINI_MODEL") or MODELO_PADRAO


def chamar(system: str, mensagens: list[dict], api_key: str | None = None, timeout: float | None = None,
           modelo: str | None = None) -> str:
    from google import genai
    from google.genai import types

    chave = api_key or os.getenv("GEMINI_API_KEY")
    if not chave:
        raise ErroLLM("GEMINI_API_KEY não configurada. Defina-a no arquivo .env ou informe na barra lateral.")
    modelo = modelo or modelo_configurado()
    contents = [
        types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part(text=m["content"])])
        for m in mensagens
    ]
    limite = timeout or timeout_segundos()
    try:
        client = genai.Client(api_key=chave, http_options=types.HttpOptions(timeout=int(limite * 1000)))
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
        if eh_timeout(e):
            raise ErroTimeout(f"O Gemini não respondeu em {limite:.0f}s: {e}") from e
        raise ErroLLM(f"Erro ao chamar o Gemini: {e}") from e


class ProvedorGemini(Provedor):
    id = "gemini"
    nome = "Gemini (Cloud)"
    nuvem = True
    variavel_modelo = "GEMINI_MODEL"
    modelo_fixo = MODELO_PADRAO

    def configurado(self) -> tuple[bool, str]:
        if os.getenv("GEMINI_API_KEY", "").strip():
            return True, "Chave configurada."
        return False, "GEMINI_API_KEY não configurada (pode ser informada na barra lateral)."

    def saude(self) -> dict:
        info = super().saude()
        info["chave_configurada"] = info["configurado"]
        return info

    def chamar(self, system, mensagens, *, modelo=None, timeout=None, api_key=None) -> str:
        return chamar(system, mensagens, api_key=api_key, timeout=timeout, modelo=modelo)
