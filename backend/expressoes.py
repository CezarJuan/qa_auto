"""Linguagem restrita de guardas e ações do modelo de estados.

Guardas: variáveis, literais, `+ - %`, comparações `== != < <= > >=`, `e`, `ou`, `não` e parênteses.
Ações: `x = expr`, `x += expr`, `x -= expr`.

O texto é traduzido para a sintaxe do Python, analisado com `ast` e aceito só se usar os nós
permitidos. A avaliação é feita por um interpretador próprio sobre a árvore, nunca com `eval`.
"""
import ast
import operator
import re
from dataclasses import dataclass
from datetime import date

DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_TRADUCOES = [
    (re.compile(r"\bnão\b|\bnao\b", re.IGNORECASE), "not"),
    (re.compile(r"\be\b", re.IGNORECASE), "and"),
    (re.compile(r"\bou\b", re.IGNORECASE), "or"),
    (re.compile(r"\bverdadeiro\b", re.IGNORECASE), "True"),
    (re.compile(r"\bfalso\b", re.IGNORECASE), "False"),
]

_COMPARACOES = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}
_ARITMETICA = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mod: operator.mod}
_SIMBOLO = {
    ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=",
    ast.Add: "+", ast.Sub: "-", ast.Mod: "%",
}
_ATRIBUICOES = {None: "=", ast.Add: "+=", ast.Sub: "-="}

NUMERICOS = {"inteiro", "decimal"}


class ErroExpressao(ValueError):
    """Guarda ou ação fora da linguagem permitida, ou impossível de avaliar."""


@dataclass(frozen=True)
class Acao:
    alvo: str
    operador: str  # "=", "+=" ou "-="
    expressao: ast.expr


def _traduzir(texto: str) -> str:
    # Literais entre aspas (datas) não são traduzidos
    partes = re.split(r"('[^']*'|\"[^\"]*\")", texto)
    for i in range(0, len(partes), 2):
        for padrao, python in _TRADUCOES:
            partes[i] = padrao.sub(python, partes[i])
    return "".join(partes)


def _verificar(no: ast.AST, texto: str) -> None:
    """Rejeita qualquer nó fora da linguagem."""
    if isinstance(no, ast.BoolOp):
        for v in no.values:
            _verificar(v, texto)
    elif isinstance(no, ast.Compare):
        if not all(type(op) in _COMPARACOES for op in no.ops):
            raise ErroExpressao(f"Comparação não permitida em '{texto}'.")
        for v in [no.left, *no.comparators]:
            _verificar(v, texto)
    elif isinstance(no, ast.BinOp):
        if type(no.op) not in _ARITMETICA:
            raise ErroExpressao(f"Operador não permitido em '{texto}' (use só + - %).")
        _verificar(no.left, texto)
        _verificar(no.right, texto)
    elif isinstance(no, ast.UnaryOp):
        if not isinstance(no.op, (ast.Not, ast.USub)):
            raise ErroExpressao(f"Operador não permitido em '{texto}'.")
        _verificar(no.operand, texto)
    elif isinstance(no, ast.Name):
        if not isinstance(no.ctx, ast.Load):
            raise ErroExpressao(f"Uso inválido de '{no.id}' em '{texto}'.")
    elif isinstance(no, ast.Constant):
        if not isinstance(no.value, (bool, int, float, str)):
            raise ErroExpressao(f"Literal não permitido em '{texto}'.")
    else:
        raise ErroExpressao(
            f"'{texto}' usa uma construção não permitida ({type(no).__name__}). "
            "Use só variáveis, literais, + - %, comparações, e, ou, não."
        )


def analisar_guarda(texto: str) -> ast.expr:
    """Converte o texto da guarda em árvore validada."""
    try:
        arvore = ast.parse(_traduzir(texto).strip(), mode="eval").body
    except SyntaxError as e:
        raise ErroExpressao(f"Guarda com sintaxe inválida: '{texto}'.") from e
    _verificar(arvore, texto)
    return arvore


def analisar_acao(texto: str) -> Acao:
    """Converte `x = expr`, `x += expr` ou `x -= expr` em ação validada."""
    try:
        modulo = ast.parse(_traduzir(texto).strip(), mode="exec")
    except SyntaxError as e:
        raise ErroExpressao(f"Ação com sintaxe inválida: '{texto}'.") from e
    if len(modulo.body) != 1:
        raise ErroExpressao(f"Cada ação deve ter uma única atribuição: '{texto}'.")
    instrucao = modulo.body[0]
    if isinstance(instrucao, ast.Assign) and len(instrucao.targets) == 1:
        alvo, op, valor = instrucao.targets[0], None, instrucao.value
    elif isinstance(instrucao, ast.AugAssign) and type(instrucao.op) in (ast.Add, ast.Sub):
        alvo, op, valor = instrucao.target, type(instrucao.op), instrucao.value
    else:
        raise ErroExpressao(f"Ação deve ser 'x = expr', 'x += expr' ou 'x -= expr': '{texto}'.")
    if not isinstance(alvo, ast.Name):
        raise ErroExpressao(f"O alvo da ação deve ser uma variável: '{texto}'.")
    _verificar(valor, texto)
    return Acao(alvo.id, _ATRIBUICOES[op], valor)


def variaveis_usadas(arvore: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(arvore) if isinstance(n, ast.Name)}


def literais(arvore: ast.AST) -> list:
    return [n.value for n in ast.walk(arvore) if isinstance(n, ast.Constant)]


# ---------------------------------------------------------------- avaliação
def _como_data(valor):
    if isinstance(valor, str) and DATA_ISO.match(valor):
        return date.fromisoformat(valor)
    return valor


def avaliar(arvore: ast.expr, valores: dict):
    """Interpretador da linguagem: só os nós aceitos por `_verificar` chegam aqui."""
    if isinstance(arvore, ast.Constant):
        return _como_data(arvore.value)
    if isinstance(arvore, ast.Name):
        if arvore.id not in valores:
            raise ErroExpressao(f"Variável sem valor: '{arvore.id}'.")
        return _como_data(valores[arvore.id])
    if isinstance(arvore, ast.BoolOp):
        if isinstance(arvore.op, ast.And):
            return all(bool(avaliar(v, valores)) for v in arvore.values)
        return any(bool(avaliar(v, valores)) for v in arvore.values)
    if isinstance(arvore, ast.UnaryOp):
        valor = avaliar(arvore.operand, valores)
        return (not valor) if isinstance(arvore.op, ast.Not) else -valor
    if isinstance(arvore, ast.BinOp):
        return _ARITMETICA[type(arvore.op)](avaliar(arvore.left, valores), avaliar(arvore.right, valores))
    if isinstance(arvore, ast.Compare):
        esquerda = avaliar(arvore.left, valores)
        for op, comparado in zip(arvore.ops, arvore.comparators):
            direita = avaliar(comparado, valores)
            if not _COMPARACOES[type(op)](esquerda, direita):
                return False
            esquerda = direita
        return True
    raise ErroExpressao(f"Construção não suportada: {type(arvore).__name__}.")


def avaliar_guarda(texto: str | None, valores: dict) -> bool:
    """Guarda ausente é sempre verdadeira."""
    if not texto:
        return True
    return bool(avaliar(analisar_guarda(texto), valores))


def executar_acoes(acoes: list[str], valores: dict) -> dict:
    """Aplica as ações na ordem declarada e devolve os novos valores."""
    novos = dict(valores)
    for texto in acoes:
        acao = analisar_acao(texto)
        resultado = avaliar(acao.expressao, novos)
        if acao.operador == "+=":
            resultado = novos[acao.alvo] + resultado
        elif acao.operador == "-=":
            resultado = novos[acao.alvo] - resultado
        novos[acao.alvo] = resultado
    return novos


# ---------------------------------------------------------------- tipos
def tipo_literal(valor) -> str:
    if isinstance(valor, bool):
        return "booleano"
    if isinstance(valor, int):
        return "inteiro"
    if isinstance(valor, float):
        return "decimal"
    if isinstance(valor, str) and DATA_ISO.match(valor):
        return "data"
    return "texto"


def inferir_tipo(arvore: ast.expr, tipos: dict[str, str]) -> str:
    """Tipo da expressão, ou ErroExpressao se os tipos não combinam."""
    if isinstance(arvore, ast.Constant):
        return tipo_literal(arvore.value)
    if isinstance(arvore, ast.Name):
        if arvore.id not in tipos:
            raise ErroExpressao(f"Variável não declarada: '{arvore.id}'.")
        return tipos[arvore.id]
    if isinstance(arvore, ast.BoolOp):
        for v in arvore.values:
            if inferir_tipo(v, tipos) != "booleano":
                raise ErroExpressao("'e' e 'ou' só combinam condições booleanas.")
        return "booleano"
    if isinstance(arvore, ast.UnaryOp):
        tipo = inferir_tipo(arvore.operand, tipos)
        if isinstance(arvore.op, ast.Not):
            if tipo != "booleano":
                raise ErroExpressao("'não' só se aplica a condições booleanas.")
            return "booleano"
        if tipo not in NUMERICOS:
            raise ErroExpressao("O sinal '-' só se aplica a números.")
        return tipo
    if isinstance(arvore, ast.BinOp):
        esquerda, direita = inferir_tipo(arvore.left, tipos), inferir_tipo(arvore.right, tipos)
        if esquerda not in NUMERICOS or direita not in NUMERICOS:
            raise ErroExpressao(f"'{_SIMBOLO[type(arvore.op)]}' só se aplica a números.")
        return "decimal" if "decimal" in (esquerda, direita) else "inteiro"
    if isinstance(arvore, ast.Compare):
        operandos = [inferir_tipo(v, tipos) for v in [arvore.left, *arvore.comparators]]
        for (a, b), op in zip(zip(operandos, operandos[1:]), arvore.ops):
            compativeis = a == b or {a, b} <= NUMERICOS
            if not compativeis:
                raise ErroExpressao(f"Comparação entre tipos diferentes ({a} e {b}).")
            if a == "booleano" and not isinstance(op, (ast.Eq, ast.NotEq)):
                raise ErroExpressao("Booleanos só podem ser comparados com == ou !=.")
        return "booleano"
    raise ErroExpressao(f"Construção não suportada: {type(arvore).__name__}.")


def tipo_compativel(destino: str, origem: str) -> bool:
    """Pode atribuir um valor do tipo `origem` a uma variável do tipo `destino`?"""
    return destino == origem or (destino == "decimal" and origem == "inteiro")


# ---------------------------------------------------------------- formatação canônica
_PRECEDENCIA = {ast.Or: 1, ast.And: 2, ast.Not: 3, "cmp": 4, ast.Add: 5, ast.Sub: 5, ast.Mod: 6, ast.USub: 7}


def _prec(no: ast.expr) -> int:
    if isinstance(no, ast.BoolOp):
        return _PRECEDENCIA[type(no.op)]
    if isinstance(no, ast.UnaryOp):
        return _PRECEDENCIA[type(no.op)]
    if isinstance(no, ast.Compare):
        return _PRECEDENCIA["cmp"]
    if isinstance(no, ast.BinOp):
        return _PRECEDENCIA[type(no.op)]
    return 99


def _fmt(no: ast.expr, minimo: int = 0) -> str:
    if isinstance(no, ast.Constant):
        if isinstance(no.value, bool):
            texto = "verdadeiro" if no.value else "falso"
        elif isinstance(no.value, str):
            texto = f"'{no.value}'"
        else:
            texto = repr(no.value)
    elif isinstance(no, ast.Name):
        texto = no.id
    elif isinstance(no, ast.BoolOp):
        palavra = " e " if isinstance(no.op, ast.And) else " ou "
        texto = palavra.join(_fmt(v, _prec(no) + 1) for v in no.values)
    elif isinstance(no, ast.UnaryOp):
        prefixo = "não " if isinstance(no.op, ast.Not) else "-"
        texto = prefixo + _fmt(no.operand, _prec(no))
    elif isinstance(no, ast.BinOp):
        texto = f"{_fmt(no.left, _prec(no))} {_SIMBOLO[type(no.op)]} {_fmt(no.right, _prec(no) + 1)}"
    elif isinstance(no, ast.Compare):
        partes = [_fmt(no.left, _prec(no) + 1)]
        for op, comparado in zip(no.ops, no.comparators):
            partes += [_SIMBOLO[type(op)], _fmt(comparado, _prec(no) + 1)]
        texto = " ".join(partes)
    else:
        raise ErroExpressao(f"Construção não suportada: {type(no).__name__}.")
    return f"({texto})" if _prec(no) < minimo else texto


def formatar(texto: str) -> str:
    """Guarda em forma canônica, com espaços em volta dos operadores (ex.: 'valor<=saldo' → 'valor <= saldo')."""
    return _fmt(analisar_guarda(texto))
