# Proposal

## Why

O explore confirmou 10 bugs, e o fluxo real com Ollama falhou por timeout em metade das execuções. O change `gerar-testes-executaveis`, já arquivado, corrigiu parte deles: nomes de estado seguros (bug 3), critério inexistente (bug 10), timeout configurável e modelo padrão `llama3.1:8b` (bug 4, parcial), e a demonstração passou a gerar artefatos a partir do modelo de referência (bug 9). Os demais continuam abertos: upload de requisitos (bugs 1 e 2), retry sem API key (bug 7), erro não JSON quebrando a interface (bug 6), orçamento de tempo por tentativa em vez de total (bug 5) e demonstração que aceita texto livre (bug 8). Antes de mudar o formato do modelo, a primeira metade do pipeline precisa ser confiável.

## What Changes

- Corrige a importação de requisitos: o texto editado à mão prevalece sobre o arquivo importado (bug 1), e a importação usa marcadores de seção explícitos em vez de descartar linhas por palavras como "cada" (bug 2).
- Numera os critérios de 1 a N na interface antes do envio, para que a API, que já recusa critérios sem numeração, não rejeite listas simples.
- Adiciona os exemplos canônicos do 5W2H em 1 clique: Saque em Caixa Eletrônico, Cupom Promocional e Autenticação MFA, além de Login e Carrinho. Só Login e Saque têm sistema exemplo por enquanto. Os outros geram esqueleto até `add-test-execution`.
- Verifica, na inicialização e em `/saude`, se o modelo configurado do Ollama está instalado, e aquece o modelo com `keep_alive`.
- **BREAKING** Troca o limite de tempo "por tentativa × 3" por um orçamento total por geração, lido pela interface e pelo backend (bug 5).
- **BREAKING** Padroniza os erros da API (422, 502, 504, 500) com corpo JSON `{codigo, mensagem}`. A interface trata qualquer resposta de erro, inclusive corpo não JSON (bug 6).
- Remove a segunda chamada sem API key quando ocorre `TypeError` interno (bug 7).
- Identifica o modo demonstração em todas as abas de resultado e recusa texto livre ou editado em vez de só avisar (bug 8).
- `/gerar` passa a devolver também as tentativas e a duração.
- Rótulos do diagrama mostram os critérios de aceite, e o código Mermaid pode ser copiado.
- Corrige o README.

## Capabilities

### New Capabilities
- `requirement-input`: entrada da história de usuário e dos critérios de aceite por formulário, arquivo ou exemplo canônico.
- `llm-provider`: configuração e uso dos provedores de LLM (Ollama e Gemini), com verificação de disponibilidade, aquecimento e tempo limite por chamada.
- `generation-api`: contrato HTTP de geração e de saúde, com códigos de erro, orçamento de tempo e tratamento na interface.
- `state-diagram`: renderização do modelo de estados como diagrama Mermaid stateDiagram-v2.
- `demo-mode`: modo de demonstração offline, claramente identificado e restrito aos exemplos com modelo de referência.

### Modified Capabilities
- `extracao-modelo`: remove "Limites de tempo configuráveis" e "Modelo Ollama padrão disponível", que passam para `generation-api` e `llm-provider`.
- `execucao-testes`: remove "Demonstração não mascara requisito editado". A regra fica mais rígida e passa para `demo-mode`.

## Impact

- `app.py`: importação de arquivo, numeração, exemplos, tratamento de erro, avisos da demonstração e aba do diagrama.
- `backend/main.py`, `backend/servico.py` e `backend/llm.py`: códigos de erro, orçamento, verificação de modelo, aquecimento e remoção do `except TypeError`.
- `demo_data.py`: exemplos sem sistema exemplo (Cupom, MFA e Carrinho).
- `.env.example` e `README.md`.
- Testes de interface com `AppTest` e fakes do provedor com a assinatura real.
- O formato do modelo de estados não muda; isso fica para `fsm-model-v2`.
