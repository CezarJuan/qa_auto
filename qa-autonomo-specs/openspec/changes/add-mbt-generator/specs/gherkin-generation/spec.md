# Spec Delta

## Purpose

Traduzir os caminhos de teste em especificação BDD na sintaxe Gherkin em português, com rastreabilidade para os critérios de aceite.

## ADDED Requirements

### Requirement: Arquivo .feature válido em português
O sistema SHALL gerar um arquivo `.feature` com `# language: pt`, uma Funcionalidade com o título e o texto da história, e SHALL garantir que o arquivo é aceito por um parser Gherkin sem erros.

#### Scenario: Feature do Saque
- **WHEN** o Gherkin do Saque é gerado
- **THEN** o arquivo começa com `# language: pt` e uma `Funcionalidade:`
- **AND** o parser Gherkin o aceita sem erros

### Requirement: Um cenário por caminho
Cada caminho SHALL virar um `Cenário` cujo nome identifica o número do caminho, a sequência de eventos e o estado final.

#### Scenario: Nome do cenário
- **WHEN** o caminho 2 tem eventos `inserir_cartao`, `pin_valido`, `solicitar_saque` e termina em `SaqueRealizado`
- **THEN** o cenário se chama "Caminho 2: inserir_cartao → pin_valido → solicitar_saque → SaqueRealizado"

### Requirement: Mapeamento formal dos passos
O sistema SHALL mapear o estado de origem e o contexto para `Dado`/`E`, cada evento com seus dados para `Quando`, e cada estado resultante para `Então`, usando um vocabulário fixo de frases.

#### Scenario: Passos de uma transição com guarda
- **WHEN** o trecho do caminho parte de `Autenticado`, com contexto `saldo = 100` e o evento `solicitar_saque` com `valor = 80` levando a `SaqueRealizado`
- **THEN** o cenário contém `Dado que o sistema está no estado "Autenticado"`, `E que o contexto "saldo" vale 100`, `Quando ocorre o evento "solicitar_saque" com:` seguido de tabela `| valor | 80 |` e `Então o sistema está no estado "SaqueRealizado"`

#### Scenario: Evento recusado em cenário de borda
- **WHEN** o cenário de borda termina com o evento recusado
- **THEN** o último passo é `Então o evento é recusado e o sistema permanece no estado "<estado>"`

### Requirement: Tags de rastreabilidade
Cada cenário SHALL ter as tags `@CA-<n>` para cada critério coberto, `@caminho-<n>` e, quando for de borda, `@borda`.

#### Scenario: Tags do cenário
- **WHEN** o caminho 3 cobre os critérios 2 e 4 e é de borda
- **THEN** o cenário tem as tags `@CA-2 @CA-4 @caminho-3 @borda`

### Requirement: Gherkin sem LLM
O conteúdo do arquivo `.feature` SHALL ser derivado apenas do modelo, dos caminhos e da história, sem chamada a LLM.

#### Scenario: Geração offline
- **WHEN** o provedor de LLM está indisponível e o modelo já foi extraído
- **THEN** o Gherkin é gerado normalmente
