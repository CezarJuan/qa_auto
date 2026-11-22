# Proposal

## Why

O modelo atual (`Transicao` com `de`, `evento`, `para`, `criterio`) não representa contagem, condições nem fim de fluxo. Por isso "bloquear após 3 tentativas" não tem representação correta, e o gerador de testes não teria guardas para transformar em condições de borda. O explore também mostrou que a validação aceita critério inexistente e transições ambíguas (bug 10), e que três modelos aceitos estavam semanticamente errados.

## What Changes

- **BREAKING** Novo formato do modelo de estados: estados com id, rótulo e tipo (inicial, intermediário, final); variáveis de estado e de entrada; transições com guarda, ações e lista de critérios.
- Linguagem de guardas e ações restrita e verificável (comparações, `e`/`ou`/`não`, atribuições simples).
- Validação ampliada: estado inicial único, estados finais sem saída, todo estado alcançável e com caminho até um final, referências válidas a variáveis e critérios, cobertura de todos os critérios e ausência de ambiguidade entre transições.
- Extração com saída restrita ao JSON Schema do modelo, temperatura zero, campo de análise antes dos dados e correção guiada pelos erros de validação.
- Diagrama passa a exibir guardas e marcar estados finais.

## Capabilities

### New Capabilities
- `state-model`: formato do modelo de estados finito estendido (estados, variáveis, transições, guardas e ações).
- `state-model-validation`: regras estruturais e de consistência que um modelo precisa cumprir para seguir no pipeline.
- `state-extraction`: extração do modelo de estados a partir da história e dos critérios usando um LLM, com saída estruturada e correção.

### Modified Capabilities
- `state-diagram`: passa a exibir guardas e estados finais.

## Impact

- `backend/` (esquemas, validação, serviço de extração, prompts) e `app.py` (exibição do modelo).
- Os exemplos pré-gravados da demo precisam ser regravados no formato novo.
- Os testes atuais de validação precisam ser reescritos para o formato novo.
- Pré-requisito para `add-reference-evaluation` e `add-mbt-generator`.
