# Design

## Context

Ver proposal.md (Why). Estado após `stabilize-pipeline`: retry com o erro devolvido ao LLM, orçamento de tempo, erros padronizados e `ModeloMBT` simples. `/gerar` já devolve `tentativas`, `duracao` e `historico`, com resultado (`valido`, `invalido` ou `timeout`), duração e erro de cada tentativa (`servico.gerar` → `ResultadoGeracao`). A validação atual (`validar_coerencia`) checa catálogo, nomes seguros, determinismo por par estado/evento, critérios e finais conhecidos. `backend/geracao.py` faz BFS sobre o grafo e lê `t["criterio"]`. Os modelos de referência de Login e Saque estão em `sistemas_exemplo/` e não usam variáveis. O Login tem um laço no estado final `ContaBloqueada`.

O formato novo é o alvo de todo o trabalho futuro de melhoria do modelo do Ollama (few-shot, fine-tuning), então precisa estar estável antes disso.

## Goals / Non-Goals

**Goals:**
- Representar contadores, limites de valor, datas de validade e pré-condições dos 3 exemplos canônicos do 5W2H.
- Validação suficiente para o gerador de caminhos confiar no modelo sem checagens extras.
- Manter o pipeline atual funcionando de ponta a ponta com o formato novo.

**Non-Goals:**
- Detectar erros semânticos, isto é, modelo coerente mas diferente do que a história pede. Isso é medido em `add-reference-evaluation`.
- Caminhos viáveis sob guardas e casos de borda. Ficam para `add-mbt-generator`.
- Estados hierárquicos ou paralelos.

## Decisions

### 1. Esquema Pydantic

```python
class Variavel(BaseModel):
    nome: str                       # snake_case
    tipo: Literal["inteiro", "decimal", "booleano", "data"]
    categoria: Literal["estado", "entrada", "contexto"]
    valor_inicial: int | float | bool | str | None = None  # obrigatório se categoria == "estado"

class Estado(BaseModel):
    id: str = Field(pattern=r"^[A-Z][A-Za-z0-9]*$")
    rotulo: str
    tipo: Literal["inicial", "intermediario", "final"]

class Transicao(BaseModel):
    id: str                         # "T1", "T2"...
    de: str
    evento: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    para: str
    guarda: str | None = None
    acoes: list[str] = []
    criterios: list[int] = []

class ModeloEstados(BaseModel):
    analise: str                    # PRIMEIRO campo: o LLM raciocina antes de estruturar
    variaveis: list[Variavel] = []
    estados: list[Estado]
    transicoes: list[Transicao]
```

`analise` vem primeiro porque a geração restrita ao esquema segue a ordem dos campos. Alternativa descartada: uma chamada separada para raciocínio, que dobraria a latência. `ModeloMBT` deixa de existir. O nome muda para `ModeloEstados` para que nenhum uso antigo passe despercebido.

### 2. Guardas e ações com `ast` e lista de nós permitidos

O texto é traduzido (`e`→`and`, `ou`→`or`, `não`→`not`) e passa por `ast.parse(mode="eval")`. Ele é rejeitado se tiver nó fora da lista permitida: `BoolOp`, `Compare`, `BinOp` com `Add`, `Sub` ou `Mod`, `UnaryOp` com `Not` ou `USub`, `Name` e `Constant`. A avaliação usa um interpretador próprio sobre a árvore, nunca `eval`. Ações aceitam `Assign` e `AugAssign` com alvo `Name`. Alternativa descartada: gramática com Lark, porque o `ast` já cobre a sintaxe e evita dependência nova. O interpretador fica em módulo próprio (`backend/expressoes.py`), reusado pelo gerador de caminhos e pela avaliação.

### 3. Ambiguidade por valores de fronteira

Para cada par estado/evento com mais de uma transição, monta-se um conjunto de candidatos por variável: literais das guardas, cada literal ±1 (±0,01 para decimal; ±1 dia para data), 0 e o valor inicial. Booleanos usam os dois valores. Todas as combinações são avaliadas, com limite de 10 000, e é reportada a primeira valoração que satisfaz duas guardas. Comparações entre variáveis usam também os pontos de igualdade. Alternativa descartada: solver SMT (z3), exato mas pesado para o escopo. Guardas não lineares podem escapar, e isso fica documentado.

### 4. Erros estruturados e ordem

`ErroValidacao(codigo, elementos, mensagem)`. A validação junta todos os erros e os ordena por grupo: esquema → referências → inicial/final → alcançabilidade → critérios → determinismo. `ErroModelo` passa a carregar a lista. A mensagem de correção reenvia o modelo anterior e os erros, para o LLM corrigir em vez de reescrever do zero.

### 5. Catálogo com variáveis opcionais

`Catalogo` ganha `variaveis: dict[str, str] = {}`. Login e Saque continuam sem variáveis, com a contagem desdobrada em estados. Assim, os testes com sistema alvo continuam sem guardas, e a BFS atual segue produzindo caminhos viáveis para eles. Os eventos passam para snake_case (`SenhaCorreta` → `senha_correta`). O laço `ContaBloqueada --senha_correta--> ContaBloqueada` sai do modelo de referência do Login, porque estados finais não têm saída. A checagem de que a conta bloqueada recusa a senha correta volta como cenário de evento recusado em `add-mbt-generator`.

Isso revê a decisão do change arquivado, que rejeitou contadores como guarda. O motivo da época (o LLM erra mais) continua valendo para sistemas com catálogo, que não usam variáveis. A extração livre e os gabaritos dos exemplos canônicos passam a poder usá-las.

### 6. Gabaritos dos exemplos sem sistema

`exemplos/<id>.json` guarda os gabaritos de `cupom-promocional`, `mfa-bloqueio`, `carrinho` e `saque-atm` (versão canônica com 4 critérios, `valor`, `saldo` e `tentativas`). O `saque-atm` ainda não aparece na interface, para não competir com o sistema exemplo Saque. Ele substitui esse sistema em `add-test-execution`. `demo_data.py` aponta Cupom, MFA e Carrinho para seus gabaritos.

### 7. Gerador atual adaptado, sem mudar a estratégia

`backend/geracao.py` passa a ler `estados[].id`, o estado do tipo inicial, os finais pelo tipo e `criterios` (lista). A BFS ignora guardas. Com sistema alvo, isso é correto, porque os catálogos não têm variáveis. Sem sistema alvo, gera esqueleto, que falha por construção. Caminhos inviáveis em modelos com guardas são uma limitação conhecida até `add-mbt-generator`.

### 8. Saída restrita e semente

Ollama: `format=ModeloEstados.model_json_schema()` e `options={"temperature": 0, "seed": QA_SEMENTE}`. Gemini: `response_schema=ModeloEstados` e `temperature=0`. O Gemini não garante determinismo por semente, e isso fica documentado. O prompt fica em `backend/prompts/extracao_v2.md`, com versão `extracao-v2`. O exemplo resolvido é o Login, que não é um dos 3 canônicos usados no conjunto de teste da avaliação.

## Risks / Trade-offs

- [Esquema maior deixa modelos de 8B mais lentos e com mais erros] → É exatamente o que o benchmark do change 3 vai medir. Não simplificar antes de haver dados.
- [Fronteiras não detectam toda sobreposição] → Limitação documentada; o benchmark acompanha os falsos negativos.
- [Remover o laço do Login reduz a checagem do critério 3 até o change 4] → O cenário de três falhas até `ContaBloqueada` continua cobrindo o bloqueio. A recusa da senha correta volta com os cenários de evento recusado.
- [Caminhos inviáveis em extração livre com guardas] → Só afeta esqueletos, que já falham por construção. Resolvido em `add-mbt-generator`.

## Migration Plan

O formato antigo não é persistido (não há banco), então não há migração de dados. Modelos de referência, gabaritos e fixtures são regravados neste change, e os testes de validação são reescritos. Clientes de `/gerar` recebem o formato novo; o único cliente é o front. Para reverter, basta desfazer o merge.
