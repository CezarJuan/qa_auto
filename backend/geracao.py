"""Geração determinística de artefatos a partir do modelo, sem uso do LLM."""
import re
from collections import deque
from dataclasses import dataclass

from sistemas_exemplo import obter

from . import expressoes
from .schemas import estado_inicial, estados_finais, rotulos

SCRIPT = '''"""Testes gerados pelo QA Autonomous a partir de __FEATURE__.

Salve os dois arquivos em uma mesma pasta dentro do projeto e rode, na raiz:
    python -m pytest <pasta>
__USO__
"""
import os

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
__IMPORT_SISTEMA__
scenarios("__FEATURE__")


__FIXTURE__


@given(parsers.parse('que o sistema está no estado "{estado}"'))
def estado_inicial(sut, estado):
    assert sut.estado == estado, f"Esperado {estado}, obtido {sut.estado}"


@when(parsers.parse('ocorre o evento "{evento}"'))
def ocorre_evento(sut, evento):
    sut.disparar(evento)


@then(parsers.parse('o estado deve ser "{estado}"'))
def confere_estado(sut, estado):
    assert sut.estado == estado, f"Esperado {estado}, obtido {sut.estado}"
'''

FIXTURE_SISTEMA = '''@pytest.fixture
def sut():
    return criar("__SISTEMA__", os.getenv("QA_VARIANTE", "correto"))'''

FIXTURE_ESQUELETO = '''@pytest.fixture
def sut():
    pytest.fail("Sistema não conectado: implemente a fixture sut com estado e disparar(evento).")'''


@dataclass(frozen=True)
class Artefatos:
    nome_feature: str
    feature: str
    nome_script: str
    script: str


def _rotulo_mermaid(texto: str) -> str:
    """Remove do rótulo os caracteres que mudam a sintaxe do Mermaid (`:`, `;`, `"`, `#`, chaves, quebras)."""
    texto = re.sub(r'[:;"#{}]', " ", texto)
    return re.sub(r"\s+", " ", texto).strip() or "evento"


def _guarda_legivel(guarda: str) -> str:
    """Guarda em forma canônica (operadores com espaços, para o `<` nunca parecer uma tag HTML)."""
    try:
        return expressoes.formatar(guarda)
    except expressoes.ErroExpressao:
        return re.sub(r"\s*([<>!=]=|[<>])\s*", r" \1 ", guarda)


def modelo_para_mermaid(modelo: dict) -> str:
    """Converte o modelo em stateDiagram-v2: rótulos dos estados, evento [guarda] (CA<n>) e finais."""
    linhas = ["stateDiagram-v2"]
    for id_, rotulo in rotulos(modelo).items():
        linhas.append(f'    state "{_rotulo_mermaid(rotulo)}" as {id_}')
    linhas.append(f"    [*] --> {estado_inicial(modelo)}")
    for t in modelo["transicoes"]:
        rotulo = _rotulo_mermaid(t["evento"])
        if t.get("guarda"):
            rotulo += f" [{_rotulo_mermaid(_guarda_legivel(t['guarda']))}]"
        if t.get("criterios"):
            rotulo += " (" + ", ".join(f"CA{n}" for n in t["criterios"]) + ")"
        linhas.append(f"    {t['de']} --> {t['para']} : {rotulo}")
    linhas.extend(f"    {final} --> [*]" for final in estados_finais(modelo))
    return "\n".join(linhas)


def _caminho_ate(modelo: dict, destino: str) -> list[int]:
    """Índices das transições do caminho mais curto do estado inicial até o destino (BFS)."""
    inicial = estado_inicial(modelo)
    anteriores: dict[str, list[int]] = {inicial: []}
    fila = deque([inicial])
    while fila and destino not in anteriores:
        atual = fila.popleft()
        for indice, t in enumerate(modelo["transicoes"]):
            if t["de"] == atual and t["para"] not in anteriores:
                anteriores[t["para"]] = anteriores[atual] + [indice]
                fila.append(t["para"])
    if destino not in anteriores:
        raise ValueError(f"Estado inalcançável a partir do inicial: {destino}")
    return anteriores[destino]


def gerar_caminhos(modelo: dict) -> list[list[dict]]:
    """Caminhos a partir do inicial que, juntos, percorrem todas as transições."""
    transicoes = modelo["transicoes"]
    cobertas: set[int] = set()
    caminhos = []
    for indice, transicao in enumerate(transicoes):
        if indice in cobertas:
            continue
        caminho = _caminho_ate(modelo, transicao["de"]) + [indice]
        cobertas.update(caminho)
        caminhos.append([transicoes[i] for i in caminho])
    return caminhos


def _limpar(texto: str) -> str:
    """Impede que texto do modelo altere a estrutura do Gherkin."""
    return re.sub(r"\s+", " ", texto).replace('"', "'").strip()


def _titulo_cenario(numero: int, caminho: list[dict]) -> str:
    criterios = sorted({n for t in caminho for n in t.get("criterios", [])})
    if not criterios:
        return f"Caminho {numero} - auxiliar"
    return f"Caminho {numero} - critérios {', '.join(map(str, criterios))}"


def gerar_feature(modelo: dict, caminhos: list[list[dict]], titulo: str) -> str:
    linhas = [f"Feature: {_limpar(titulo)}"]
    for numero, caminho in enumerate(caminhos, start=1):
        linhas += ["", f"  Scenario: {_titulo_cenario(numero, caminho)}"]
        linhas.append(f'    Given que o sistema está no estado "{_limpar(estado_inicial(modelo))}"')
        for t in caminho:
            linhas.append(f'    When ocorre o evento "{_limpar(t["evento"])}"')
            linhas.append(f'    Then o estado deve ser "{_limpar(t["para"])}"')
    return "\n".join(linhas) + "\n"


def gerar_script(nome_feature: str, sistema_id: str | None = None) -> str:
    if sistema_id:
        obter(sistema_id)
        import_sistema = "\nfrom sistemas_exemplo import criar\n"
        fixture = FIXTURE_SISTEMA.replace("__SISTEMA__", sistema_id)
        uso = "Para rodar contra a variante com bug, defina QA_VARIANTE=bug."
    else:
        import_sistema = ""
        fixture = FIXTURE_ESQUELETO
        uso = "Este é um esqueleto: os testes falham até o sistema ser conectado."
    return (
        SCRIPT.replace("__FEATURE__", nome_feature)
        .replace("__USO__", uso)
        .replace("__IMPORT_SISTEMA__", import_sistema)
        .replace("__FIXTURE__", fixture)
    )


def gerar_artefatos(modelo: dict, sistema_id: str | None = None) -> Artefatos:
    base = sistema_id or "cenarios"
    titulo = obter(sistema_id).nome if sistema_id else "Modelo gerado"
    nome_feature = f"{base}.feature"
    return Artefatos(
        nome_feature=nome_feature,
        feature=gerar_feature(modelo, gerar_caminhos(modelo), titulo),
        nome_script=f"test_{base}.py",
        script=gerar_script(nome_feature, sistema_id),
    )
