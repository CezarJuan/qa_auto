# Proposal

## Why

O modelo atual (`estados`, `inicial`, `finais`, transições com `de`, `evento`, `para` e um único `criterio`) só representa contagem desdobrando estados (`UmaFalha`, `DuasFalhas`). Também não representa valores, como saldo ou valor do saque, nem condições. Nos exemplos canônicos do 5W2H (Saque com múltiplo de 20, Cupom com validade, MFA com bloqueio após 3 tentativas), isso torna a extração livre frágil e deixa o gerador de testes sem guardas para transformar em casos de borda. O explore também mostrou três modelos aceitos que estavam semanticamente errados. Na medição de 2026-11-02 (`docs/medicoes/stabilize-pipeline.md`), o `llama3.1:8b` falhou em todos os exemplos. Em Saque, Cupom e Carrinho, a falha foi "transição ambígua" em situações que dependem de condição, que o formato atual não consegue representar. Este change estabelece o formato estendido que os changes seguintes usam.

O change arquivado `gerar-testes-executaveis` rejeitou contadores como guardas, para reduzir o que o LLM pode errar. Essa decisão é revista aqui: os sistemas exemplo continuam com contagem desdobrada no catálogo, mas a extração livre passa a poder usar variáveis e guardas.

## What Changes

- **BREAKING** Novo formato do modelo de estados: campo de análise, variáveis (estado, entrada, contexto), estados com id ASCII, rótulo e tipo (inicial, intermediário, final), e transições com id, guarda, ações e lista de critérios.
- Linguagem de guardas e ações restrita e verificável, avaliada por interpretador próprio, nunca por `eval`.
- **BREAKING** Validação ampliada: inicial único, ao menos um final, finais sem saída, alcançabilidade e término, referências válidas, critérios cobertos, determinismo com guardas e erros estruturados devolvidos todos de uma vez.
- Extração com saída restrita ao JSON Schema, temperatura 0, semente fixa, exemplo resolvido no prompt, prompt versionado e reenvio do modelo anterior junto com os erros.
- `/gerar` devolve o detalhe de cada tentativa e a versão do prompt, o provedor e o modelo usados.
- Catálogos e modelos de referência de Login e Saque migram para o formato novo, com eventos em snake_case e sem o laço no estado final do Login.
- Gabaritos novos para Cupom, MFA, Carrinho e Saque ATM, com variáveis. Os de Cupom, MFA e Carrinho passam a servir à demonstração.
- O diagrama mostra rótulos de estado, guardas e o marcador de fim ligado aos estados finais.

## Capabilities

### New Capabilities
- `state-model`: formato do modelo de estados finito estendido (análise, variáveis, estados, transições, guardas e ações).
- `state-model-validation`: regras estruturais e de consistência que um modelo precisa cumprir para seguir no pipeline.

### Modified Capabilities
- `extracao-modelo`: ganha saída restrita ao esquema, prompt versionado, correção guiada por erros e registro de tentativas. O catálogo passa a cobrir variáveis. As regras de validação saem daqui e vão para `state-model-validation`, e "Estados finais opcionais" é removido.
- `state-diagram`: rótulos de estado, guardas nas transições e marcadores de início e fim.
- `generation-api`: a resposta de `/gerar` inclui o detalhe das tentativas e a versão do prompt.
- `demo-mode`: exemplos com gabarito e sem sistema exemplo passam a ser exibidos na demonstração.
- `sistemas-exemplo`: catálogo com eventos em snake_case e variáveis opcionais. Os modelos de referência passam a seguir o formato novo.

## Impact

- `backend/schemas.py`, `backend/validacao.py`, `backend/prompts.py`, `backend/servico.py`, `backend/llm.py` e um novo interpretador de guardas e ações.
- `backend/geracao.py`: leitura do formato novo, com campos `criterios`, `id` e `tipo`. A estratégia de caminhos não muda neste change.
- `sistemas_exemplo/`: catálogos e modelos de referência de Login e Saque.
- `exemplos/`: gabaritos de Cupom, MFA, Carrinho e Saque ATM. `demo_data.py` aponta para eles.
- `app.py`: exibição de análise, variáveis e tentativas.
- Testes de validação e de extração reescritos para o formato novo.
- Pré-requisito para `add-reference-evaluation` e `add-mbt-generator`.
