# Resumo das alterações na plataforma

*QA Autônomo Baseado em Especificação · atualizado em 2026-11-22*

O ponto de partida era um protótipo com 110 testes. O LLM extraía um modelo de estados simples, e o gerador produzia testes para dois sistemas exemplo (Login e Saque). Hoje são **441 testes passando** (6 pulados), o modelo de estados ficou mais rico, há uma avaliação que mede se os modelos estão **certos**, e não só bem formados, e a extração pode usar quatro provedores de LLM.

> **Situação:** o trabalho está commitado na branch `feat/estabilizacao-fsm-avaliacao`, em dois commits sobre a `main`, e segue para revisão em PR.

---

## 1. Planejamento (OpenSpec)

- Os 6 changes de `qa-autonomo-specs/` foram importados e ajustados ao que o projeto já tinha, para não duplicar as quatro specs existentes (`extracao-modelo`, `geracao-testes`, `execucao-testes`, `sistemas-exemplo`).
- O roadmap, com a ordem dos changes e o que mudou em relação ao material original, está em [`roadmap-specs.md`](roadmap-specs.md).

| Change | Situação |
|---|---|
| `stabilize-pipeline` | ✅ Implementado e arquivado |
| `fsm-model-v2` | ✅ Implementado e arquivado |
| `add-reference-evaluation` | 🟡 Arquivado com 13 de 14 tarefas; falta a revisão em dupla (1.4) |
| `add-llm-providers` | ✅ Implementado e arquivado (criado no projeto, fora dos 6 importados) |
| `add-mbt-generator` | ⏳ Planejado, não iniciado |
| `add-test-execution` | ⏳ Planejado, não iniciado |
| `add-persistence` | ⏳ Planejado, não iniciado |

---

## 2. Estabilização do pipeline (`stabilize-pipeline`)

### Bugs corrigidos

| Bug | Correção |
|---|---|
| 1 e 2 | Importação de arquivo com marcadores `# História` / `# Critérios`. Linhas com palavras como "cada" não são mais descartadas, e o texto editado depois da importação prevalece. |
| 5 | Orçamento de tempo único por geração (`QA_ORCAMENTO_GERACAO`); a interface espera esse valor mais 15 s. |
| 6 | A API responde sempre com `{codigo, mensagem}` (422, 502, 504 e 500), e a interface mostra qualquer erro sem exceção, inclusive resposta em texto puro. |
| 7 | Não há mais uma segunda chamada ao provedor sem a API key quando ocorre um erro interno. |
| 8 | A demonstração recusa texto livre ou editado e mostra o aviso "Demonstração: modelo de referência, sem LLM" em todas as abas. |

### Melhorias

- Critérios sem número são numerados automaticamente, e a lista numerada aparece antes do envio.
- Exemplos em 1 clique: Cupom Promocional, Autenticação MFA e Carrinho de Compras, além de Login e Saque.
- A API verifica se o modelo do Ollama está instalado (`/saude` lista os modelos disponíveis) e o carrega na memória ao subir.
- O diagrama mostra os critérios (`CA3`) em cada seta e tem o código Mermaid copiável.
- **Segurança:** havia uma chave real do Gemini no `.env.example`, a caminho do próximo commit. A chave foi movida para o `.env`, que o git ignora.

**Medição:** [`medicoes/stabilize-pipeline.md`](medicoes/stabilize-pipeline.md). Nenhuma das 15 rodadas teve erro sem tratamento na interface, e o orçamento de tempo funcionou como previsto.

---

## 3. Modelo de estados estendido (`fsm-model-v2`)

### Formato novo (`ModeloEstados`)

| Campo | Conteúdo |
|---|---|
| `analise` | Primeiro campo: o LLM escreve as regras de cada critério antes de montar o modelo. |
| `variaveis` | Categorias **estado** (muda por ações), **entrada** (vem com o evento) e **contexto** (fixa no cenário). |
| `estados` | Id em PascalCase ASCII, rótulo em português e tipo (inicial, intermediário ou final). |
| `transicoes` | Evento, guarda, ações e lista de critérios. |

Com isso, "bloquear após 3 tentativas" é representado por uma variável e guardas, e não mais por um estado para cada tentativa.

### Guardas e ações

A linguagem é restrita, por exemplo `valor <= saldo e valor % 20 == 0` e `tentativas += 1`. Ela é interpretada por código próprio, nunca por `eval`, e tem verificação de tipos.

### Validação

Todos os erros voltam de uma vez, com código, elementos envolvidos e mensagem. A validação exige:

- um único estado inicial e ao menos um final;
- estados finais sem transição de saída;
- todo estado alcançável a partir do inicial e com caminho até um final;
- referências e tipos válidos;
- todos os critérios cobertos;
- nenhuma sobreposição de guardas no mesmo estado e evento, verificada por valores de fronteira. O erro mostra o valor que causa a sobreposição.

### Extração

- Temperatura 0, semente fixa (`QA_SEMENTE`) e saída restrita ao JSON Schema, no Ollama e no Gemini.
- Prompt versionado (`extracao-v2`) com um exemplo resolvido.
- Na correção, o LLM recebe o modelo anterior e todos os erros agrupados.
- `/gerar` informa a versão do prompt, o provedor, o modelo e o histórico de tentativas.

### Interface e exemplos

- 4 gabaritos escritos à mão em `exemplos/`: Saque ATM, Cupom, MFA e Carrinho.
- A aba **Análise** mostra a análise do LLM, as variáveis e as tentativas.
- O diagrama mostra os rótulos dos estados, as guardas e os estados finais.

**Medição:** [`medicoes/fsm-model-v2.md`](medicoes/fsm-model-v2.md). Com o `llama3.1:8b`, **3 de 5** exemplos geraram modelo válido; com o formato antigo, foram 0 de 5.

---

## 4. Avaliação da qualidade da extração (`add-reference-evaluation`)

- **Casos de referência:** `benchmark/` tem **15 casos em 11 domínios**, divididos em teste (7) e desenvolvimento (8), com **90 propriedades comportamentais** (por exemplo, "um PIN errado não retém o cartão").
- **Executor:** `python -m avaliacao executar` mede validade, precisão e recall de estados e transições, propriedades satisfeitas e latência, com média e desvio padrão.
- **Comparação:** `python -m avaliacao comparar` coloca duas configurações lado a lado.
- **Proteção contra vazamento:** a avaliação é recusada se o prompt usar como exemplo um caso do conjunto de teste.

### Linha de base (`llama3.1:8b`, conjunto de teste)

| Métrica | Valor |
|---|---|
| Validade | 0,29 (6 de 21 rodadas) |
| Válido na 1ª tentativa | 0,14 |
| Precisão / recall de estados | 0,19 / 0,13 |
| Precisão / recall de transições | 0,00 / 0,00 |
| Propriedades satisfeitas | **0,00** |
| Duração média | 124 s |

Os poucos modelos válidos estavam semanticamente errados. No MFA, o código era aceito sem passar pela senha; na Reserva, ela era confirmada sem pagamento. É a evidência de que a validação estrutural sozinha não basta. Detalhes em [`avaliacao/README.md`](avaliacao/README.md).

---

## 5. Provedores de LLM (`add-llm-providers`)

- **Registro:** `backend/provedores/` reúne quatro provedores (`ollama`, `gemini`, `openai_compat` e `anthropic`). A interface, a API, o `/saude` e a avaliação leem o mesmo registro.
- **Anthropic:** usa o SDK oficial, com `claude-opus-5-5` por padrão e saída restrita ao esquema. Não envia temperatura nem semente, desliga as novas tentativas do SDK e deixa ligado, por padrão, o fallback de recusa do servidor (`ANTHROPIC_FALLBACK_RECUSA`). O esforço do modelo é configurável (`ANTHROPIC_EFFORT`).
- **Compatível com OpenAI:** atende LM Studio, vLLM, o endpoint `/v1` do Ollama, OpenRouter e similares, com os modos de esquema `json_schema`, `json_object` e nenhum.
- **API:** o modelo pode ser escolhido por requisição, `/gerar` aceita o flag `deterministico` e `/saude` traz uma entrada por provedor, sem expor as chaves.
- **Configuração:** as variáveis estão em `.env.example`, sem valores secretos. As chaves reais ficam só no `.env`, que o git ignora.

### Comparação no conjunto de desenvolvimento

| Métrica | `ollama` / `llama3.1:8b` | `openai_compat` / `gemma4:12b` |
|---|---|---|
| Validade | 0,38 | 0,00 |
| Propriedades satisfeitas | 0,15 | 0,00 |
| Rodadas com timeout | 0,00 | 1,00 |
| Duração média | 129 s | 362 s |

O `gemma4:12b` estourou o tempo em todas as rodadas, então essa comparação não mede a qualidade dele. Detalhes em [`avaliacao/comparacao-desenvolvimento-20261102.md`](avaliacao/comparacao-desenvolvimento-20261102.md).

---

## 6. Limitações atuais

### Qualidade da extração

- O Ollama local (8B) ainda gera modelos fracos: às vezes válidos, raramente corretos. A melhoria do modelo é o próximo passo previsto, comparada a esta linha de base.
- O Gemini não pôde ser medido: a cota da chave acabou (429) e o serviço esteve instável (503). Um 503 do provedor hoje não é tentado de novo.
- O provedor Anthropic foi implementado e é coberto por testes com cliente falso, mas ainda não há avaliação dele no benchmark.
- O `gemma4:12b` via `openai_compat` estourou o tempo em todas as rodadas do conjunto de desenvolvimento, então não há medição de qualidade para ele.
- O catálogo não informa quais estados são finais, e o LLM às vezes marca estados intermediários como finais.

### Geração de testes

- Os caminhos de teste ainda ignoram as guardas. Modelos com variáveis (Cupom, MFA, Carrinho) geram apenas esqueleto. Testes viáveis com valores de borda dependem do `add-mbt-generator`.
- Só Login e Saque têm sistema exemplo executável, e cada um tem uma única variante com bug. Mutantes e os demais sistemas vêm no `add-test-execution`.
- O Saque do sistema exemplo ainda não é o Saque canônico do 5W2H, que tem valor, saldo e múltiplo de 20.

### Avaliação

- As rodadas repetidas saem idênticas, por causa da temperatura 0 e da semente fixa. Para medir variância é preciso variar `QA_SEMENTE`.
- A detecção de guardas sobrepostas é por valores de fronteira, não uma prova formal; guardas não lineares podem escapar.
- Faltam alguns sinônimos (ex.: `AcessoConcedido` → `Autenticado`), o que pode subestimar as métricas.

### Infraestrutura

- Não há persistência nem histórico (o `add-persistence` não foi iniciado).
- O validador oficial do Mermaid (`mmdc`) não está instalado, então esses testes são pulados. Os diagramas foram validados uma vez com o parser real do Mermaid.
- O `python` padrão da máquina aponta para uma instalação quebrada. É preciso usar `C:\Users\juan\AppData\Local\Programs\Python\Python314\python.exe`.

---

## 7. Pendências que dependem da equipe

1. **Revisão em dupla** dos 7 casos de teste, preenchendo a tabela em `benchmark/README.md`. Os 10 casos novos foram redigidos com apoio de IA e precisam de validação humana.
2. **Cota do Gemini**, se a equipe quiser resultados com esse provedor.
3. **Avaliar o provedor Anthropic** no benchmark e comparar com a linha de base, para quem tiver uma chave com crédito.

---

## 8. Números

| Indicador | Antes | Agora |
|---|---|---|
| Testes automatizados | 110 | 441 (6 pulados) |
| Specs principais (OpenSpec) | 4 | 13 |
| Provedores de LLM | 2 | 4 |
| Exemplos na interface | 2 | 5 |
| Gabaritos / casos de referência | 2 | 4 gabaritos, 15 casos |
| Modelos válidos com `llama3.1:8b` (5 exemplos) | 0 de 5 | 3 de 5 |
