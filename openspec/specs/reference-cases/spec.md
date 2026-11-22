# reference-cases Specification

## Purpose

Manter um conjunto versionado de histórias de usuário com modelo de estados gabarito e propriedades comportamentais, usado como verdade de referência para avaliar a extração.

## Requirements

### Requirement: Conteúdo de um caso de referência
Cada caso SHALL ter id, domínio, conjunto (desenvolvimento ou teste), história, critérios numerados, modelo gabarito válido, sinônimos aceitos para estados, eventos e variáveis, e ao menos uma propriedade por critério.

#### Scenario: Caso completo
- **WHEN** o caso `saque-atm` é carregado
- **THEN** ele tem gabarito que passa na validação e ao menos uma propriedade para cada critério

#### Scenario: Caso sem propriedade para um critério
- **WHEN** um caso tem 4 critérios e propriedades só para 1, 2 e 3
- **THEN** o carregamento do conjunto falha citando o caso e o critério 4

### Requirement: Propriedades comportamentais
Uma propriedade SHALL descrever valores de contexto opcionais, uma sequência de eventos com dados de entrada e o estado esperado ao final, ou que um evento seja recusado em determinado ponto.

#### Scenario: PIN errado uma vez não retém o cartão
- **WHEN** a propriedade é "após 1 `pin_invalido`, o estado é `AguardandoPin`"
- **THEN** ela é satisfeita pelo gabarito do Saque
- **AND** não é satisfeita pelo modelo que o explore registrou como errado

#### Scenario: Finalizar carrinho vazio é recusado
- **WHEN** a propriedade é "em `CarrinhoVazio`, o evento `finalizar` é recusado"
- **THEN** ela é satisfeita pelo gabarito do Carrinho

### Requirement: Casos mínimos do conjunto
O conjunto SHALL conter ao menos 15 casos de pelo menos 5 domínios, incluindo Saque em Caixa Eletrônico, Cupom Promocional e Autenticação MFA no conjunto de teste e Login no conjunto de desenvolvimento.

#### Scenario: Composição do conjunto
- **WHEN** o conjunto é carregado
- **THEN** há ao menos 15 casos e 5 domínios
- **AND** `saque-atm`, `cupom-promocional` e `mfa-bloqueio` pertencem ao conjunto de teste

### Requirement: Isolamento do conjunto de teste
Casos do conjunto de teste SHALL NOT ser usados como exemplos de prompt ou dados de treino, e o executor SHALL recusar uma configuração cujos exemplos incluam um caso de teste.

#### Scenario: Exemplo de prompt vazado
- **WHEN** a versão do prompt usa `mfa-bloqueio` como exemplo
- **THEN** a avaliação é recusada citando o caso vazado
