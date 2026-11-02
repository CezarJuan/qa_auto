# Design

## Context

Ver proposal.md (Why). O modelo de `fsm-model-v2` tem variáveis de estado, entrada e contexto, guardas e ações, e um interpretador seguro. O grafo puro (NetworkX) não basta para saber se um caminho é viável, porque a viabilidade depende dos valores das variáveis.

## Goals / Non-Goals

**Goals:**
- Caminhos que de fato executam no modelo, com valores concretos.
- Gherkin e pytest gerados 100% por código, testáveis byte a byte.

**Non-Goals:**
- Gerar a implementação do adaptador para sistemas reais (só o esqueleto).
- Otimizar a cobertura mínima de forma exata (problema NP-difícil); basta uma heurística gulosa.

## Decisions

### 1. Busca sobre configurações, não sobre o grafo de estados

Uma configuração é (estado, valores das variáveis de estado). Os valores de contexto são escolhidos antes da busca e os de entrada em cada evento, ambos a partir dos candidatos de fronteira das guardas (mesma rotina de `fsm-model-v2`, decisão 3). Uma aresta da busca é uma transição cuja guarda é verdadeira com aqueles valores.

- **Todas as transições (padrão):** BFS a partir do inicial até a primeira configuração que dispare cada transição ainda não coberta, seguida do caminho mais curto até um final. As transições são cobertas em ordem de id. Um caminho que cobre várias transições pendentes as marca todas, o que dá uma heurística gulosa.
- **Caminhos elementares (5W2H):** DFS que não repete configuração. Como contadores mudam a configuração, laços como "PIN inválido" são percorridos o necessário sem loop infinito.

Alternativa: DFS sobre o grafo puro e checagem de viabilidade depois. Descartada porque geraria caminhos inviáveis (ex.: reter cartão no 1º erro), justamente o tipo de alucinação que o projeto quer eliminar.

Limites configuráveis: profundidade 30, caminhos 200, combinações de contexto 50.

### 2. Escolha determinística de valores

Os candidatos são ordenados (numéricos crescentes, `False` antes de `True`, datas crescentes) e a busca sempre tenta na mesma ordem. O primeiro valor que satisfaz a guarda é o usado no caminho "normal". Os cenários de borda usam explicitamente o ponto de fronteira e o vizinho fora dela, respeitando as outras guardas do mesmo par estado/evento. No exemplo de múltiplo de 20, o vizinho fora válido é 120, não 101.

### 3. Vocabulário fixo de passos

```gherkin
Dado que o sistema está no estado "<EstadoId>"
E que o contexto "<variavel>" vale <valor>
Quando ocorre o evento "<evento>"
Quando ocorre o evento "<evento>" com:
  | <variavel> | <valor> |
Então o sistema está no estado "<EstadoId>"
Então o evento é recusado e o sistema permanece no estado "<EstadoId>"
```

Com só seis frases parametrizadas, o `test_<slug>.py` tem seis definições de passo genéricas (`parsers.parse`) e a garantia "todo passo tem definição" passa a valer por construção. Alternativa: um passo em linguagem natural por transição (`Quando o cliente informa um PIN inválido`). Fica mais legível, mas exige gerar uma definição por frase e manter os nomes em sincronia. Pode virar melhoria futura, com as frases vindo do rótulo do evento.

Sobre o 5W2H: ele mapeia a guarda para "E". Aqui a guarda aparece como valores concretos (contexto no `E que...`, dados na tabela do `Quando`), porque é isso que torna o teste executável. A guarda textual também vai como comentário acima do passo, para rastreabilidade.

### 4. Estrutura do teste gerado

```
<slug>.feature
test_<slug>.py          # scenarios("<slug>.feature") + 6 definições de passo
adaptador_<slug>.py     # classe com definir_contexto / disparar / estado_atual → NotImplementedError
conftest.py             # fixture `sistema` que instancia o adaptador
README.md               # como implementar o adaptador e rodar
```

### 5. Validação do Gherkin com `gherkin-official`

É o parser oficial do Cucumber e suporta `# language: pt`. Os testes do gerador fazem o parse de cada `.feature` produzido.

### 6. Adaptador de simulação para testar o gerador

Os testes do próprio gerador usam um adaptador que executa o modelo gabarito com o interpretador. Todos os cenários devem passar contra ele. Esse adaptador é reusado em `add-test-execution`.

## Risks / Trade-offs

- [Explosão de combinações em modelos com muitas variáveis] → Limites configuráveis e aviso no relatório de cobertura.
- [Passos genéricos ficam menos legíveis para o PO] → O nome do cenário e os comentários de guarda dão contexto. A versão com frases naturais fica registrada como melhoria.
- [`gherkin-official` com pt] → Teste explícito com palavras-chave em português já no grupo 2 das tarefas.
