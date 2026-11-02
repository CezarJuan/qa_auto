"""Entrada de requisitos: numeração de critérios, importação de arquivo e validação antes do envio."""
import re
import unicodedata

from .schemas import MAX_CARACTERES

NUMERADA = re.compile(r"^\s*(\d+)\s*[.)\-:]\s*")
MARCADOR_LISTA = re.compile(r"^\s*[-*•]\s+")
MARCADOR_SECAO = re.compile(r"^\s*#+\s*(.+?)\s*:?\s*$")

FORMATO_IMPORTACAO = """# História
Como cliente, quero sacar dinheiro, para ter dinheiro em espécie.

# Critérios
1. Saque com saldo suficiente entrega as notas.
2. Saque sem saldo é recusado."""


class ErroImportacao(ValueError):
    """O arquivo de requisitos não está no formato aceito."""


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def numerar_criterios(texto: str) -> str:
    """Numera cada linha de critério de 1 a N, preservando os números que o usuário já escreveu."""
    linhas = [l.strip() for l in texto.replace("\r\n", "\n").split("\n") if l.strip()]
    saida, proximo = [], 1
    for linha in linhas:
        m = NUMERADA.match(linha)
        if m:
            numero = int(m.group(1))
            saida.append(f"{numero}. {linha[m.end():].strip()}")
            proximo = max(proximo, numero + 1)
        else:
            saida.append(f"{proximo}. {MARCADOR_LISTA.sub('', linha)}")
            proximo += 1
    return "\n".join(saida)


def total_criterios(texto: str) -> int:
    """Quantidade de critérios distintos depois da numeração."""
    return len({NUMERADA.match(l).group(1) for l in numerar_criterios(texto).splitlines()})


def extrair_requisitos_de_texto(conteudo: str) -> tuple[str, str]:
    """Separa história e critérios de um arquivo com as seções `# História` e `# Critérios`."""
    secoes: dict[str, list[str]] = {}
    atual = None
    for linha in conteudo.replace("\r\n", "\n").split("\n"):
        m = MARCADOR_SECAO.match(linha)
        if m:
            titulo = _sem_acento(m.group(1)).lower()
            if titulo.startswith("historia"):
                atual = "historia"
                secoes.setdefault(atual, [])
                continue
            if titulo.startswith("criterio"):
                atual = "criterios"
                secoes.setdefault(atual, [])
                continue
        if atual:
            secoes[atual].append(linha)

    historia = "\n".join(secoes.get("historia", [])).strip()
    criterios = "\n".join(secoes.get("criterios", [])).strip()
    if not historia:
        raise ErroImportacao(
            "A história de usuário não foi encontrada no arquivo. Use o formato:\n\n" + FORMATO_IMPORTACAO
        )
    if not criterios:
        raise ErroImportacao(
            "Os critérios de aceite não foram encontrados no arquivo. Use o formato:\n\n" + FORMATO_IMPORTACAO
        )
    return historia, criterios


def validar_entrada(user_story: str, criterios: str) -> list[str]:
    """Erros que impedem o envio, com a mensagem que a interface deve mostrar."""
    erros = []
    campos = (("A história de usuário", user_story), ("Os critérios de aceite", criterios))
    for nome, valor in campos:
        texto = valor.strip()
        if not texto:
            erros.append(f"{nome} é obrigatória." if nome.startswith("A ") else f"{nome} são obrigatórios.")
        elif len(texto) > MAX_CARACTERES:
            verbo = "tem" if nome.startswith("A ") else "têm"
            erros.append(
                f"{nome} {verbo} {len(texto)} caracteres; o limite é {MAX_CARACTERES}."
            )
    return erros
