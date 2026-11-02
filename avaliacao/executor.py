"""Executor da avaliação: roda a extração N vezes por caso, calcula métricas e grava os resultados.

Saída: resultados/<AAAAMMDD-HHMM>_<provedor>_<modelo>_<prompt>/ com config.json, rodadas/*.json,
resumo.csv e relatorio.md.
"""
import csv
import json
import os
import re
import statistics
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from backend import servico
from backend.llm import ErroLLM
from backend.prompts import EXEMPLOS_DO_PROMPT, SYSTEM_PROMPT, VERSAO_PROMPT
from backend.schemas import Requisicao
from backend.servico import ErroOrcamento
from backend.validacao import ErroModelo

from .alinhamento import Embeddings, normalizar
from .casos import TESTE, Caso, carregar_conjunto
from .metricas import calcular

RAIZ = Path(__file__).resolve().parent.parent
SAIDA_PADRAO = RAIZ / "resultados"
PROVEDORES = {"ollama": ("Ollama (Local)", "OLLAMA_MODEL"), "gemini": ("Gemini (Cloud)", "GEMINI_MODEL")}
SEGUNDOS_TIPICOS_POR_EXTRACAO = 60

COLUNAS = [
    "caso", "conjunto", "rodada", "valido", "timeout", "tentativas", "primeira_tentativa_valida", "duracao_s",
    "precisao_estados", "recall_estados", "precisao_transicoes", "recall_transicoes", "propriedades", "erro",
]
METRICAS = [
    ("valido", "Validade"),
    ("primeira_tentativa_valida", "Válido na 1ª tentativa"),
    ("precisao_estados", "Precisão de estados"),
    ("recall_estados", "Recall de estados"),
    ("precisao_transicoes", "Precisão de transições"),
    ("recall_transicoes", "Recall de transições"),
    ("propriedades", "Propriedades satisfeitas"),
    ("timeout", "Timeout"),
    ("duracao_s", "Duração (s)"),
]


class ErroVazamento(ValueError):
    """O prompt usa como exemplo um caso do conjunto de teste."""


@dataclass
class Configuracao:
    provedor: str
    modelo: str
    rodadas: int = 3
    conjunto: str = TESTE
    casos: list[str] | None = None
    versao_prompt: str = VERSAO_PROMPT
    alinhamento_semantico: bool = False


@dataclass
class Rodada:
    caso: str
    conjunto: str
    rodada: int
    valido: bool = False
    timeout: bool = False
    tentativas: int = 0
    primeira_tentativa_valida: bool = False
    duracao_s: float = 0.0
    precisao_estados: float = 0.0
    recall_estados: float = 0.0
    precisao_transicoes: float = 0.0
    recall_transicoes: float = 0.0
    propriedades: float = 0.0
    erro: str = ""
    detalhes_propriedades: list[dict] = field(default_factory=list)
    nao_mapeados: dict[str, list[str]] = field(default_factory=dict)
    historico: list[dict] = field(default_factory=list)
    modelo: dict | None = None


# ---------------------------------------------------------------- vazamento
def casos_vazados(casos_teste: list[Caso], exemplos_do_prompt: list[str], texto_prompt: str) -> list[str]:
    """Casos de teste declarados como exemplo do prompt ou cujo texto aparece no prompt."""
    texto = normalizar(texto_prompt)
    vazados = []
    for caso in casos_teste:
        if caso.id in exemplos_do_prompt:
            vazados.append(caso.id)
            continue
        trechos = [caso.historia, *caso.criterios.values()]
        if any(len(normalizar(t)) >= 20 and normalizar(t) in texto for t in trechos):
            vazados.append(caso.id)
    return vazados


def verificar_vazamento(casos_teste: list[Caso], versao_prompt: str,
                        exemplos_do_prompt: list[str] | None = None, texto_prompt: str | None = None) -> None:
    exemplos = EXEMPLOS_DO_PROMPT.get(versao_prompt, []) if exemplos_do_prompt is None else exemplos_do_prompt
    vazados = casos_vazados(casos_teste, exemplos, SYSTEM_PROMPT if texto_prompt is None else texto_prompt)
    if vazados:
        raise ErroVazamento(
            f"O prompt {versao_prompt} usa caso(s) do conjunto de teste como exemplo: {', '.join(vazados)}. "
            "Troque o exemplo ou mova o caso para o conjunto de desenvolvimento."
        )


# ---------------------------------------------------------------- execução
@contextmanager
def _modelo_configurado(provedor: str, modelo: str):
    variavel = PROVEDORES[provedor][1]
    anterior = os.environ.get(variavel)
    os.environ[variavel] = modelo
    try:
        yield
    finally:
        if anterior is None:
            os.environ.pop(variavel, None)
        else:
            os.environ[variavel] = anterior


def _slug(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9.]+", "-", texto).strip("-")


def _pasta_execucao(base: Path, config: Configuracao, agora: datetime) -> Path:
    nome = f"{agora:%Y%m%d-%H%M}_{config.provedor}_{_slug(config.modelo)}_{config.versao_prompt}"
    pasta, n = base / nome, 2
    while pasta.exists():
        pasta, n = base / f"{nome}-{n}", n + 1
    return pasta


def estimativa(n_extracoes: int) -> str:
    tipico = n_extracoes * SEGUNDOS_TIPICOS_POR_EXTRACAO / 60
    pior = n_extracoes * servico.orcamento_segundos() / 60
    return f"{n_extracoes} extrações; estimativa de ~{tipico:.0f} min (pior caso {pior:.0f} min)"


def avaliar_rodada(caso: Caso, n: int, config: Configuracao, gerar, embeddings: Embeddings | None) -> Rodada:
    rodada = Rodada(caso.id, caso.conjunto, n)
    req = Requisicao(
        user_story=caso.historia,
        criterios=caso.criterios_texto,
        motor=PROVEDORES[config.provedor][0],
        sistema=caso.sistema,
    )
    t0 = time.perf_counter()
    try:
        resultado = gerar(req)
    except Exception as e:  # noqa: BLE001 - uma falha não pode interromper a avaliação inteira
        rodada.timeout = isinstance(e, ErroOrcamento)
        conhecido = isinstance(e, (ErroOrcamento, ErroModelo, ErroLLM))
        rodada.erro = str(e) if conhecido else f"{type(e).__name__}: {e}"
        tentativas = getattr(e, "tentativas", [])
        rodada.tentativas = len(tentativas)
        rodada.historico = [asdict(t) for t in tentativas]
    else:
        modelo = resultado.modelo.model_dump()
        qualidade = calcular(modelo, caso, embeddings)
        rodada.valido = True
        rodada.modelo = modelo
        rodada.tentativas = len(resultado.tentativas)
        rodada.primeira_tentativa_valida = rodada.tentativas == 1
        rodada.historico = [asdict(t) for t in resultado.tentativas]
        for campo in ("precisao_estados", "recall_estados", "precisao_transicoes", "recall_transicoes",
                      "propriedades"):
            setattr(rodada, campo, round(getattr(qualidade, campo), 4))
        rodada.detalhes_propriedades = [asdict(d) for d in qualidade.detalhes_propriedades]
        rodada.nao_mapeados = qualidade.nao_mapeados
    rodada.duracao_s = round(time.perf_counter() - t0, 2)
    return rodada


def executar(config: Configuracao, casos: list[Caso] | None = None, saida: Path = SAIDA_PADRAO,
             gerar=None, embeddings: Embeddings | None = None, agora: datetime | None = None,
             exemplos_do_prompt: list[str] | None = None, texto_prompt: str | None = None,
             mensagem=print) -> Path:
    """Roda a avaliação e devolve a pasta com os resultados."""
    if config.provedor not in PROVEDORES:
        raise ValueError(f"Provedor desconhecido: {config.provedor} (use ollama ou gemini)")
    todos = carregar_conjunto()
    verificar_vazamento([c for c in todos if c.conjunto == TESTE], config.versao_prompt,
                        exemplos_do_prompt, texto_prompt)
    if casos is None:
        casos = carregar_conjunto(conjunto=config.conjunto, ids=config.casos)
    if not casos:
        raise ValueError("Nenhum caso selecionado.")
    if config.alinhamento_semantico and embeddings is None:
        from .alinhamento import embeddings_ollama

        embeddings = embeddings_ollama
    gerar = gerar or servico.gerar

    pasta = _pasta_execucao(Path(saida), config, agora or datetime.now())
    (pasta / "rodadas").mkdir(parents=True)
    (pasta / "config.json").write_text(
        json.dumps({**asdict(config), "casos_avaliados": [c.id for c in casos]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    mensagem(f"Avaliação em {pasta}: {estimativa(len(casos) * config.rodadas)}")

    rodadas: list[Rodada] = []
    with _modelo_configurado(config.provedor, config.modelo):
        for caso in casos:
            for n in range(1, config.rodadas + 1):
                rodada = avaliar_rodada(caso, n, config, gerar, embeddings)
                rodadas.append(rodada)
                (pasta / "rodadas" / f"{caso.id}_{n}.json").write_text(
                    json.dumps(asdict(rodada), ensure_ascii=False, indent=2), encoding="utf-8"
                )
                situacao = "válido" if rodada.valido else ("timeout" if rodada.timeout else "inválido")
                mensagem(f"  {caso.id} #{n}: {situacao}, propriedades {rodada.propriedades:.2f}, "
                         f"{rodada.duracao_s:.0f}s")
    _gravar_resumo(pasta, rodadas)
    (pasta / "relatorio.md").write_text(relatorio(config, casos, rodadas), encoding="utf-8")
    return pasta


# ---------------------------------------------------------------- saída
def _gravar_resumo(pasta: Path, rodadas: list[Rodada]) -> None:
    with (pasta / "resumo.csv").open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        escritor.writeheader()
        for r in rodadas:
            linha = {c: getattr(r, c) for c in COLUNAS}
            for c in ("valido", "timeout", "primeira_tentativa_valida"):
                linha[c] = int(linha[c])
            escritor.writerow(linha)


def _media_dp(valores: list[float]) -> tuple[float, float]:
    if not valores:
        return 0.0, 0.0
    return statistics.fmean(valores), statistics.stdev(valores) if len(valores) > 1 else 0.0


def _fmt(media: float, dp: float, chave: str) -> str:
    return f"{media:.1f} ± {dp:.1f}" if chave == "duracao_s" else f"{media:.2f} ± {dp:.2f}"


def relatorio(config: Configuracao, casos: list[Caso], rodadas: list[Rodada]) -> str:
    linhas = [
        f"# Avaliação: {config.provedor} / {config.modelo} / {config.versao_prompt}",
        "",
        f"- Conjunto: {config.conjunto}; casos: {len(casos)}; rodadas por caso: {config.rodadas}; "
        f"total de rodadas: {len(rodadas)}",
        f"- Alinhamento semântico: {'sim' if config.alinhamento_semantico else 'não'}",
        "",
        "## Total",
        "",
        "| Métrica | Média ± desvio padrão |",
        "|---|---|",
    ]
    for chave, nome in METRICAS:
        linhas.append(f"| {nome} | {_fmt(*_media_dp([float(getattr(r, chave)) for r in rodadas]), chave)} |")
    validas_1a = sum(r.primeira_tentativa_valida for r in rodadas)
    linhas += ["", f"Taxa de validade na primeira tentativa: {validas_1a}/{len(rodadas)} "
                   f"({validas_1a / len(rodadas):.0%}).", "", "## Por caso", "",
               "| Caso | Conjunto | Validade | Precisão estados | Recall estados | Precisão transições "
               "| Recall transições | Propriedades | Duração (s) |",
               "|---|---|---|---|---|---|---|---|---|"]
    por_caso = defaultdict(list)
    for r in rodadas:
        por_caso[r.caso].append(r)
    for caso in casos:
        rs = por_caso[caso.id]
        celulas = [_fmt(*_media_dp([float(getattr(r, c)) for r in rs]), c) for c in (
            "valido", "precisao_estados", "recall_estados", "precisao_transicoes", "recall_transicoes",
            "propriedades", "duracao_s")]
        linhas.append(f"| {caso.id} | {caso.conjunto} | " + " | ".join(celulas) + " |")

    falhas = Counter()
    motivos = defaultdict(Counter)
    for r in rodadas:
        for d in r.detalhes_propriedades:
            if not d["satisfeita"]:
                chave = (r.caso, d["criterio"], d["descricao"])
                falhas[chave] += 1
                motivos[chave][d["motivo"]] += 1
    linhas += ["", "## Propriedades que mais falharam", ""]
    if falhas:
        linhas += ["| Caso | Critério | Propriedade | Falhas | Motivo mais comum |", "|---|---|---|---|---|"]
        for (caso, criterio, descricao), n in falhas.most_common(15):
            motivo = motivos[(caso, criterio, descricao)].most_common(1)[0][0]
            linhas.append(f"| {caso} | {criterio} | {descricao} | {n} | {motivo} |")
    else:
        linhas.append("Nenhuma propriedade falhou nas rodadas válidas.")

    linhas += ["", "## Elementos não mapeados", "",
               "Nomes do modelo extraído sem correspondência no gabarito. Revise se faltam sinônimos.", ""]
    nao_mapeados = defaultdict(Counter)
    for r in rodadas:
        for categoria, nomes in r.nao_mapeados.items():
            for nome in nomes:
                nao_mapeados[(r.caso, categoria)][nome] += 1
    if nao_mapeados:
        for (caso, categoria), nomes in sorted(nao_mapeados.items()):
            lista = ", ".join(f"{n} ({q}x)" for n, q in nomes.most_common())
            linhas.append(f"- {caso} / {categoria}: {lista}")
    else:
        linhas.append("Nenhum.")

    erros = [r for r in rodadas if not r.valido]
    linhas += ["", "## Rodadas inválidas", ""]
    if erros:
        linhas += [f"- {r.caso} #{r.rodada} ({'timeout' if r.timeout else 'inválida'}): {r.erro[:300]}"
                   for r in erros]
    else:
        linhas.append("Nenhuma.")
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------- comparação
def _ler_execucao(pasta: Path) -> tuple[str, dict[str, float]]:
    config = json.loads((pasta / "config.json").read_text(encoding="utf-8"))
    with (pasta / "resumo.csv").open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    medias = {chave: statistics.fmean(float(l[chave]) for l in linhas) if linhas else 0.0 for chave, _ in METRICAS}
    rotulo = f"{config['provedor']}/{config['modelo']}/{config['versao_prompt']}"
    return rotulo, medias


def comparar(pastas: list[Path]) -> str:
    """Tabela com a média de cada métrica por execução e a diferença em relação à primeira."""
    if len(pastas) < 2:
        raise ValueError("Informe ao menos duas execuções para comparar.")
    execucoes = [_ler_execucao(Path(p)) for p in pastas]
    rotulos = [r for r, _ in execucoes]
    cabecalho = "| Métrica | " + " | ".join(rotulos) + " | " + " | ".join(
        f"Δ {r} − {rotulos[0]}" for r in rotulos[1:]) + " |"
    linhas = ["# Comparação de avaliações", "", cabecalho, "|" + "---|" * (1 + 2 * len(rotulos) - 1)]
    for chave, nome in METRICAS:
        valores = [m[chave] for _, m in execucoes]
        casas = 1 if chave == "duracao_s" else 2
        celulas = [f"{v:.{casas}f}" for v in valores] + [f"{v - valores[0]:+.{casas}f}" for v in valores[1:]]
        linhas.append(f"| {nome} | " + " | ".join(celulas) + " |")
    return "\n".join(linhas) + "\n"
