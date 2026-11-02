# Proposal

## Why

O change arquivado `gerar-testes-executaveis` entregou a primeira versão do gerador: BFS sobre o grafo, cenários com passos genéricos em Gherkin de palavras-chave inglesas e execução contra Login e Saque. Com o modelo estendido de `fsm-model-v2`, essa BFS ignora guardas e contadores. Ela pode gerar caminhos inviáveis, como reter o cartão no primeiro erro, justamente o tipo de cenário alucinado que o projeto quer eliminar. Também faltam a travessia DFS do 5W2H, os cenários de borda, a cobertura mensurável e a exportação em pacote e por linha de comando (cenário mínimo WCS).

## What Changes

- Caminhos de teste viáveis, calculados sobre configurações (estado e valores das variáveis), do estado inicial até um estado final. Há duas estratégias: cobertura de todas as transições (padrão) e caminhos elementares por DFS.
- Cenários de borda para guardas com comparação: valor na fronteira e logo fora dela, que pode terminar em evento recusado.
- Relatório de cobertura de estados, transições e critérios, com o motivo de cada item não coberto.
- **BREAKING** Gherkin em português (`# language: pt`), com vocabulário fixo de seis frases, contexto e dados de entrada, nomes de cenário com a sequência de eventos e tags `@CA-<n>`, `@caminho-<n>` e `@borda`.
- **BREAKING** Testes pytest-bdd passam a usar um adaptador com três operações: definir contexto, disparar evento com dados e informar o estado. Os sistemas exemplo cumprem essa interface. O esqueleto falha com "Implemente o adaptador do sistema sob teste".
- Exportação de cada artefato e de um pacote zip pela interface, e geração dos mesmos artefatos por linha de comando.
- Aba de cobertura e escolha de estratégia e de cenários de borda na interface.

## Capabilities

### New Capabilities
- `artifact-export`: exibição, download individual e em pacote, e geração por linha de comando dos artefatos.

### Modified Capabilities
- `geracao-testes`: caminhos viáveis do inicial ao final, estratégias, bordas, cobertura, Gherkin em português com tags e testes baseados em adaptador.
- `sistemas-exemplo`: a interface de execução passa a aceitar contexto e dados no evento e a informar se o evento foi aceito.
- `execucao-testes`: "Artefatos gerados no modo real e na demonstração" passa para `artifact-export`.

## Impact

- `backend/geracao.py` dividido em módulos de caminhos, cobertura, compilador Gherkin e gerador pytest, reusando `backend/expressoes.py`.
- `sistemas_exemplo/`: `definir_contexto`, `disparar(evento, dados) -> bool` e `estado_atual`.
- `backend/execucao.py`: escreve o pacote completo (feature, teste, adaptador, conftest) antes de rodar.
- `app.py`: abas Gherkin, Pytest e Cobertura, downloads, zip e opções de estratégia.
- Nova linha de comando de geração.
- A geração continua no processo do front e da linha de comando; `/gerar` não muda.
- Nova dependência: `gherkin-official`, para validar o Gherkin gerado.
