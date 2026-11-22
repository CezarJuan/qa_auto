# Proposal

## Why

O explore confirmou 10 bugs e mostrou que o fluxo real com Ollama falha por timeout em metade das execuções. Antes de evoluir o modelo de estados ou gerar testes, a primeira metade do pipeline (requisito → LLM → modelo → grafo) precisa ser confiável, e a demo não pode se passar por resultado real.

## What Changes

- Corrige a entrada de requisitos: o texto editado à mão prevalece sobre o arquivo importado (bug 1) e a importação não descarta linhas por conter palavras como "cada" (bug 2).
- Adiciona os exemplos canônicos do 5W2H em 1 clique: Saque em Caixa Eletrônico, Cupom Promocional e Autenticação MFA, além de Login e Carrinho.
- Torna o diagrama Mermaid válido para qualquer nome de estado, inclusive com espaços e acentos (bug 3).
- Verifica o modelo configurado do Ollama na inicialização e em `/saude`, com mensagem clara quando ele não estiver instalado (bug 4).
- Unifica o orçamento de tempo entre interface e backend (bug 5) e reduz o primeiro timeout com aquecimento do modelo.
- Garante que todo erro da API, inclusive 500 sem JSON, apareça na interface com mensagem legível (bug 6).
- Remove a nova chamada sem API key em caso de `TypeError` interno (bug 7).
- Identifica claramente o modo demonstração e impede que ele exiba resultado fixo para texto digitado pelo usuário (bugs 8 e 9).
- Corrige o README, que cita exemplos inexistentes.

## Capabilities

### New Capabilities
- `requirement-input`: entrada da história de usuário e dos critérios de aceite por formulário, arquivo ou exemplo canônico.
- `llm-provider`: configuração e uso dos provedores de LLM (Ollama padrão, Gemini opcional), com verificação de saúde e tempo limite.
- `generation-api`: contrato HTTP de geração e de saúde, incluindo códigos de erro e tratamento na interface.
- `state-diagram`: renderização do modelo de estados como diagrama Mermaid stateDiagram-v2.
- `demo-mode`: modo de demonstração offline, claramente identificado.

### Modified Capabilities
<!-- Nenhuma: openspec/specs/ ainda está vazio. -->

## Impact

- `app.py` (linhas citadas no explore: 150, 168, 179, 198, 320, 350, 425).
- `backend/servico.py`, `.env.example`, `README.md`.
- Testes: novos testes para a interface (hoje os 12 cobrem só o backend).
- Sem mudança no formato do modelo de estados; isso fica para `fsm-model-v2`.
