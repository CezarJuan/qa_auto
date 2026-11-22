# Design

## Context

Ver proposal.md (Why). Estado esperado após `fsm-model-v2`:

- `backend/geracao.py` lê o `ModeloEstados` e faz BFS sobre o grafo, ignorando guardas. O script é fixo, com três passos genéricos em português sob palavras-chave inglesas (`Given`/`When`/`Then`). O sistema é escolhido pela fixture `sut`, com variante por `QA_VARIANTE`.
- `backend/execucao.py` escreve `.feature` e script num diretório temporário, roda as duas variantes em subprocesso e lê o JUnit XML.
- `backend/expressoes.py` interpreta guardas e ações com segurança.
- A geração roda no processo do front, que funciona sem backend na demonstração. Essa decisão do change arquivado continua valendo.
- Sistemas exemplo expõem `estado` e `disparar(evento)`, sem dados nem contexto.

## Goals / Non-Goals

**Goals:**
- Caminhos que de fato executam no modelo, com valores concretos.
- Gherkin e pytest gerados 100% por código, testáveis byte a byte.
- Manter a execução e o veredito atuais funcionando com o pacote novo.

**Non-Goals:**
- Implementar adaptadores para sistemas reais; só o esqueleto.
- Otimizar a cobertura mínima de forma exata (problema NP-difícil). Basta uma heurística gulosa.
- Mover a geração para a API. O material original previa estender `/gerar`, mas isso quebraria a demonstração sem backend e duplicaria a lógica.

## Decisions

### 1. Busca sobre configurações, não sobre o grafo de estados

Uma configuração é (estado, valores das variáveis de estado). Os valores de contexto são escolhidos antes da busca, e os de entrada em cada evento, ambos a partir dos candidatos de fronteira das guardas (mesma rotina da validação de determinismo de `fsm-model-v2`). Uma aresta da busca é uma transição cuja guarda é verdadeira com aqueles valores.

- **Todas as transições (padrão):** BFS a partir do inicial até a primeira configuração que dispare cada transição ainda não coberta, seguida do caminho mais curto até um final. As transições são cobertas em ordem de id. Um caminho que cobre várias transições pendentes marca todas.
- **Caminhos elementares (5W2H):** DFS que não repete configuração. Como contadores mudam a configuração, laços como "PIN inválido" são percorridos o necessário, sem loop infinito.

Alternativa descartada: DFS sobre o grafo puro e checagem de viabilidade depois, porque geraria caminhos inviáveis. Limites configuráveis: profundidade 30, caminhos 200, combinações de contexto 50.

### 2. Escolha determinística de valores

Os candidatos são ordenados (numéricos crescentes, `False` antes de `True`, datas crescentes) e tentados sempre na mesma ordem. O primeiro valor que satisfaz a guarda é usado no caminho normal. Os cenários de borda usam o ponto de fronteira e o vizinho fora dela, respeitando as outras guardas do mesmo par estado/evento. No exemplo de múltiplo de 20, o vizinho fora válido é 120, não 101.

### 3. Vocabulário fixo de passos em português

```gherkin
# language: pt
Funcionalidade: <título>

  @CA-2 @caminho-3 @borda
  Cenário: Caminho 3: inserir_cartao → pin_valido → solicitar_saque → SaqueRealizado
    Dado que o sistema está no estado "<EstadoId>"
    E que o contexto "<variavel>" vale <valor>
    Quando ocorre o evento "<evento>"
    Quando ocorre o evento "<evento>" com:
      | <variavel> | <valor> |
    Então o sistema está no estado "<EstadoId>"
    Então o evento é recusado e o sistema permanece no estado "<EstadoId>"
```

As seis frases geram seis definições genéricas (`parsers.parse`), e "todo passo tem definição" vale por construção. Texto do modelo só entra no `.feature`, normalizado. O script continua sem nenhum texto do modelo, o que preserva o requisito "Texto do modelo tratado como dado". A guarda textual vai como comentário acima do `Quando`, para rastreabilidade. As frases mudam em relação ao change arquivado (`o estado deve ser` → `o sistema está no estado`), e por isso a mudança é BREAKING para arquivos já baixados.

### 4. Estrutura do pacote gerado

```
<slug>.feature
test_<slug_py>.py      # scenarios("<slug>.feature") + 6 definições de passo
adaptador_<slug_py>.py # definir_contexto / disparar(evento, dados) -> bool / estado_atual
conftest.py            # fixture `sistema` que instancia o adaptador
LEIAME.md              # como implementar o adaptador e rodar
```

O slug é o id do exemplo (`login`, `saque`, `cupom-promocional`) ou `requisito` para texto livre. Com sistema alvo, o adaptador delega para `sistemas_exemplo.criar(id, os.getenv("QA_VARIANTE", "correto"))`. Sem sistema, as três operações lançam `NotImplementedError("Implemente o adaptador do sistema sob teste")`.

### 5. Sistemas exemplo com a interface do adaptador

`SistemaExemplo` ganha `definir_contexto(nome, valor)` e `disparar(evento, dados=None) -> bool`. O retorno indica se a regra de negócio aceitou o evento, e não apenas se o estado mudou, porque laços aceitos não mudam o estado. `estado_atual` é um alias de `estado`. Login e Saque não têm contexto, então `definir_contexto` lança erro para qualquer nome. A decisão de cada sistema continua sendo regra de negócio própria, e não consulta ao modelo.

### 6. Validação do Gherkin com `gherkin-official`

É o parser oficial do Cucumber e suporta `# language: pt`. Os testes do gerador fazem o parse de cada `.feature` produzido. O `pytest-bdd` atual usa o mesmo parser. A tarefa 2.1 confirma que ele coleta cenários em português antes de qualquer outra mudança.

### 7. Adaptador de simulação para testar o gerador

Os testes do gerador usam um adaptador que executa o próprio modelo com o interpretador. Todos os cenários devem passar contra ele. Esse adaptador é reusado em `add-test-execution` para testar a infraestrutura, mas não como sistema alvo.

### 8. Linha de comando

`python -m backend.cli gerar (--requisito arq.md --motor ... | --modelo modelo.json) [--sistema id] [--estrategia transicoes|elementares] [--sem-borda] --saida dir`. A extração usa `backend.servico` diretamente, sem HTTP.

## Risks / Trade-offs

- [Explosão de combinações em modelos com muitas variáveis] → Limites configuráveis e aviso no relatório de cobertura.
- [Passos genéricos ficam menos legíveis para o PO] → O nome do cenário e os comentários de guarda dão contexto. A versão com frases naturais fica registrada como melhoria futura.
- [`pytest-bdd` não aceitar palavras-chave em português] → Verificado na tarefa 2.1. Se falhar, mantém-se `# language: pt` só no parser de validação e as palavras-chave em inglês no arquivo executado, registrando o desvio.
- [Caminhos até um final ficam longos no Saque, cujo único final é `CartaoRetido`] → Aceito: o caminho mais curto até um final é determinístico, e o nome do cenário mostra a sequência.

## Migration Plan

Arquivos `.feature` e scripts baixados com a versão anterior deixam de valer e precisam ser gerados de novo. Não há dados persistidos. Para reverter, basta desfazer o merge.
