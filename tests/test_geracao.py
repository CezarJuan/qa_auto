import copy
import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.geracao import (
    gerar_artefatos,
    gerar_caminhos,
    gerar_feature,
    gerar_script,
)
from backend.schemas import estado_inicial
from sistemas_exemplo import SISTEMAS, obter

RAIZ = Path(__file__).resolve().parent.parent
LIVRE = {
    "analise": "",
    "variaveis": [],
    "estados": [{"id": "A", "rotulo": "A", "tipo": "inicial"}, {"id": "B", "rotulo": "B", "tipo": "final"}],
    "transicoes": [
        {"id": "T1", "de": "A", "evento": "ir", "para": "B", "guarda": None, "acoes": [], "criterios": []},
        {"id": "T2", "de": "B", "evento": "voltar", "para": "A", "guarda": None, "acoes": [], "criterios": [1]},
    ],
}


def rodar(pasta, variante="correto"):
    ambiente = {
        **os.environ, "PYTHONPATH": str(RAIZ), "QA_VARIANTE": variante, "PYTHONIOENCODING": "utf-8",
    }
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(pasta), "-q", "-p", "no:cacheprovider", f"--rootdir={pasta}"],
        env=ambiente, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def salvar(artefatos, pasta):
    (pasta / artefatos.nome_feature).write_text(artefatos.feature, encoding="utf-8")
    (pasta / artefatos.nome_script).write_text(artefatos.script, encoding="utf-8")


# caminhos
@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_todas_as_transicoes_cobertas(sistema_id):
    modelo = obter(sistema_id).modelo
    percorridas = [t for caminho in gerar_caminhos(modelo) for t in caminho]
    assert all(t in percorridas for t in modelo["transicoes"])


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_caminhos_partem_do_inicial_e_sao_conexos(sistema_id):
    modelo = obter(sistema_id).modelo
    for caminho in gerar_caminhos(modelo):
        atual = estado_inicial(modelo)
        for t in caminho:
            assert t["de"] == atual
            atual = t["para"]


def test_estado_inalcancavel_e_recusado():
    modelo = {**LIVRE, "transicoes": [{"id": "T1", "de": "B", "evento": "x", "para": "A", "criterios": []}]}
    with pytest.raises(ValueError, match="B"):
        gerar_caminhos(modelo)


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_geracao_deterministica(sistema_id):
    modelo = obter(sistema_id).modelo
    assert gerar_artefatos(modelo, sistema_id) == gerar_artefatos(copy.deepcopy(modelo), sistema_id)


# gherkin
def test_cenario_confere_cada_passo():
    feature = gerar_feature(LIVRE, [LIVRE["transicoes"]], "T")
    assert 'Given que o sistema está no estado "A"' in feature
    assert feature.count("When ocorre o evento") == 2
    assert feature.count("Then o estado deve ser") == 2


def test_titulos_com_criterios_e_auxiliar():
    transicoes = LIVRE["transicoes"]
    feature = gerar_feature(
        LIVRE,
        [[transicoes[0]], [{**transicoes[0], "criterios": [3]}, {**transicoes[1], "criterios": [2]}]],
        "T",
    )
    assert "Scenario: Caminho 1 - auxiliar" in feature
    assert "Scenario: Caminho 2 - critérios 2, 3" in feature


def test_nomes_de_cenario_unicos():
    feature = gerar_artefatos(obter("login").modelo, "login").feature
    nomes = [l for l in feature.splitlines() if "Scenario:" in l]
    assert len(nomes) == len(set(nomes)) > 1


MALICIOSO = 'x"\n  Scenario: invadido\n    Given import os; os.system("calc")'


def test_evento_malicioso_nao_altera_estrutura():
    modelo = copy.deepcopy(LIVRE)
    modelo["transicoes"][0]["evento"] = MALICIOSO
    linhas = [l.strip() for l in gerar_artefatos(modelo).feature.splitlines() if l.strip()]
    assert sum(l.startswith("Scenario:") for l in linhas) == 2
    assert all(l.startswith(("Feature:", "Scenario:", "Given ", "When ", "Then ")) for l in linhas)


def test_texto_do_modelo_nao_aparece_no_script():
    modelo = copy.deepcopy(LIVRE)
    modelo["transicoes"][0]["evento"] = MALICIOSO
    assert "calc" not in gerar_artefatos(modelo).script
    assert "invadido" not in gerar_artefatos(modelo).script


# script
def test_nomes_coerentes():
    artefatos = gerar_artefatos(obter("login").modelo, "login")
    assert (artefatos.nome_feature, artefatos.nome_script) == ("login.feature", "test_login.py")
    assert 'scenarios("login.feature")' in artefatos.script
    assert "python -m pytest" in artefatos.script


def test_sistema_desconhecido_no_script():
    with pytest.raises(Exception, match="fantasma"):
        gerar_script("x.feature", "fantasma")


# ponta a ponta
@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_referencia_passa_no_correto_e_falha_no_bug(sistema_id, tmp_path):
    salvar(gerar_artefatos(obter(sistema_id).modelo, sistema_id), tmp_path)

    correto = rodar(tmp_path, "correto")
    assert correto.returncode == 0, correto.stdout

    com_bug = rodar(tmp_path, "bug")
    assert com_bug.returncode == 1, com_bug.stdout
    assert "Esperado" in com_bug.stdout and "obtido" in com_bug.stdout


def test_esqueleto_falha_pedindo_conexao(tmp_path):
    artefatos = gerar_artefatos(LIVRE)
    assert artefatos.nome_feature == "cenarios.feature"
    salvar(artefatos, tmp_path)
    r = rodar(tmp_path)
    assert r.returncode == 1, r.stdout
    assert "Sistema não conectado" in r.stdout
