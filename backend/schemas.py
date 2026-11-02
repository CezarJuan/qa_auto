"""Esquemas Pydantic: entrada da geração e modelo de estados finito estendido."""
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from sistemas_exemplo import SISTEMAS

MAX_CARACTERES = 2000
MOTORES = ("Gemini (Cloud)", "Ollama (Local)")

PADRAO_ID_ESTADO = r"^[A-Z][A-Za-z0-9]*$"
PADRAO_SNAKE = r"^[a-z][a-z0-9_]*$"
TIPOS_VARIAVEL = ("inteiro", "decimal", "booleano", "data")
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def numeros_de_criterios(criterios: str) -> set[int]:
    """Extrai os números das linhas de critérios (ex.: '1. ...' ou '2) ...')."""
    return {int(n) for n in re.findall(r"^\s*(\d+)\s*[.)\-:]", criterios, flags=re.MULTILINE)}


class Requisicao(BaseModel):
    user_story: str
    criterios: str
    motor: Literal["Gemini (Cloud)", "Ollama (Local)"]
    api_key: str | None = None
    sistema: str | None = None

    @field_validator("user_story", "criterios")
    @classmethod
    def limpar_e_validar(cls, valor: str, info) -> str:
        # Normaliza quebras de linha e remove espaços nas pontas
        valor = valor.replace("\r\n", "\n").replace("\r", "\n").strip()
        nome = "A User Story" if info.field_name == "user_story" else "Os Critérios de Aceite"
        if not valor:
            raise ValueError(f"{nome} não pode estar vazio(a).")
        if len(valor) > MAX_CARACTERES:
            raise ValueError(f"{nome} excede {MAX_CARACTERES} caracteres.")
        if info.field_name == "criterios" and not numeros_de_criterios(valor):
            raise ValueError("Numere os Critérios de Aceite (ex.: '1. ...').")
        return valor

    @field_validator("sistema")
    @classmethod
    def sistema_conhecido(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in SISTEMAS:
            raise ValueError(f"Sistema exemplo desconhecido: {valor}.")
        return valor


# ---------------------------------------------------------------- modelo de estados
def valor_compativel(tipo: str, valor) -> bool:
    """O valor literal combina com o tipo declarado da variável?"""
    if tipo == "booleano":
        return isinstance(valor, bool)
    if tipo == "inteiro":
        return isinstance(valor, int) and not isinstance(valor, bool)
    if tipo == "decimal":
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)
    return isinstance(valor, str) and bool(DATA_ISO.match(valor))


class Variavel(BaseModel):
    nome: str = Field(pattern=PADRAO_SNAKE, description="Nome em snake_case")
    tipo: Literal["inteiro", "decimal", "booleano", "data"]
    categoria: Literal["estado", "entrada", "contexto"] = Field(
        description="estado: muda por ações; entrada: chega com o evento; contexto: fixo no cenário"
    )
    valor_inicial: int | float | bool | str | None = Field(
        default=None, description="Obrigatório para variáveis de estado. Datas em AAAA-MM-DD."
    )

    @model_validator(mode="after")
    def valor_inicial_coerente(self):
        if self.categoria == "estado" and self.valor_inicial is None:
            raise ValueError(f"A variável de estado '{self.nome}' precisa de valor_inicial.")
        if self.valor_inicial is not None and not valor_compativel(self.tipo, self.valor_inicial):
            raise ValueError(
                f"O valor_inicial {self.valor_inicial!r} de '{self.nome}' não é do tipo {self.tipo}."
            )
        return self


class Estado(BaseModel):
    id: str = Field(pattern=PADRAO_ID_ESTADO, description="PascalCase ASCII, sem espaços nem acentos")
    rotulo: str = Field(description="Nome legível em português")
    tipo: Literal["inicial", "intermediario", "final"]


class Transicao(BaseModel):
    id: str = Field(description="T1, T2, ...")
    de: str
    evento: str = Field(pattern=PADRAO_SNAKE, description="Nome do evento em snake_case")
    para: str
    guarda: str | None = Field(default=None, description="Condição, ex.: tentativas < 2 e valor > 0")
    acoes: list[str] = Field(default_factory=list, description="Ex.: tentativas += 1")
    criterios: list[int] = Field(default_factory=list, description="Números dos critérios de aceite")


class ModeloEstados(BaseModel):
    analise: str = Field(description="Regras identificadas em cada critério, escritas antes do modelo")
    variaveis: list[Variavel] = Field(default_factory=list)
    estados: list[Estado]
    transicoes: list[Transicao]


# ---------------------------------------------------------------- leitura do modelo em dict
def ids_estados(modelo: dict) -> list[str]:
    return [e["id"] for e in modelo["estados"]]


def estado_inicial(modelo: dict) -> str:
    """Id do (primeiro) estado do tipo inicial."""
    return next(e["id"] for e in modelo["estados"] if e["tipo"] == "inicial")


def estados_finais(modelo: dict) -> list[str]:
    return [e["id"] for e in modelo["estados"] if e["tipo"] == "final"]


def rotulos(modelo: dict) -> dict[str, str]:
    return {e["id"]: e.get("rotulo") or e["id"] for e in modelo["estados"]}


def criterios_cobertos(modelo: dict) -> set[int]:
    return {n for t in modelo["transicoes"] for n in t.get("criterios", [])}
