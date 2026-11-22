# Spec Delta

## Purpose

Gerar testes executáveis pytest-bdd que verificam o sistema sob teste contra os cenários Gherkin, desacoplados da implementação por uma interface de adaptação.

## ADDED Requirements

### Requirement: Interface de adaptação do sistema sob teste
O sistema SHALL gerar um adaptador com três operações: definir um valor de contexto, disparar um evento com dados, indicando se foi aceito, e informar o estado atual. A versão gerada SHALL falhar com mensagem explícita até ser implementada.

#### Scenario: Adaptador não implementado
- **WHEN** os testes rodam com o adaptador gerado sem alterações
- **THEN** cada cenário falha com a mensagem "Implemente o adaptador do sistema sob teste"

### Requirement: Arquivos com nomes consistentes
Para uma história com identificador `<slug>`, o sistema SHALL gerar `<slug>.feature`, `test_<slug>.py` e o adaptador, e o teste SHALL referenciar exatamente o arquivo `<slug>.feature` no mesmo diretório.

#### Scenario: Nomes do Saque
- **WHEN** a história do Saque é exportada
- **THEN** existem `saque-atm.feature` e `test_saque_atm.py`
- **AND** o teste carrega `saque-atm.feature`

### Requirement: Definição para todo passo
Todo passo do `.feature` gerado SHALL corresponder a exatamente uma definição de passo do teste gerado.

#### Scenario: Execução contra o gabarito
- **WHEN** os testes rodam com um adaptador que simula o próprio modelo
- **THEN** todos os cenários passam e nenhum passo fica sem definição

### Requirement: Asserções reais
Os passos `Então` SHALL comparar o estado atual informado pelo adaptador com o estado esperado, e o passo de evento recusado SHALL verificar a recusa e a permanência no estado. O teste gerado SHALL NOT conter asserções sempre verdadeiras nem passos vazios.

#### Scenario: Estado divergente
- **WHEN** o adaptador informa `CartaoRetido` e o cenário espera `AguardandoPin`
- **THEN** o teste falha mostrando o estado esperado e o obtido

#### Scenario: Teste sem asserção vazia
- **WHEN** o arquivo de teste gerado é inspecionado
- **THEN** ele não contém `assert True` nem definição de passo com corpo `pass`
