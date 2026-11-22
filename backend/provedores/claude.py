"""Anthropic (Claude) pelo SDK oficial, com saída restrita ao JSON Schema do modelo de estados.

- Modelo padrão `claude-opus-5-5` (ANTHROPIC_MODEL ou modelo da requisição).
- Esses modelos recusam temperatura e semente, então nada disso é enviado: a extração não é determinística.
- `max_retries=0`: novas tentativas do SDK multiplicariam o tempo e furariam o orçamento da geração.
- Fallback de recusa do próprio servidor ligado por padrão (ANTHROPIC_FALLBACK_RECUSA=0 desliga).
"""
import os

from ..schemas import ModeloEstados
from .base import Capacidades, ErroLLM, ErroTimeout, Provedor, timeout_segundos

MODELO_PADRAO = "claude-opus-5-5"
EFFORT_PADRAO = "medium"
MAX_TOKENS = 16000
BETA_FALLBACK = "server-side-fallback-2026-07-01"
NOME = "Anthropic"


def effort() -> str:
    return os.getenv("ANTHROPIC_EFFORT", EFFORT_PADRAO).strip()


def fallback_de_recusa() -> bool:
    return os.getenv("ANTHROPIC_FALLBACK_RECUSA", "1").strip() != "0"


def esquema() -> dict:
    """Esquema no subconjunto aceito pela API (restrições sem suporte vão para a descrição)."""
    import anthropic

    return anthropic.transform_schema(ModeloEstados)


def cliente(limite: float):
    import anthropic

    return anthropic.Anthropic(timeout=limite, max_retries=0)


def traduzir_erro(e: Exception, limite: float) -> ErroLLM | None:
    """Converte as exceções tipadas do SDK em ErroLLM/ErroTimeout, da mais específica à mais geral."""
    import anthropic

    if isinstance(e, anthropic.APITimeoutError):
        return ErroTimeout(f"{NOME}: não respondeu em {limite:.0f}s.")
    if isinstance(e, anthropic.AuthenticationError):
        return ErroLLM(f"{NOME}: credencial recusada (401). Confira ANTHROPIC_API_KEY.")
    if isinstance(e, anthropic.RateLimitError):
        return ErroLLM(f"{NOME}: limite de taxa atingido (429). Aguarde ou troque de provedor.")
    if isinstance(e, anthropic.APIStatusError):
        if e.status_code == 529 or isinstance(e, anthropic.OverloadedError):
            return ErroLLM(f"{NOME}: sobrecarregado ({e.status_code}). Tente de novo ou troque de provedor.")
        if e.status_code >= 500:
            return ErroLLM(f"{NOME}: indisponível ({e.status_code}). Tente de novo ou troque de provedor.")
        return ErroLLM(f"{NOME}: erro {e.status_code}: {e.message}")
    if isinstance(e, anthropic.APIConnectionError):
        return ErroLLM(f"{NOME}: sem conexão com a API ({e}).")
    erro_de_credencial = getattr(anthropic, "CredentialsError", ())
    if (erro_de_credencial and isinstance(e, erro_de_credencial)) or (
        isinstance(e, TypeError) and "authentication" in str(e).lower()
    ):
        return ErroLLM(f"{NOME}: nenhuma credencial encontrada. Defina ANTHROPIC_API_KEY no .env.")
    return None


class ProvedorAnthropic(Provedor):
    id = "anthropic"
    nome = "Anthropic (Claude)"
    nuvem = True
    variavel_modelo = "ANTHROPIC_MODEL"
    modelo_fixo = MODELO_PADRAO

    def capacidades(self, modelo: str) -> Capacidades:
        return Capacidades(esquema=True, temperatura=False, semente=False)

    def configurado(self) -> tuple[bool, str]:
        if os.getenv("ANTHROPIC_API_KEY", "").strip() or os.getenv("ANTHROPIC_AUTH_TOKEN", "").strip():
            return True, "Credencial configurada."
        return False, "ANTHROPIC_API_KEY não definida (um perfil do `ant auth login` também é aceito)."

    def saude(self) -> dict:
        info = super().saude()
        info["chave_configurada"] = info["configurado"]
        info["effort"] = effort() or None
        info["fallback_de_recusa"] = fallback_de_recusa()
        return info

    def chamar(self, system, mensagens, *, modelo=None, timeout=None, api_key=None) -> str:
        limite = timeout or timeout_segundos()
        config = {"format": {"type": "json_schema", "schema": esquema()}}
        if effort():
            config["effort"] = effort()
        pedido = dict(
            model=self.modelo(modelo),
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": m["role"], "content": m["content"]} for m in mensagens],
            output_config=config,
        )
        try:
            api = cliente(limite)
            if fallback_de_recusa():
                resposta = api.beta.messages.create(betas=[BETA_FALLBACK], fallbacks="default", **pedido)
            else:
                resposta = api.messages.create(**pedido)
        except Exception as e:  # noqa: BLE001
            traduzido = traduzir_erro(e, limite)
            if traduzido is None:
                raise
            raise traduzido from e
        if resposta.stop_reason == "refusal":
            detalhes = getattr(resposta, "stop_details", None)
            categoria = getattr(detalhes, "category", None) or "não informada"
            raise ErroLLM(f"{NOME}: o modelo recusou a solicitação (categoria: {categoria}).")
        return "".join(b.text for b in resposta.content if getattr(b, "type", "") == "text")
