"""Casos de referência (benchmark/): esquema, carregamento e verificação.

Cada caso é um YAML com história, critérios, gabarito, sinônimos e propriedades comportamentais.
Os casos que já têm gabarito no projeto apontam para ele com `origem` (`exemplo:<id>` ou
`sistema:<id>`), para que exista uma única fonte de cada modelo.
"""
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

import exemplos
from backend.schemas import ModeloEstados, numeros_de_criterios
from backend.validacao import validar_modelo
from sistemas_exemplo import Catalogo, obter

from .simulacao import ErroSimulacao, simular

PASTA_PADRAO = Path(__file__).resolve().parent.parent / "benchmark"
DESENVOLVIMENTO, TESTE = "desenvolvimento", "teste"
MINIMO_CASOS, MINIMO_DOMINIOS = 15, 5
OBRIGATORIOS = {TESTE: {"saque-atm", "cupom-promocional", "mfa-bloqueio"}, DESENVOLVIMENTO: {"login"}}


class ErroCaso(ValueError):
    """Caso de referência incompleto ou inconsistente."""


class PassoPropriedade(BaseModel):
    evento: str
    dados: dict = Field(default_factory=dict)


class Propriedade(BaseModel):
    criterio: int
    descricao: str
    contexto: dict = Field(default_factory=dict)
    eventos: list[PassoPropriedade]
    estado_esperado: str | None = None
    recusado: bool = Field(default=False, description="O último evento deve ser recusado")

    @model_validator(mode="after")
    def tem_expectativa(self):
        if self.estado_esperado is None and not self.recusado:
            raise ValueError("A propriedade precisa de estado_esperado ou recusado: true.")
        if not self.eventos:
            raise ValueError("A propriedade precisa de ao menos um evento.")
        return self


class Caso(BaseModel):
    id: str
    dominio: str
    conjunto: Literal["desenvolvimento", "teste"]
    origem: str | None = None
    sistema: str | None = None
    historia: str = ""
    criterios: dict[int, str] = Field(default_factory=dict)
    gabarito: dict = Field(default_factory=dict)
    sinonimos: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    propriedades: list[Propriedade]

    @property
    def criterios_texto(self) -> str:
        return "\n".join(f"{n}. {texto}" for n, texto in sorted(self.criterios.items()))

    @property
    def catalogo(self) -> Catalogo | None:
        return obter(self.sistema).catalogo if self.sistema else None


def _resolver_origem(dados: dict) -> dict:
    origem = dados.get("origem")
    if not origem:
        return dados
    tipo, _, ident = origem.partition(":")
    if tipo == "exemplo":
        g = exemplos.carregar(ident)
        historia, criterios, modelo = g["historia"], g["criterios"], g["modelo"]
    elif tipo == "sistema":
        d = obter(ident)
        historia, criterios, modelo = d.user_story, d.criterios, d.modelo
        dados.setdefault("sistema", ident)
    else:
        raise ErroCaso(f"Origem desconhecida: {origem}")
    numerados = {
        int(linha.split(".", 1)[0]): linha.split(".", 1)[1].strip()
        for linha in criterios.splitlines() if linha.strip()
    }
    return {"historia": historia, "criterios": numerados, "gabarito": modelo, **dados}


def satisfaz(modelo: dict, propriedade: Propriedade) -> tuple[bool, str]:
    """A propriedade vale no modelo, usando os nomes do próprio modelo?"""
    try:
        sim = simular(modelo, [(p.evento, p.dados) for p in propriedade.eventos], propriedade.contexto)
    except ErroSimulacao as e:
        return False, str(e)
    if propriedade.recusado and not sim.ultimo_recusado:
        return False, f"o evento '{propriedade.eventos[-1].evento}' foi aceito, mas deveria ser recusado"
    if propriedade.estado_esperado and sim.estado != propriedade.estado_esperado:
        return False, f"estado final {sim.estado}, esperado {propriedade.estado_esperado}"
    return True, ""


def verificar_caso(caso: Caso) -> None:
    """Gabarito válido, propriedade para cada critério e todas as propriedades satisfeitas pelo gabarito."""
    try:
        modelo = ModeloEstados.model_validate(caso.gabarito)
    except ValidationError as e:
        raise ErroCaso(f"Caso {caso.id}: gabarito fora do formato: {e}") from e
    erros = validar_modelo(modelo, caso.criterios_texto, caso.catalogo)
    if erros:
        raise ErroCaso(f"Caso {caso.id}: gabarito inválido: " + "; ".join(e.mensagem for e in erros))
    numeros = numeros_de_criterios(caso.criterios_texto)
    sem_propriedade = sorted(numeros - {p.criterio for p in caso.propriedades})
    if sem_propriedade:
        lista = ", ".join(map(str, sem_propriedade))
        raise ErroCaso(f"Caso {caso.id}: sem propriedade para o(s) critério(s) {lista}.")
    for p in caso.propriedades:
        if p.criterio not in numeros:
            raise ErroCaso(f"Caso {caso.id}: a propriedade '{p.descricao}' cita o critério {p.criterio}, que não existe.")
        ok, motivo = satisfaz(caso.gabarito, p)
        if not ok:
            raise ErroCaso(f"Caso {caso.id}: o gabarito não satisfaz '{p.descricao}': {motivo}.")


def carregar_caso(caminho: Path) -> Caso:
    try:
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
        caso = Caso.model_validate(_resolver_origem(dados))
    except (yaml.YAMLError, ValidationError, KeyError) as e:
        raise ErroCaso(f"{caminho.name}: {e}") from e
    if caso.id != caminho.stem:
        raise ErroCaso(f"{caminho.name}: o id '{caso.id}' deve ser igual ao nome do arquivo.")
    verificar_caso(caso)
    return caso


def carregar_conjunto(pasta: Path = PASTA_PADRAO, conjunto: str | None = None,
                      ids: list[str] | None = None) -> list[Caso]:
    """Carrega e verifica todos os casos; filtra por conjunto e por ids, se informados."""
    casos = [carregar_caso(p) for p in sorted(Path(pasta).glob("*.yaml"))]
    if ids:
        desconhecidos = sorted(set(ids) - {c.id for c in casos})
        if desconhecidos:
            raise ErroCaso(f"Casos desconhecidos: {', '.join(desconhecidos)}")
        casos = [c for c in casos if c.id in ids]
    if conjunto and conjunto != "ambos":
        casos = [c for c in casos if c.conjunto == conjunto]
    return casos


def verificar_composicao(casos: list[Caso]) -> None:
    """Ao menos 15 casos de 5 domínios, com os canônicos do 5W2H no teste e o Login no desenvolvimento."""
    dominios = {c.dominio for c in casos}
    if len(casos) < MINIMO_CASOS or len(dominios) < MINIMO_DOMINIOS:
        raise ErroCaso(
            f"O conjunto precisa de ao menos {MINIMO_CASOS} casos e {MINIMO_DOMINIOS} domínios; "
            f"tem {len(casos)} casos e {len(dominios)} domínios."
        )
    por_id = {c.id: c for c in casos}
    for conjunto, ids in OBRIGATORIOS.items():
        for ident in sorted(ids):
            if ident not in por_id or por_id[ident].conjunto != conjunto:
                raise ErroCaso(f"O caso '{ident}' precisa estar no conjunto de {conjunto}.")
