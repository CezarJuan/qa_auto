# Roadmap de specs: alinhamento com o 5W2H

Este documento liga cada objetivo do 5W2H ao change do OpenSpec que o implementa. Os changes devem ser aplicados **e arquivados em ordem**, porque os posteriores modificam requisitos criados pelos anteriores. O `openspec archive` recusa um delta MODIFIED cuja spec ainda não existe.

Os changes foram importados de `qa-autonomo-specs/` e reconciliados com o que o change arquivado `2026-11-01-gerar-testes-executaveis` já entregou: as specs `extracao-modelo`, `geracao-testes`, `execucao-testes` e `sistemas-exemplo`. Requisitos que se sobrepunham a essas specs viraram deltas sobre elas, sem criar capabilities duplicadas.

| Ordem | Change | Capabilities novas | Capabilities modificadas | Objetivo do 5W2H atendido |
|---|---|---|---|---|
| 1 | `stabilize-pipeline` | `requirement-input`, `llm-provider`, `generation-api`, `state-diagram`, `demo-mode` | `extracao-modelo`, `execucao-testes` | Interface Streamlit, exemplos em 1 clique, renderização Mermaid, Ollama/Gemini |
| 2 | `fsm-model-v2` | `state-model`, `state-model-validation` | `extracao-modelo`, `state-diagram`, `generation-api`, `demo-mode`, `sistemas-exemplo` | Etapa 1: parsing semântico com JSON Schema, temperatura zero, guardas |
| 3 | `add-reference-evaluation` | `reference-cases`, `extraction-evaluation` | — | Passo 8: avaliação experimental; base para melhorar o modelo do Ollama |
| 4 | `add-mbt-generator` | `artifact-export` | `geracao-testes`, `sistemas-exemplo`, `execucao-testes` | Etapas 3 e 4: travessia DFS/cobertura, Gherkin, pytest-bdd |
| 5 | `add-test-execution` | — | `sistemas-exemplo`, `execucao-testes` | Contratos executáveis; prova de que os testes detectam defeitos |
| 6 | `add-persistence` | `generation-history` | — | Camada SQLite + SQLAlchemy, histórico, `init_db.py` |

O change `add-llm-providers` não faz parte do material original: foi criado no projeto e aplicado depois do change 3. Ele acrescenta os provedores Anthropic e compatível com OpenAI e modifica `llm-provider`, `generation-api` e `extracao-modelo`. Já está implementado e arquivado.

## O que mudou na reconciliação

| Material original | Como ficou |
|---|---|
| `state-extraction` (change 2) | Requisitos adicionados a `extracao-modelo` |
| `test-path-generation`, `gherkin-generation`, `pytest-generation` (change 4) | Requisitos modificados e adicionados em `geracao-testes` |
| `reference-systems` (change 5) e diretório `sistemas_referencia/` | Requisitos em `sistemas-exemplo`; mutantes em `sistemas_exemplo/` |
| `test-execution` (change 5) | Requisitos em `execucao-testes`; o veredito passa a contar mutantes |
| `demo-mode` "Artefatos de teste fora da demo" (changes 1 e 4) | Removido: a geração real de testes já existia |
| Provedor só por variável de ambiente | Provedor escolhido por requisição na interface; modelo por ambiente |
| `TEMPO_LIMITE_CHAMADA` / `ORCAMENTO_TOTAL_GERACAO` | `QA_TIMEOUT_LLM` (já existente) / `QA_ORCAMENTO_GERACAO` |
| `/gerar` devolvendo diagrama, caminhos e artefatos | `/gerar` só extrai; geração e execução seguem no processo do front e da linha de comando |
| Gravação de suítes e execuções pela API | Gravação no processo onde a ação acontece |
| Contagem só por estados desdobrados (decisão do change arquivado) | Revista: sistemas com catálogo seguem desdobrados até o change 5; extração livre e gabaritos usam variáveis |

O change 6 grava objetos dos changes 2, 4 e 5. No cronograma do 5W2H, a persistência é a Semana 2. Se for preciso tê-la mais cedo, aplique o change 6 logo após o 4 e mova o requisito de execuções (e a TB_EXECUCAO) para o change 5. Ver o design.md do change 6.

## Ligação com os bugs do explore

| Bug | Situação |
|---|---|
| 1, 2 | `stabilize-pipeline` → `requirement-input`: Importação de arquivo, Texto editado prevalece |
| 3 | Já corrigido pela validação de nomes do change arquivado; `fsm-model-v2` separa id e rótulo |
| 4 | Padrão `llama3.1:8b` já corrigido; `stabilize-pipeline` → `llm-provider`: Verificação do modelo configurado |
| 5 | `stabilize-pipeline` → `generation-api`: Orçamento de tempo único |
| 6 | `stabilize-pipeline` → `generation-api`: Erros sempre tratados pela interface |
| 7 | `stabilize-pipeline` → `llm-provider`: Falha de configuração não gera nova chamada |
| 8 | `stabilize-pipeline` → `demo-mode`: Demo restrita aos exemplos com modelo de referência |
| 9 | Já corrigido pelo change arquivado (artefatos gerados do modelo de referência) |
| 10 | Critério inexistente já corrigido; `fsm-model-v2` → `state-model-validation` amplia |
| "Modelo não representa contagem" | `fsm-model-v2` → `state-model`: Variáveis, Guardas, Ações |
| "Contra o que os testes rodam" | Já atendido por `sistemas-exemplo`; `add-test-execution` amplia com mutantes |
| Modelos semanticamente errados (Saque, Carrinho) | `add-reference-evaluation` → `reference-cases`: Propriedades comportamentais |

## Depois do change 3

Com o benchmark pronto, a melhoria do modelo do Ollama vira um change próprio (por exemplo, `improve-extraction-model`): troca de modelo base, few-shot dinâmico, Modelfile e, se necessário, fine-tuning com LoRA. Cada etapa é comparada pelas métricas de `extraction-evaluation`.
