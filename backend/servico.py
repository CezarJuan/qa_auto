"""Orquestração da extração: prompt -> LLM -> validação, com retry, feedback do erro e orçamento de tempo."""
import logging
import os
import time
from dataclasses import dataclass, field

from sistemas_exemplo import obter

from .llm import ErroLLM, ErroTimeout, capacidades, chamar_llm, nome_do_modelo, timeout_segundos
from .prompts import SYSTEM_PROMPT, VERSAO_PROMPT, montar_prompt_correcao, montar_user_prompt
from .schemas import ModeloEstados, Requisicao
from .validacao import ErroModelo, ErroValidacao, validar_resposta

log = logging.getLogger(__name__)

MAX_TENTATIVAS = 3
ORCAMENTO_PADRAO_SEGUNDOS = 360
MARGEM_FRONT_SEGUNDOS = 15
MINIMO_POR_TENTATIVA_SEGUNDOS = 5

VALIDO = "valido"
INVALIDO = "invalido"
TIMEOUT = "timeout"


class ErroOrcamento(Exception):
    """O orçamento total de tempo da geração se esgotou."""


def orcamento_segundos() -> int:
    return int(os.getenv("QA_ORCAMENTO_GERACAO", ORCAMENTO_PADRAO_SEGUNDOS))


def espera_maxima() -> int:
    """Tempo que o front deve aguardar: o orçamento total do backend, mais uma margem."""
    return orcamento_segundos() + MARGEM_FRONT_SEGUNDOS


@dataclass
class Tentativa:
    resultado: str
    duracao: float
    erro: str = ""


@dataclass
class ResultadoGeracao:
    modelo: ModeloEstados
    tentativas: list[Tentativa] = field(default_factory=list)
    duracao: float = 0.0
    versao_prompt: str = VERSAO_PROMPT
    provedor: str = ""
    modelo_llm: str = ""
    deterministico: bool = True


def gerar(req: Requisicao, chamar=chamar_llm, relogio=time.monotonic) -> ResultadoGeracao:
    """Extrai o modelo dentro do orçamento, devolvendo o modelo e o registro das tentativas."""
    catalogo = obter(req.sistema).catalogo if req.sistema else None
    prompt = montar_user_prompt(req.user_story, req.criterios, catalogo)
    mensagens = [{"role": "user", "content": prompt}]
    orcamento = orcamento_segundos()
    inicio = relogio()
    tentativas: list[Tentativa] = []
    ultimo_erro = ""
    ultimos_erros: list[ErroValidacao] = []

    for _ in range(MAX_TENTATIVAS):
        restante = orcamento - (relogio() - inicio)
        if restante < MINIMO_POR_TENTATIVA_SEGUNDOS:
            raise _com_tentativas(ErroOrcamento(
                f"O orçamento de {orcamento}s para a geração se esgotou após "
                f"{len(tentativas)} tentativa(s). Último erro: {ultimo_erro or 'nenhum'}"
            ), tentativas)
        limite = min(timeout_segundos(), restante)
        t0 = relogio()
        try:
            resposta = chamar(req.motor, SYSTEM_PROMPT, mensagens, api_key=req.api_key, timeout=limite,
                              modelo=req.modelo)
        except ErroLLM as e:
            if not isinstance(e, ErroTimeout):
                raise _com_tentativas(e, tentativas)
            ultimo_erro = str(e)
            tentativas.append(Tentativa(TIMEOUT, relogio() - t0, ultimo_erro))
            log.warning("Tentativa %d: timeout (%s)", len(tentativas), ultimo_erro)
            continue
        try:
            modelo = validar_resposta(resposta, req.criterios, catalogo)
        except ErroModelo as e:
            ultimo_erro, ultimos_erros = str(e), e.erros
            tentativas.append(Tentativa(INVALIDO, relogio() - t0, ultimo_erro))
            # O modelo anterior vai como resposta do assistente, seguido dos erros agrupados
            mensagens.append({"role": "assistant", "content": resposta})
            mensagens.append({"role": "user", "content": montar_prompt_correcao(e.erros)})
            continue
        tentativas.append(Tentativa(VALIDO, relogio() - t0))
        return ResultadoGeracao(
            modelo, tentativas, relogio() - inicio,
            versao_prompt=VERSAO_PROMPT, provedor=req.motor, modelo_llm=nome_do_modelo(req.motor, req.modelo),
            deterministico=capacidades(req.motor, req.modelo).deterministico,
        )

    if tentativas and tentativas[-1].resultado == TIMEOUT:
        raise _com_tentativas(ErroOrcamento(
            f"O provedor não respondeu a tempo em {MAX_TENTATIVAS} tentativas. Último erro: {ultimo_erro}"
        ), tentativas)
    raise _com_tentativas(ErroModelo(
        f"Não foi possível obter um modelo válido após {MAX_TENTATIVAS} tentativas. "
        f"Último erro: {ultimo_erro}",
        ultimos_erros,
    ), tentativas)


def _com_tentativas(erro: Exception, tentativas: list[Tentativa]) -> Exception:
    """Anexa ao erro as tentativas feitas até a falha (usado pela avaliação)."""
    erro.tentativas = list(tentativas)
    return erro


def gerar_modelo(req: Requisicao, chamar=chamar_llm) -> ModeloEstados:
    """Atalho que devolve só o modelo extraído."""
    return gerar(req, chamar=chamar).modelo
