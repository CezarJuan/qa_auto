# Roadmap de specs: alinhamento com o 5W2H

Este documento liga cada objetivo do 5W2H ao change do OpenSpec que o
implementa. Os changes devem ser aplicados **e arquivados em ordem**, porque
os posteriores dependem do modelo de estados definido nos anteriores.

| Ordem | Change | Capabilities criadas | Objetivo do 5W2H atendido |
|---|---|---|---|
| 1 | `stabilize-pipeline` | `requirement-input`, `llm-provider`, `generation-api`, `state-diagram`, `demo-mode` | Interface Streamlit, exemplos em 1 clique, renderização Mermaid, Ollama/Gemini |
| 2 | `fsm-model-v2` | `state-model`, `state-model-validation`, `state-extraction` | Etapa 1: parsing semântico com JSON Schema, temperatura zero, guardas |
| 3 | `add-reference-evaluation` | `reference-cases`, `extraction-evaluation` | Passo 8: avaliação experimental; base para melhorar o modelo do Ollama |
| 4 | `add-mbt-generator` | `test-path-generation`, `gherkin-generation`, `pytest-generation`, `artifact-export` | Etapas 3 e 4: travessia DFS/cobertura, Gherkin, pytest-bdd |
| 5 | `add-test-execution` | `reference-systems`, `test-execution` | Contratos executáveis; prova de que os testes detectam defeitos |
| 6 | `add-persistence` | `generation-history` | Camada SQLite + SQLAlchemy, histórico, `init_db.py` |

O change 6 grava objetos dos changes 2, 4 e 5. No cronograma do 5W2H a
persistência é a Semana 2. Se precisarem dela mais cedo, apliquem o change 6
logo após o 4 e movam o requisito de execuções (e a TB_EXECUCAO) para o
change 5 (ver design.md do change 6).

## Ligação com os bugs do explore

| Bug | Change | Requirement |
|---|---|---|
| 1, 2 | stabilize-pipeline | `requirement-input`: Importação de arquivo, Texto editado prevalece |
| 3 | stabilize-pipeline | `state-diagram`: Nomes de estado arbitrários |
| 4, 7 | stabilize-pipeline | `llm-provider`: Modelo configurado verificado, Falha de configuração |
| 5 | stabilize-pipeline | `generation-api`: Orçamento de tempo único |
| 6 | stabilize-pipeline | `generation-api`: Erros sempre tratados pela interface |
| 8, 9 | stabilize-pipeline | `demo-mode` (artefatos reais chegam no change 4) |
| 10 | fsm-model-v2 | `state-model-validation`: Critérios, Determinismo |
| "Modelo não representa contagem" | fsm-model-v2 | `state-model`: Variáveis, Guardas, Ações |
| "Contra o que os testes rodam" | add-test-execution | `reference-systems` |
| Modelos semanticamente errados (Saque, Carrinho) | add-reference-evaluation | `reference-cases`: Propriedades comportamentais |

## Depois do change 3

Com o benchmark pronto, a melhoria do modelo do Ollama vira um change próprio
(por exemplo `improve-extraction-model`): troca de modelo base, few-shot
dinâmico, Modelfile e, se necessário, fine-tuning com LoRA. Cada etapa é
comparada pelas métricas de `extraction-evaluation`.
