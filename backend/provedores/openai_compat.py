"""Qualquer servidor do protocolo de chat da OpenAI: LM Studio, vLLM, llama.cpp server, endpoint /v1 do
Ollama, OpenRouter, Groq, Together...

OPENAI_COMPAT_MODO_ESQUEMA escolhe como pedir JSON, porque o suporte varia entre servidores:
`json_schema` (esquema estrito, padrão), `json_object` (só JSON) ou `nenhum` (só o prompt).
"""
import os

from .base import (
    TEMPERATURA,
    Capacidades,
    ErroLLM,
    ErroTimeout,
    Provedor,
    esquema_saida,
    semente,
    timeout_segundos,
)

MODOS = ("json_schema", "json_object", "nenhum")
CHAVE_SEM_USO = "sem-chave"  # servidores locais ignoram a chave, mas o cliente exige um valor
NOME = "OpenAI compatível"


def base_url() -> str:
    return os.getenv("OPENAI_COMPAT_BASE_URL", "").strip()


def modo_esquema() -> str:
    modo = os.getenv("OPENAI_COMPAT_MODO_ESQUEMA", "json_schema").strip() or "json_schema"
    if modo not in MODOS:
        raise ErroLLM(f"OPENAI_COMPAT_MODO_ESQUEMA inválido: {modo}. Use um destes: {', '.join(MODOS)}.")
    return modo


def formato_resposta(modo: str) -> dict | None:
    if modo == "json_schema":
        return {"type": "json_schema",
                "json_schema": {"name": "modelo_estados", "schema": esquema_saida(), "strict": True}}
    if modo == "json_object":
        return {"type": "json_object"}
    return None


def cliente(limite: float):
    import openai

    return openai.OpenAI(base_url=base_url(), api_key=os.getenv("OPENAI_COMPAT_API_KEY", "").strip() or CHAVE_SEM_USO,
                         timeout=limite, max_retries=0)


def traduzir_erro(e: Exception, limite: float) -> ErroLLM | None:
    import openai

    if isinstance(e, openai.APITimeoutError):
        return ErroTimeout(f"{NOME}: não respondeu em {limite:.0f}s.")
    if isinstance(e, openai.AuthenticationError):
        return ErroLLM(f"{NOME}: credencial recusada (401). Confira OPENAI_COMPAT_API_KEY.")
    if isinstance(e, openai.RateLimitError):
        return ErroLLM(f"{NOME}: limite de taxa atingido (429). Aguarde ou troque de provedor.")
    if isinstance(e, openai.APIStatusError):
        if e.status_code >= 500:
            return ErroLLM(f"{NOME}: indisponível ({e.status_code}). Tente de novo ou troque de provedor.")
        return ErroLLM(f"{NOME}: erro {e.status_code}: {e.message}")
    if isinstance(e, openai.APIConnectionError):
        return ErroLLM(f"{NOME}: sem conexão com {base_url()} ({e}).")
    return None


class ProvedorOpenAICompat(Provedor):
    id = "openai_compat"
    nome = "OpenAI compatível"
    variavel_modelo = "OPENAI_COMPAT_MODEL"
    modelo_fixo = ""

    @property
    def nuvem(self) -> bool:  # local ou nuvem depende da URL configurada
        url = base_url().lower()
        return bool(url) and not any(h in url for h in ("localhost", "127.0.0.1", "0.0.0.0"))

    def capacidades(self, modelo: str) -> Capacidades:
        try:
            modo = modo_esquema()
        except ErroLLM:
            modo = "nenhum"
        deterministico = os.getenv("OPENAI_COMPAT_DETERMINISTICO", "0").strip() == "1"
        return Capacidades(esquema=modo == "json_schema", temperatura=True, semente=deterministico)

    def configurado(self) -> tuple[bool, str]:
        if not base_url():
            return False, "OPENAI_COMPAT_BASE_URL não definida."
        if not self.modelo_padrao():
            return False, "OPENAI_COMPAT_MODEL não definido."
        return True, f"Servidor em {base_url()}."

    def saude(self) -> dict:
        info = super().saude()
        info["base_url"] = base_url() or None
        info["modo_esquema"] = os.getenv("OPENAI_COMPAT_MODO_ESQUEMA", "json_schema")
        info["chave_configurada"] = bool(os.getenv("OPENAI_COMPAT_API_KEY", "").strip())
        if info["configurado"]:
            try:
                cliente(3).models.list()
                info["acessivel"] = True
            except Exception as e:  # noqa: BLE001
                info["acessivel"] = False
                info["mensagem"] = f"Servidor não respondeu em {base_url()}: {type(e).__name__}"
        return info

    def chamar(self, system, mensagens, *, modelo=None, timeout=None, api_key=None) -> str:
        if not base_url():
            raise ErroLLM(f"{NOME}: defina OPENAI_COMPAT_BASE_URL no .env (ex.: http://localhost:1234/v1).")
        modelo = self.modelo(modelo)
        if not modelo:
            raise ErroLLM(f"{NOME}: defina OPENAI_COMPAT_MODEL no .env ou informe o modelo na geração.")
        limite = timeout or timeout_segundos()
        pedido = dict(
            model=modelo,
            messages=[{"role": "system", "content": system}, *mensagens],
            temperature=TEMPERATURA,
            seed=semente(),
        )
        formato = formato_resposta(modo_esquema())
        if formato:
            pedido["response_format"] = formato
        try:
            resposta = cliente(limite).chat.completions.create(**pedido)
        except Exception as e:  # noqa: BLE001
            traduzido = traduzir_erro(e, limite)
            if traduzido is None:
                raise
            raise traduzido from e
        escolha = resposta.choices[0]
        recusa = getattr(escolha.message, "refusal", None)
        if recusa:
            raise ErroLLM(f"{NOME}: o modelo recusou a solicitação ({recusa}).")
        return escolha.message.content or ""
