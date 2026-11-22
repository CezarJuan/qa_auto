"""Validação do modelo de estados: estrutura, referências, alcançabilidade, critérios e determinismo.

Todos os erros são coletados de uma vez, com código, elementos envolvidos e mensagem em português,
ordenados do mais estrutural ao mais fino, para que o LLM consiga corrigir tudo numa tentativa.
"""
import itertools
import json
import re
from collections import deque
from dataclasses import dataclass
from datetime import date, timedelta

from pydantic import ValidationError

from sistemas_exemplo import Catalogo

from . import expressoes
from .expressoes import ErroExpressao
from .schemas import ModeloEstados, numeros_de_criterios

LIMITE_COMBINACOES = 10_000
DATA_BASE = "2000-01-01"

# Grupos, do mais estrutural ao mais fino
ESQUEMA, REFERENCIAS, INICIAL_FINAL, ALCANCABILIDADE, CRITERIOS, DETERMINISMO = range(6)


@dataclass(frozen=True)
class ErroValidacao:
    codigo: str
    elementos: tuple[str, ...]
    mensagem: str
    grupo: int = ESQUEMA

    def como_dict(self) -> dict:
        return {"codigo": self.codigo, "elementos": list(self.elementos), "mensagem": self.mensagem}


class ErroModelo(Exception):
    """A resposta do LLM não gerou um modelo de estados válido."""

    def __init__(self, mensagem: str, erros: list[ErroValidacao] | None = None):
        super().__init__(mensagem)
        self.erros = erros or []


def descrever(erros: list[ErroValidacao]) -> str:
    return "\n".join(f"- [{e.codigo}] {e.mensagem}" for e in erros)


def extrair_json(texto: str) -> dict:
    """Remove cercas de markdown / texto extra e converte para dict."""
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE)
    ini, fim = texto.find("{"), texto.rfind("}")
    if ini == -1 or fim == -1 or fim < ini:
        raise ErroModelo(
            "A resposta não contém um objeto JSON.",
            [ErroValidacao("json_ausente", (), "A resposta não contém um objeto JSON.")],
        )
    try:
        return json.loads(texto[ini : fim + 1])
    except json.JSONDecodeError as e:
        raise ErroModelo(
            f"JSON inválido: {e}", [ErroValidacao("json_invalido", (), f"JSON inválido: {e}")]
        ) from e


# ---------------------------------------------------------------- grupos de regras
def _esquema(modelo: ModeloEstados) -> list[ErroValidacao]:
    erros = []
    for nome, itens in (
        ("estado", [e.id for e in modelo.estados]),
        ("transição", [t.id for t in modelo.transicoes]),
        ("variável", [v.nome for v in modelo.variaveis]),
    ):
        repetidos = sorted({i for i in itens if itens.count(i) > 1})
        if repetidos:
            erros.append(ErroValidacao(
                "id_duplicado", tuple(repetidos),
                f"Há {nome} com identificador repetido: {', '.join(repetidos)}. Use um id único para cada um.",
            ))
    if not modelo.estados:
        erros.append(ErroValidacao("sem_estados", (), "A lista de estados está vazia."))
    if not modelo.transicoes:
        erros.append(ErroValidacao("sem_transicoes", (), "Não há nenhuma transição."))
    return erros


def _referencias(modelo: ModeloEstados, catalogo: Catalogo | None) -> list[ErroValidacao]:
    erros = []
    estados = {e.id for e in modelo.estados}
    variaveis = {v.nome: v for v in modelo.variaveis}
    tipos = {v.nome: v.tipo for v in modelo.variaveis}

    def erro(codigo, elementos, mensagem):
        erros.append(ErroValidacao(codigo, tuple(elementos), mensagem, REFERENCIAS))

    for t in modelo.transicoes:
        for papel, alvo in (("origem", t.de), ("destino", t.para)):
            if alvo not in estados:
                erro("estado_inexistente", (t.id, alvo),
                     f"A transição {t.id} usa o estado de {papel} '{alvo}', que não está na lista de estados.")
        if t.guarda:
            try:
                arvore = expressoes.analisar_guarda(t.guarda)
            except ErroExpressao as e:
                erro("guarda_invalida", (t.id,), f"Guarda de {t.id}: {e}")
            else:
                for nome in sorted(expressoes.variaveis_usadas(arvore) - set(variaveis)):
                    erro("variavel_nao_declarada", (t.id, nome),
                         f"A guarda de {t.id} usa a variável '{nome}', que não foi declarada.")
                if expressoes.variaveis_usadas(arvore) <= set(variaveis):
                    try:
                        if expressoes.inferir_tipo(arvore, tipos) != "booleano":
                            erro("guarda_nao_booleana", (t.id,),
                                 f"A guarda de {t.id} ('{t.guarda}') não é uma condição verdadeira/falsa.")
                    except ErroExpressao as e:
                        erro("tipo_incompativel", (t.id,), f"Guarda de {t.id}: {e}")
        for texto in t.acoes:
            try:
                acao = expressoes.analisar_acao(texto)
            except ErroExpressao as e:
                erro("acao_invalida", (t.id,), f"Ação de {t.id}: {e}")
                continue
            alvo = variaveis.get(acao.alvo)
            if alvo is None:
                erro("variavel_nao_declarada", (t.id, acao.alvo),
                     f"A ação '{texto}' de {t.id} altera '{acao.alvo}', que não foi declarada.")
                continue
            if alvo.categoria != "estado":
                erro("acao_sobre_nao_estado", (t.id, acao.alvo),
                     f"A ação '{texto}' de {t.id} altera '{acao.alvo}', que é variável de {alvo.categoria}. "
                     "Ações só podem alterar variáveis de estado.")
            faltando = sorted(expressoes.variaveis_usadas(acao.expressao) - set(variaveis))
            for nome in faltando:
                erro("variavel_nao_declarada", (t.id, nome),
                     f"A ação '{texto}' de {t.id} usa a variável '{nome}', que não foi declarada.")
            if not faltando:
                try:
                    origem = expressoes.inferir_tipo(acao.expressao, tipos)
                    if acao.operador != "=" and alvo.tipo not in expressoes.NUMERICOS:
                        raise ErroExpressao(f"'{acao.operador}' só se aplica a variáveis numéricas.")
                    if not expressoes.tipo_compativel(alvo.tipo, origem):
                        raise ErroExpressao(f"'{acao.alvo}' é {alvo.tipo} e recebe um valor {origem}.")
                except ErroExpressao as e:
                    erro("tipo_incompativel", (t.id, acao.alvo), f"Ação '{texto}' de {t.id}: {e}")

    if catalogo:
        fora = sorted(estados - set(catalogo.estados))
        if fora:
            erro("estado_fora_do_catalogo", fora, f"Estados fora do catálogo: {', '.join(fora)}.")
        fora = sorted({t.evento for t in modelo.transicoes} - set(catalogo.eventos))
        if fora:
            erro("evento_fora_do_catalogo", fora, f"Eventos fora do catálogo: {', '.join(fora)}.")
        fora = sorted(set(variaveis) - set(catalogo.variaveis))
        if fora:
            erro("variavel_fora_do_catalogo", fora, f"Variáveis fora do catálogo: {', '.join(fora)}.")
        iniciais = [e.id for e in modelo.estados if e.tipo == "inicial"]
        if iniciais and iniciais != [catalogo.inicial]:
            erro("inicial_divergente", (catalogo.inicial, *iniciais),
                 f"O estado inicial deve ser '{catalogo.inicial}', mas o modelo usa '{', '.join(iniciais)}'.")
    return erros


def _inicial_final(modelo: ModeloEstados) -> list[ErroValidacao]:
    erros = []
    iniciais = [e.id for e in modelo.estados if e.tipo == "inicial"]
    if len(iniciais) != 1:
        texto = ", ".join(iniciais) if iniciais else "nenhum"
        erros.append(ErroValidacao("inicial_nao_unico", tuple(iniciais),
                                   f"O modelo deve ter exatamente um estado inicial; tem: {texto}.",
                                   INICIAL_FINAL))
    finais = {e.id for e in modelo.estados if e.tipo == "final"}
    if not finais:
        erros.append(ErroValidacao("sem_estado_final", (),
                                   "O modelo precisa de ao menos um estado do tipo final.", INICIAL_FINAL))
    for t in modelo.transicoes:
        if t.de in finais:
            erros.append(ErroValidacao("final_com_saida", (t.de, t.id),
                                       f"'{t.de}' é final e tem a transição de saída {t.id}. "
                                       "Estados finais não podem ter saída.", INICIAL_FINAL))
    return erros


def _alcancabilidade(modelo: ModeloEstados) -> list[ErroValidacao]:
    iniciais = [e.id for e in modelo.estados if e.tipo == "inicial"]
    if len(iniciais) != 1:
        return []  # sem um inicial único não há de onde partir; o erro já foi reportado
    estados = [e.id for e in modelo.estados]
    finais = {e.id for e in modelo.estados if e.tipo == "final"}
    saidas: dict[str, set[str]] = {e: set() for e in estados}
    entradas: dict[str, set[str]] = {e: set() for e in estados}
    for t in modelo.transicoes:
        if t.de in saidas and t.para in saidas:
            saidas[t.de].add(t.para)
            entradas[t.para].add(t.de)

    def busca(inicio: set[str], vizinhos: dict[str, set[str]]) -> set[str]:
        vistos, fila = set(inicio), deque(inicio)
        while fila:
            for prox in vizinhos[fila.popleft()]:
                if prox not in vistos:
                    vistos.add(prox)
                    fila.append(prox)
        return vistos

    alcancaveis = busca({iniciais[0]}, saidas)
    chegam_ao_final = busca(finais, entradas)
    erros = []
    for e in estados:
        if e not in alcancaveis:
            erros.append(ErroValidacao("estado_inalcancavel", (e,),
                                       f"O estado '{e}' é inalcançável a partir do inicial.", ALCANCABILIDADE))
        elif finais and e not in chegam_ao_final:
            if not saidas[e]:
                mensagem = f"'{e}' é um beco sem saída: não tem transição de saída e não é final."
            else:
                mensagem = f"De '{e}' não há caminho até nenhum estado final."
            erros.append(ErroValidacao("sem_caminho_ao_final", (e,), mensagem, ALCANCABILIDADE))
    return erros


def _criterios(modelo: ModeloEstados, criterios: str) -> list[ErroValidacao]:
    esperados = numeros_de_criterios(criterios)
    erros = []
    if esperados:
        for t in modelo.transicoes:
            for n in sorted(set(t.criterios) - esperados):
                erros.append(ErroValidacao("criterio_inexistente", (t.id, str(n)),
                                           f"A transição {t.id} cita o critério {n}, que não existe.", CRITERIOS))
    cobertos = {n for t in modelo.transicoes for n in t.criterios}
    for n in sorted(esperados - cobertos):
        erros.append(ErroValidacao("criterio_nao_coberto", (str(n),),
                                   f"O critério {n} não está representado em nenhuma transição.", CRITERIOS))
    return erros


# ---------------------------------------------------------------- determinismo
def _vizinhos(valor, tipo: str) -> list:
    if tipo == "data":
        dia = date.fromisoformat(valor)
        return [(dia + timedelta(days=d)).isoformat() for d in (-1, 0, 1)]
    passo = 1 if tipo == "inteiro" else 0.01
    return [round(valor - passo, 2), valor, round(valor + passo, 2)]


def candidatos(arvores: list, variaveis: dict) -> dict[str, list]:
    """Valores de fronteira por variável usada nas guardas: literais ±1 (±0,01; ±1 dia), 0 e o inicial."""
    usadas = sorted(set().union(*(expressoes.variaveis_usadas(a) for a in arvores)) & set(variaveis))
    literais = [v for a in arvores for v in expressoes.literais(a)]
    numeros = [v for v in literais if isinstance(v, (int, float)) and not isinstance(v, bool)]
    datas = [v for v in literais if isinstance(v, str) and expressoes.DATA_ISO.match(v)]
    resultado = {}
    for nome in usadas:
        v = variaveis[nome]
        if v.tipo == "booleano":
            resultado[nome] = [False, True]
            continue
        if v.tipo == "data":
            base = datas or [DATA_BASE]
            iniciais = [v.valor_inicial] if v.valor_inicial is not None else []
            valores = {d for b in base + iniciais for d in _vizinhos(b, "data")}
        else:
            # Os literais de todas as guardas formam um conjunto comum: assim comparações entre
            # variáveis (valor <= saldo) também passam pelos pontos de igualdade.
            iniciais = [v.valor_inicial] if v.valor_inicial is not None else []
            valores = {0}
            for n in numeros + iniciais:
                valores.update(_vizinhos(n, v.tipo))
            if v.tipo == "inteiro":
                valores = {int(x) for x in valores if float(x).is_integer()}
        resultado[nome] = sorted(valores)
    return resultado


def _sobreposicao(t1, t2, variaveis: dict) -> dict | None:
    """Primeira valoração (em ordem determinística) que satisfaz as duas guardas, se houver."""
    arvores = [expressoes.analisar_guarda(t1.guarda), expressoes.analisar_guarda(t2.guarda)]
    valores = candidatos(arvores, variaveis)
    nomes = list(valores)
    for combinacao in itertools.islice(itertools.product(*(valores[n] for n in nomes)), LIMITE_COMBINACOES):
        valoracao = dict(zip(nomes, combinacao))
        try:
            if all(expressoes.avaliar(a, valoracao) for a in arvores):
                return valoracao
        except (ErroExpressao, TypeError, ArithmeticError):
            continue
    return None


def _normalizar_guarda(guarda: str | None) -> str:
    if not guarda:
        return ""
    try:
        return expressoes.formatar(guarda)
    except ErroExpressao:
        return guarda.strip()


def _determinismo(modelo: ModeloEstados, guardas_validas: bool) -> list[ErroValidacao]:
    erros = []
    variaveis = {v.nome: v for v in modelo.variaveis}
    grupos: dict[tuple[str, str], list] = {}
    for t in modelo.transicoes:
        grupos.setdefault((t.de, t.evento), []).append(t)
    for (origem, evento), transicoes in grupos.items():
        if len(transicoes) < 2:
            continue
        unicas = []
        for t in transicoes:
            igual = next(
                (u for u in unicas
                 if u.para == t.para and _normalizar_guarda(u.guarda) == _normalizar_guarda(t.guarda)),
                None,
            )
            if igual:
                erros.append(ErroValidacao("transicao_duplicada", (igual.id, t.id),
                                           f"As transições {igual.id} e {t.id} são iguais "
                                           f"({origem} --{evento}--> {t.para}). Remova uma delas.", DETERMINISMO))
            else:
                unicas.append(t)
        if len(unicas) < 2:
            continue
        sem_guarda = [t.id for t in unicas if not t.guarda]
        if sem_guarda:
            ids = ", ".join(t.id for t in unicas)
            erros.append(ErroValidacao("transicao_ambigua", (origem, evento, *sem_guarda),
                                       f"O par {origem} / {evento} tem várias transições ({ids}), e "
                                       f"{', '.join(sem_guarda)} não tem guarda. Quando um estado tem mais de "
                                       "uma transição com o mesmo evento, todas precisam de guardas que não "
                                       "se sobreponham.", DETERMINISMO))
            continue
        if not guardas_validas:
            continue
        for t1, t2 in itertools.combinations(unicas, 2):
            valoracao = _sobreposicao(t1, t2, variaveis)
            if valoracao is not None:
                exemplo = ", ".join(f"{k} = {v}" for k, v in valoracao.items())
                erros.append(ErroValidacao("guardas_sobrepostas", (t1.id, t2.id, origem, evento),
                                           f"As guardas de {t1.id} ('{t1.guarda}') e {t2.id} ('{t2.guarda}') "
                                           f"no par {origem} / {evento} se sobrepõem: com {exemplo} as duas "
                                           "são verdadeiras.", DETERMINISMO))
    return erros


# ---------------------------------------------------------------- entrada pública
def validar_modelo(
    modelo: ModeloEstados, criterios: str = "", catalogo: Catalogo | None = None
) -> list[ErroValidacao]:
    """Todos os erros do modelo, ordenados do mais estrutural ao mais fino."""
    referencias = _referencias(modelo, catalogo)
    guardas_validas = not any(e.codigo in {"guarda_invalida", "variavel_nao_declarada", "tipo_incompativel"}
                              for e in referencias)
    erros = [
        *_esquema(modelo),
        *referencias,
        *_inicial_final(modelo),
        *_alcancabilidade(modelo),
        *_criterios(modelo, criterios),
        *_determinismo(modelo, guardas_validas),
    ]
    return sorted(erros, key=lambda e: e.grupo)


def erros_de_esquema(e: ValidationError) -> list[ErroValidacao]:
    erros = []
    for err in e.errors():
        local = ".".join(map(str, err["loc"]))
        mensagem = str(err["msg"]).replace("Value error, ", "")
        erros.append(ErroValidacao("esquema_invalido", (local,), f"{local}: {mensagem}" if local else mensagem))
    return erros


def validar_resposta(texto: str, criterios: str = "", catalogo: Catalogo | None = None) -> ModeloEstados:
    """Converte a resposta do LLM em modelo válido ou lança ErroModelo com todos os erros."""
    dados = extrair_json(texto)
    try:
        modelo = ModeloEstados.model_validate(dados)
    except ValidationError as e:
        erros = erros_de_esquema(e)
        raise ErroModelo(f"Estrutura inválida:\n{descrever(erros)}", erros) from e
    erros = validar_modelo(modelo, criterios, catalogo)
    if erros:
        raise ErroModelo(f"O modelo tem {len(erros)} erro(s):\n{descrever(erros)}", erros)
    return modelo
