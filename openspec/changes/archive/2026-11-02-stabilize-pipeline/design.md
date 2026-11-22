# Design

## Context

Estado atual, depois do change arquivado `gerar-testes-executaveis`:

- `/gerar` devolve só o `ModeloMBT`. Erros saem como `{"detail": ...}`, com 502 para `ErroLLM` e 422 para `ErroModelo`. Os erros de validação do Pydantic saem como lista. Exceções não previstas viram 500 em texto puro, e `chamar_backend` em `app.py` chama `resp.json()` sem proteção (bug 6).
- `servico.gerar_modelo` repete a chamada sem `api_key` quando ocorre `TypeError` (bug 7).
- O front espera `QA_TIMEOUT_LLM × MAX_TENTATIVAS + 10 s` (padrão 550 s). Não existe orçamento total no backend (bug 5).
- `extrair_requisitos_de_texto` troca de seção quando encontra palavras como "critério" ou "história" em qualquer linha. O upload roda de novo a cada rerun do Streamlit e sobrescreve os campos (bugs 1 e 2).
- A validação já rejeita nomes de estado com espaço ou hífen. Por isso o diagrama não quebra mais por nome de estado (bug 3). Eventos ainda vão crus para o rótulo, exceto `:`.
- `EXEMPLOS` vem de `sistemas_exemplo` (Login e Saque). A demonstração usa o modelo de referência e só avisa quando o texto foi editado.
- Já existem `tests/test_interface.py` e testes de configuração.

## Goals / Non-Goals

**Goals:**
- Fluxo real reproduzível para os 5 exemplos, sem exceção visível na interface.
- Testes de interface nos pontos onde estavam os bugs.

**Non-Goals:**
- Mudar o formato do modelo ou a qualidade semântica da extração (`fsm-model-v2`, `add-reference-evaluation`).
- Criar sistemas exemplo para Cupom, MFA e Carrinho (`add-test-execution`).
- Mover a geração de artefatos para a API. Ela continua no processo do front, como definido no change arquivado.

## Decisions

### 1. Provedor escolhido por requisição, modelo por ambiente

O material original previa o provedor só por variável de ambiente. A interface atual já permite escolher o motor e informar a API key, e isso é usado na apresentação. Fica assim: provedor por requisição, nome do modelo por ambiente (`OLLAMA_MODEL`, `GEMINI_MODEL`). Alternativa descartada: provedor fixo no `.env`, que tiraria uma função já entregue.

### 2. Orçamento único com os nomes de variável atuais

`QA_TIMEOUT_LLM` continua sendo o tempo limite por chamada (padrão 180 s), e entra `QA_ORCAMENTO_GERACAO` para o total por geração. O backend mede o tempo decorrido e não inicia uma tentativa se o restante for menor que um mínimo configurado. Se faltar orçamento, devolve 504. O front importa `espera_maxima()`, que passa a ser `QA_ORCAMENTO_GERACAO + 15 s`. Os nomes do material original (`TEMPO_LIMITE_CHAMADA`, `ORCAMENTO_TOTAL_GERACAO`) não foram adotados, para não quebrar `.env` existentes.

### 3. Erros com handler global

Um `exception_handler` para `RequestValidationError`, `ErroModelo`, `ErroLLM`, um novo `ErroOrcamento` e `Exception` produz sempre `{codigo, mensagem}`. No front, `chamar_backend` tenta `resp.json()` e, se falhar, usa uma mensagem por status ("Erro interno no servidor" para 500).

### 4. Fakes com a assinatura real

O `except TypeError` existe só porque fakes antigos não aceitavam `api_key`. Corrige-se os fakes, não o código de produção.

### 5. Aquecimento via `keep_alive`

No `startup`, uma thread chama `ollama.generate(model, prompt="", keep_alive=QA_OLLAMA_KEEP_ALIVE)` (padrão `30m`) depois de checar `ollama.list()`. O estado (`carregando`, `pronto`, `indisponivel`) fica em memória e é exposto em `/saude`. Isso testa a hipótese de que os timeouts iniciais vêm da carga do modelo.

### 6. Importação com marcadores e estado de upload

O formato aceito tem linhas `# História` e `# Critérios`, comparadas sem acento e sem diferenciar maiúsculas. O front guarda o hash do último arquivo importado em `session_state` e só preenche os campos quando o arquivo muda. Assim, edições posteriores prevalecem.

### 7. Numeração no front

`numerar_criterios(texto)` mantém linhas que já começam com número. Nas demais, numera na sequência, continuando depois do maior número visto. A API continua recusando critérios sem numeração, o que protege outros clientes.

### 8. Exemplos sem sistema exemplo

`EXEMPLOS` passa a ter entradas com `sistema: None` e texto próprio (Cupom, MFA, Carrinho) em `demo_data.py`. Com elas, o modo real gera esqueleto e a demonstração recusa por falta de modelo de referência.

### 9. Diagrama

`modelo_para_mermaid` escapa o texto do evento (remove `:`, `"`, `;` e quebras de linha) e acrescenta `CA<n>` quando há critério. Um teste usa `mmdc` se ele estiver instalado e é pulado se não estiver. Um teste sem dependências confere a estrutura das linhas.

## Risks / Trade-offs

- [O aquecimento não resolve os timeouts] → A duração de cada tentativa é registrada. Se persistir, avaliar modelo menor no change de melhoria do modelo.
- [Formato novo de importação quebra arquivos antigos] → A mensagem de erro mostra um exemplo do formato aceito.
- [Mudança do corpo de erro quebra clientes] → O único cliente é o front, atualizado no mesmo change.
- [`mmdc` ausente no ambiente] → Teste marcado como opcional, com teste estrutural obrigatório.

## Open Questions

- Valor padrão de `QA_ORCAMENTO_GERACAO`. A proposta é 360 s, duas chamadas completas. Pode ser ajustado após medir com o aquecimento ativo.
