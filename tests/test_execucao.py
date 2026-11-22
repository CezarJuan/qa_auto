import copy
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

import pytest

import backend.execucao as execucao
from backend.execucao import (
    BUG_DETECTADO,
    BUG_NAO_DETECTADO,
    ERRO_EXECUCAO,
    MODELO_DIVERGE,
    Cenario,
    ResultadoVariante,
    calcular_veredito,
    executar_testes,
)
from backend.geracao import gerar_artefatos
from sistemas_exemplo import SISTEMAS, obter

RAIZ = Path(__file__).resolve().parent.parent


def variante(*passou, erro=""):
    cenarios = [Cenario(f"c{i}", p) for i, p in enumerate(passou)]
    return ResultadoVariante("x", cenarios, erro)


# tabela do veredito
@pytest.mark.parametrize(
    "correto, bug, esperado",
    [
        (variante(True), variante(False), BUG_DETECTADO),
        (variante(True), variante(True), BUG_NAO_DETECTADO),
        (variante(False), variante(False), MODELO_DIVERGE),
        (variante(False), variante(True), MODELO_DIVERGE),
        (variante(False), variante(erro="x"), MODELO_DIVERGE),
        (variante(erro="x"), variante(True), ERRO_EXECUCAO),
        (variante(erro="x"), variante(False), ERRO_EXECUCAO),
        (variante(True), variante(erro="x"), ERRO_EXECUCAO),
    ],
)
def test_veredito(correto, bug, esperado):
    assert calcular_veredito(correto, bug) == esperado


# ponta a ponta
def sem_transicao_do_bug():
    modelo = copy.deepcopy(obter("login").modelo)
    modelo["estados"] = [e for e in modelo["estados"] if e["id"] != "ContaBloqueada"]
    modelo["transicoes"] = [
        t for t in modelo["transicoes"] if "ContaBloqueada" not in (t["de"], t["para"])
    ]
    return modelo


def divergente():
    modelo = copy.deepcopy(obter("login").modelo)
    senha_correta_com_duas_falhas = next(t for t in modelo["transicoes"] if t["id"] == "T5")
    assert (senha_correta_com_duas_falhas["de"], senha_correta_com_duas_falhas["evento"]) == (
        "DuasFalhas", "senha_correta"
    )
    senha_correta_com_duas_falhas["para"] = "ContaBloqueada"
    return modelo


@pytest.mark.parametrize("sistema_id", SISTEMAS)
def test_referencia_detecta_bug(sistema_id):
    execucao_ = executar_testes(gerar_artefatos(obter(sistema_id).modelo, sistema_id))
    assert execucao_.veredito == BUG_DETECTADO
    assert execucao_.correto.cenarios and not execucao_.correto.falhas
    assert execucao_.bug.falhas
    assert "Esperado" in execucao_.bug.falhas[0].motivo
    assert execucao_.bug.falhas[0].nome.startswith("Caminho")


def test_modelo_sem_a_transicao_nao_detecta_bug():
    assert executar_testes(gerar_artefatos(sem_transicao_do_bug(), "login")).veredito == BUG_NAO_DETECTADO


def test_modelo_divergente():
    r = executar_testes(gerar_artefatos(divergente(), "login"))
    assert r.veredito == MODELO_DIVERGE
    assert r.correto.falhas


def test_script_quebrado_e_erro_de_execucao():
    artefatos = gerar_artefatos(obter("login").modelo, "login")
    r = executar_testes(replace(artefatos, script="import modulo_que_nao_existe\n"))
    assert r.veredito == ERRO_EXECUCAO
    assert r.correto.erro and not r.correto.cenarios


def test_arquivo_sem_testes_e_erro_de_execucao():
    artefatos = gerar_artefatos(obter("login").modelo, "login")
    r = executar_testes(replace(artefatos, script="# vazio\n"))
    assert r.veredito == ERRO_EXECUCAO


def test_timeout_e_erro_de_execucao():
    artefatos = gerar_artefatos(obter("login").modelo, "login")
    r = executar_testes(replace(artefatos, script="import time\ntime.sleep(30)\n"), timeout=1)
    assert r.veredito == ERRO_EXECUCAO
    assert "ultrapassou" in r.correto.erro


def test_sem_residuos(monkeypatch, tmp_path):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    git = ["git", "-C", str(RAIZ), "status", "--porcelain"]
    antes = subprocess.run(git, capture_output=True, text=True).stdout

    executar_testes(gerar_artefatos(obter("login").modelo, "login"))

    assert list(tmp_path.iterdir()) == []
    assert subprocess.run(git, capture_output=True, text=True).stdout == antes


def test_ambiente_aponta_para_a_raiz():
    assert (execucao.RAIZ_PROJETO / "sistemas_exemplo").is_dir()
