# Proposal

## Why

A extração está presa a dois provedores fixos no código (Ollama e Gemini), espalhados em quatro lugares: cliente, esquema da requisição, interface e executor da avaliação. Na linha de base, o `llama3.1:8b` não satisfez nenhuma propriedade, e o Gemini ficou indisponível por cota (429) e alta demanda (503). Sem outros modelos, não há como saber se um modelo mais capaz resolve os erros semânticos medidos, nem como trocar de provedor quando um deles falha.

## What Changes

- Registro de provedores: cada provedor declara id, nome, modelo configurado, disponibilidade e se aceita saída restrita a JSON Schema, temperatura e semente. Interface, API, `/saude` e avaliação passam a ler esse registro.
- Novo provedor **compatível com OpenAI**, configurado por URL base, chave e modelo. Cobre LM Studio, vLLM e llama.cpp server (locais) e OpenRouter, Groq e Together (nuvem).
- Novo provedor **Anthropic (Claude)**, pelo SDK oficial, com saída estruturada pelo esquema do `ModeloEstados`. Usa `claude-opus-5-5` por padrão, configurável.
- Escolha do **modelo por requisição**: a interface e a API aceitam um modelo opcional, além do provedor, sem precisar editar o `.env`.
- O resultado informa se a extração foi determinística, ou seja, se o provedor aceitou temperatura 0 e semente.
- `/saude` lista a disponibilidade de cada provedor, sem expor chaves.
- **BREAKING (compatível)**: `motor` passa a aceitar o id do provedor (`ollama`, `gemini`, `openai_compat`, `anthropic`). Os rótulos atuais ("Ollama (Local)", "Gemini (Cloud)") continuam aceitos como sinônimos.

Fora do escopo: fallback entre provedores e escalonamento por qualidade (decisão do usuário), e melhoria de prompt (`improve-extraction-model`).

## Capabilities

### New Capabilities
<!-- Nenhuma: os provedores pertencem à capability existente llm-provider. -->

### Modified Capabilities
- `llm-provider`: registro de provedores, dois provedores novos, modelo por requisição, disponibilidade de cada provedor e recusa do modelo tratada como falha do provedor.
- `generation-api`: `/gerar` aceita provedor por id e modelo opcional e informa se a extração foi determinística; `/saude` lista todos os provedores.
- `extracao-modelo`: temperatura 0 e semente passam a valer quando o provedor aceita; JSON Schema continua obrigatório quando o provedor suporta.

## Impact

- Novo `backend/provedores/` (registro e um módulo por provedor). `backend/llm.py` passa a delegar a ele.
- `backend/schemas.py` (`Requisicao.motor` e `modelo`), `backend/servico.py`, `backend/main.py` (`/saude`), `app.py` (seletor de provedor e campo de modelo) e `avaliacao/` (`--provedor` aceita qualquer id do registro).
- Novas dependências: `anthropic` (SDK oficial, 1.x) e `openai` (cliente do protocolo compatível).
- Novas variáveis: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ANTHROPIC_EFFORT`, `OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_API_KEY`, `OPENAI_COMPAT_MODEL` e `OPENAI_COMPAT_MODO_ESQUEMA`.
- Provedores na nuvem recebem os requisitos do usuário, e a interface deixa isso visível.
- Depende de `add-reference-evaluation` (pacote `avaliacao/`) estar no código, o que já é verdade no branch atual.
