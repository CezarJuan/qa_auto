import re
import shutil
import subprocess

import pytest

import exemplos
from backend.geracao import modelo_para_mermaid
from sistemas_exemplo import SISTEMAS, obter

SETA = re.compile(r"^    (\S+) --> (\S+) : (.+)$")


def modelo(transicoes, estados=(("A", "A", "inicial"), ("B", "B", "final"))):
    return {
        "analise": "",
        "variaveis": [],
        "estados": [{"id": i, "rotulo": r, "tipo": t} for i, r, t in estados],
        "transicoes": [{"id": f"T{n}", "guarda": None, "acoes": [], "criterios": [], **t}
                       for n, t in enumerate(transicoes, start=1)],
    }


def setas(codigo):
    return [SETA.match(l).groups() for l in codigo.splitlines() if SETA.match(l)]


# rótulos das transições
def test_transicao_com_criterio_mostra_ca():
    codigo = modelo_para_mermaid(modelo([{"de": "A", "evento": "pin_invalido", "para": "B", "criterios": [3]}]))
    assert setas(codigo) == [("A", "B", "pin_invalido (CA3)")]


def test_varios_criterios():
    codigo = modelo_para_mermaid(modelo([{"de": "A", "evento": "sacar", "para": "B", "criterios": [2, 4]}]))
    assert setas(codigo) == [("A", "B", "sacar (CA2, CA4)")]


def test_transicao_sem_criterio_mostra_so_o_evento():
    codigo = modelo_para_mermaid(modelo([{"de": "A", "evento": "sair", "para": "B"}]))
    assert setas(codigo) == [("A", "B", "sair")]
    assert "CA" not in setas(codigo)[0][2]


def test_transicao_com_guarda():
    codigo = modelo_para_mermaid(modelo([{"de": "A", "evento": "pin_invalido", "para": "B",
                                          "guarda": "tentativas>=2", "criterios": [3]}]))
    assert setas(codigo) == [("A", "B", "pin_invalido [tentativas >= 2] (CA3)")]


def test_guarda_com_menor_que_tem_espacos():
    codigo = modelo_para_mermaid(modelo([{"de": "A", "evento": "sacar", "para": "B", "guarda": "valor<saldo"}]))
    assert "[valor < saldo]" in codigo  # "<saldo" colado poderia virar tag HTML no navegador


def test_evento_com_dois_pontos_e_aspas_mantem_a_seta():
    evento = 'pin: "inválido"; #3\nsegunda linha'
    codigo = modelo_para_mermaid(modelo([{"de": "A", "evento": evento, "para": "B", "criterios": [1]}]))
    (de, para, rotulo), = setas(codigo)
    assert (de, para) == ("A", "B")
    assert not set(rotulo) & set(':;"#\n')
    assert rotulo == "pin inválido 3 segunda linha (CA1)"


def test_evento_so_com_simbolos_ganha_rotulo():
    codigo = modelo_para_mermaid(modelo([{"de": "A", "evento": ":::", "para": "B"}]))
    assert setas(codigo) == [("A", "B", "evento")]


# estados
def test_rotulo_acentuado_no_no_do_id():
    m = modelo([{"de": "Aguardando", "evento": "reter", "para": "CartaoRetido", "criterios": [3]}],
               estados=(("Aguardando", "Aguardando PIN", "inicial"), ("CartaoRetido", "Cartão retido", "final")))
    codigo = modelo_para_mermaid(m)
    assert '    state "Cartão retido" as CartaoRetido' in codigo
    assert codigo.count("CartaoRetido") == 3  # declaração, seta de chegada e seta para o fim


def test_rotulo_com_aspas_nao_quebra_a_declaracao():
    m = modelo([{"de": "A", "evento": "e", "para": "B"}], estados=(("A", 'Diz "oi"', "inicial"), ("B", "B", "final")))
    assert '    state "Diz oi" as A' in modelo_para_mermaid(m)


def test_inicial_e_finais():
    m = modelo([{"de": "A", "evento": "e", "para": "B"}, {"de": "A", "evento": "f", "para": "C"}],
               estados=(("A", "A", "inicial"), ("B", "B", "final"), ("C", "C", "final")))
    codigo = modelo_para_mermaid(m)
    assert "    [*] --> A" in codigo
    assert "    B --> [*]" in codigo and "    C --> [*]" in codigo
    assert codigo.count("--> [*]") == 2


# validação com o parser real (opcional)
def modelos_reais():
    return [obter(s).modelo for s in SISTEMAS] + [exemplos.carregar(g)["modelo"] for g in exemplos.ids()]


@pytest.mark.skipif(shutil.which("mmdc") is None, reason="mermaid-cli (mmdc) não instalado")
@pytest.mark.parametrize("indice", range(len(SISTEMAS) + len(exemplos.ids())))
def test_parser_do_mermaid_aceita(tmp_path, indice):
    entrada = tmp_path / "d.mmd"
    entrada.write_text(modelo_para_mermaid(modelos_reais()[indice]), encoding="utf-8")
    r = subprocess.run(
        [shutil.which("mmdc"), "-i", str(entrada), "-o", str(tmp_path / "d.svg")],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr
