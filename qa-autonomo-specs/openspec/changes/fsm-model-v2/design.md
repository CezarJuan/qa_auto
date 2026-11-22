# Design

## Context

Ver proposal.md (Why). Hoje o retry com erros devolvidos ao LLM já funciona e corrigiu modelos em 2 e 3 tentativas. Este change mantém esse mecanismo e muda o que é extraído e validado. O formato novo também é o alvo de todo o trabalho futuro de melhoria do modelo do Ollama (few-shot, fine-tuning), então precisa estar estável antes disso.

## Goals / Non-Goals

**Goals:**
- Representar contadores, limites de valor, datas de validade e pré-condições, que aparecem nos 3 exemplos canônicos do 5W2H.
- Validação suficiente para o gerador de caminhos confiar no modelo sem checagens extras.

**Non-Goals:**
- Detectar erros semânticos (modelo coerente, mas diferente do que a história pede). Isso é medido contra gabarito em `add-reference-evaluation`.
- Estados hierárquicos ou paralelos.

## Decisions

### 1. Esquema Pydantic (esboço)

```python
class Variavel(BaseModel):
    nome: str                       # snake_case
    tipo: Literal["inteiro", "decimal", "booleano", "data"]
    categoria: Literal["estado", "entrada", "contexto"]
    valor_inicial: int | float | bool | str | None = None  # obrigatório se categoria == "estado"
    # estado: muda por ações (ex.: tentativas)
    # entrada: chega com o evento (ex.: valor do saque, código do cupom)
    # contexto: fixado no início do cenário, constante (ex.: saldo, data_atual)
    #           é o que o teste gerado configura no "Dado que"

class Estado(BaseModel):
    id: str = Field(pattern=r"^[A-Z][A-Za-z0-9]*$")
    rotulo: str
    tipo: Literal["inicial", "intermediario", "final"]

class Transicao(BaseModel):
    id: str                         # "T1", "T2"...
    de: str
    evento: str                     # snake_case
    para: str
    guarda: str | None = None
    acoes: list[str] = []
    criterios: list[int] = []

class ModeloEstados(BaseModel):
    analise: str                    # PRIMEIRO campo: o LLM raciocina antes de estruturar
    variaveis: list[Variavel]
    estados: list[Estado]
    transicoes: list[Transicao]
```

`analise` vem primeiro porque a geração restrita ao esquema segue a ordem dos campos. É uma forma barata de raciocínio guiado. Alternativa: chamada separada de raciocínio, descartada por dobrar a latência.

### 2. Guardas e ações com `ast` e lista de nós permitidos

O texto é traduzido (`e`→`and`, `ou`→`or`, `não`→`not`), passa por `ast.parse(mode="eval")` e é rejeitado se tiver nó fora da lista permitida (`BoolOp`, `Compare`, `BinOp` com `Add`/`Sub`/`Mod` (o resto cobre a regra de cédulas do Saque), `UnaryOp` `Not`/`USub`, `Name`, `Constant`). A avaliação é feita por um interpretador próprio sobre a árvore, nunca com `eval`. Alternativa: gramática com Lark. Descartada porque o `ast` já cobre a sintaxe e evita dependência nova. O mesmo interpretador será reusado pelo gerador de caminhos e pelos sistemas de referência.

### 3. Ambiguidade por valores de fronteira

Para cada par (estado, evento) com mais de uma transição, o sistema monta um conjunto de valores candidatos por variável: os literais das guardas, cada literal ±1 (ou ±0,01 para decimal), 0 e o valor inicial. Datas usam o literal ±1 dia; booleanos, os dois valores. Depois avalia todas as combinações (produto cartesiano, limitado a 10 000) e reporta a primeira valoração que satisfaz duas guardas. Alternativa: solver SMT (z3), exato mas pesado para o escopo. Fica registrado como limitação: guardas não lineares podem escapar.

Comparações entre variáveis (`valor <= saldo`) usam os candidatos de cada lado e também os pontos de igualdade.

### 4. Ordem dos erros devolvidos ao LLM

Os erros vão agrupados por tipo, do mais estrutural ao mais fino: esquema → referências → inicial/final → alcançabilidade → critérios → determinismo. Na correção, a mensagem também reenvia o modelo anterior. Assim, o LLM corrige em vez de reescrever do zero.

### 5. Few-shot inicial fixo

Este change usa 1 exemplo resolvido fixo (Login), escolhido porque não é um dos 3 canônicos do 5W2H usados na avaliação. O few-shot dinâmico fica para o change de melhoria do modelo.

## Risks / Trade-offs

- [Esquema maior deixa modelos de 8B mais lentos e com mais erros] → É exatamente o que o benchmark do change 3 vai medir. O esquema não deve ser simplificado antes de haver dados.
- [Fronteiras não detectam toda sobreposição] → Limitação documentada; o benchmark acompanha os falsos negativos.
- [Quebra dos exemplos pré-gravados da demo] → Regravar os 5 exemplos no formato novo neste mesmo change.

## Migration Plan

O formato antigo não é persistido em lugar nenhum (database/ está vazio), então não há migração de dados. Basta regravar os fixtures da demo e reescrever os testes.
