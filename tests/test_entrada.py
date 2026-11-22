import pytest

from backend.entrada import (
    ErroImportacao,
    extrair_requisitos_de_texto,
    numerar_criterios,
    total_criterios,
    validar_entrada,
)
from backend.schemas import numeros_de_criterios


# numeração
def test_criterios_sem_numeracao():
    assert numerar_criterios("faz a\nfaz b\nfaz c") == "1. faz a\n2. faz b\n3. faz c"


def test_criterios_ja_numerados_preservados():
    texto = "1. faz a\n2. faz b\n3. faz c"
    assert numerar_criterios(texto) == texto


def test_formatos_de_numero_normalizados():
    assert numerar_criterios("1) a\n2 - b\n3: c") == "1. a\n2. b\n3. c"


def test_numeracao_parcial_continua_depois_do_maior():
    assert numerar_criterios("1. a\nb\n5. c\nd") == "1. a\n2. b\n5. c\n6. d"


def test_marcadores_de_lista_e_linhas_vazias():
    assert numerar_criterios("- a\n\n  * b  \n• c\n") == "1. a\n2. b\n3. c"


def test_numerados_passam_na_validacao_da_api():
    numerados = numerar_criterios("a\nb")
    assert numeros_de_criterios(numerados) == {1, 2}


def test_vazio():
    assert numerar_criterios("  \n ") == ""


def test_total_de_criterios():
    assert total_criterios("a\nb\n3. c") == 3
    assert total_criterios("1. a\n1. repetido") == 1


# importação
ARQUIVO = """Requisitos do caixa eletrônico

# História
Como cliente,
quero sacar dinheiro.

# Critérios de Aceite
1. Cada tentativa inválida incrementa o contador.
2. Critério com a palavra história no meio.
"""


def test_importa_historia_e_criterios():
    historia, criterios = extrair_requisitos_de_texto(ARQUIVO)
    assert historia == "Como cliente,\nquero sacar dinheiro."
    assert criterios == (
        "1. Cada tentativa inválida incrementa o contador.\n2. Critério com a palavra história no meio."
    )


def test_linha_com_cada_nao_e_descartada():
    _, criterios = extrair_requisitos_de_texto(
        "# História\nComo x\n# Critérios\ncada tentativa inválida incrementa o contador\n"
    )
    assert criterios == "cada tentativa inválida incrementa o contador"


@pytest.mark.parametrize("marcador", ["# HISTORIA", "## história:", "#História de usuário"])
def test_marcadores_sem_diferenciar_maiusculas_e_acentos(marcador):
    historia, _ = extrair_requisitos_de_texto(f"{marcador}\nComo x\n# CRITERIOS\n1. a")
    assert historia == "Como x"


def test_crlf_aceito():
    historia, criterios = extrair_requisitos_de_texto("# História\r\nComo x\r\n# Critérios\r\n1. a\r\n")
    assert (historia, criterios) == ("Como x", "1. a")


def test_arquivo_sem_historia():
    with pytest.raises(ErroImportacao, match="história de usuário não foi encontrada") as erro:
        extrair_requisitos_de_texto("# Critérios\n1. a")
    assert "# História" in str(erro.value)  # mostra o formato aceito


def test_arquivo_sem_criterios():
    with pytest.raises(ErroImportacao, match="critérios de aceite não foram encontrados"):
        extrair_requisitos_de_texto("# História\nComo x")


def test_arquivo_sem_marcadores():
    with pytest.raises(ErroImportacao):
        extrair_requisitos_de_texto("Como x quero y.\nCritérios: 1. a")


# validação antes do envio
def test_entrada_valida():
    assert validar_entrada("Como x", "1. a") == []


def test_campos_vazios():
    erros = validar_entrada("  ", "")
    assert erros == ["A história de usuário é obrigatória.", "Os critérios de aceite são obrigatórios."]


def test_criterios_acima_do_limite():
    erros = validar_entrada("Como x", "1. " + "x" * 2097)
    assert erros == ["Os critérios de aceite têm 2100 caracteres; o limite é 2000."]


def test_limite_exato_aceito():
    assert validar_entrada("x" * 2000, "1. a") == []
