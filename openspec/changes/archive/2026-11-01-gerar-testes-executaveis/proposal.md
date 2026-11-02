# Proposal

## Why

A ferramenta extrai um modelo de estados, mas não gera testes: o Gherkin e o Pytest exibidos na demo são texto fixo, os arquivos baixados não executam e, no modo real, essas abas estão vazias. Sem essa segunda metade do fluxo não há Model-Based Testing de fato, e a ferramenta não prova que seus testes detectam falhas.

Na primeira execução com LLM real, os modelos aceitos pelo validador tinham erros de lógica e nomes variáveis entre rodadas. Por isso, gerar testes confiáveis exige também restringir e validar melhor o modelo.

## What Changes

- Adiciona sistemas exemplo executáveis (Login e Saque), cada um com catálogo de estados e eventos, modelo de referência e uma variante com bug injetado.
- Envia o catálogo ao LLM e rejeita modelos que usem nomes fora dele, reaproveitando o retry existente.
- Endurece a validação do modelo: nomes de estado seguros para o grafo, transições ambíguas ou duplicadas e critérios inexistentes passam a ser rejeitados.
- Adiciona estados finais opcionais ao modelo e os exibe no grafo.
- **BREAKING**: `POST /gerar` passa a recusar critérios de aceite sem numeração, que antes eram aceitos sem exigir cobertura.
- Gera caminhos de teste cobrindo todas as transições, de forma determinística, sem usar o LLM nessa etapa.
- Gera pares `.feature` + script `pytest-bdd` que executam; histórias sem sistema exemplo geram apenas esqueleto, sinalizado como tal.
- Executa os testes pela interface contra as duas variantes do sistema e apresenta um veredito que separa erro do modelo de bug do sistema.
- O modo demonstração deixa de usar artefatos fixos e passa pelo mesmo gerador, a partir do modelo de referência.
- Torna o timeout do LLM configurável, com o front coerente com o pior caso do backend, e corrige o nome padrão do modelo Ollama.

Fora do escopo: persistência e histórico (SQLite), testes de aplicações web (Playwright), métricas de avaliação de PLN, CI e os bugs do upload de requisitos.

## Capabilities

### New Capabilities

- `sistemas-exemplo`: sistemas executáveis que servem de alvo dos testes, com catálogo, modelo de referência e variantes correta e com bug.
- `extracao-modelo`: extração do modelo de estados a partir de requisitos, incluindo uso do catálogo, regras de validação e limites de tempo.
- `geracao-testes`: derivação de caminhos a partir do modelo e geração dos artefatos Gherkin e Pytest.
- `execucao-testes`: execução dos testes gerados na interface, apresentação do veredito e comportamento do modo demonstração.

### Modified Capabilities

Nenhuma. O projeto ainda não tem specs publicadas.

## Impact

- **Código novo**: pacote `sistemas_exemplo/` e módulos em `backend/` para geração e execução.
- **Código alterado**: `backend/schemas.py`, `backend/validacao.py`, `backend/prompts.py`, `backend/servico.py`, `backend/llm.py`, `app.py`, `demo_data.py`, `.env.example`.
- **API**: `POST /gerar` ganha o campo opcional `sistema`, e a resposta ganha `finais`; a entrada com critérios sem numeração passa a retornar 422.
- **Dependências**: nenhuma nova. `pytest` e `pytest-bdd` já constam em `requirements.txt` e passam a ser usados em tempo de execução.
- **Documentação**: `README.md` precisa refletir o novo status e o fluxo de execução.
