# sistemas-exemplo Specification

## Purpose

Fornece sistemas executáveis que servem de alvo para os testes gerados, permitindo demonstrar que eles passam em código correto e falham quando há um bug.

## Requirements

### Requirement: Sistemas exemplo disponíveis
O projeto MUST oferecer os sistemas exemplo Login e Saque, cada um identificado por um id estável.

#### Scenario: Listar sistemas
- **WHEN** o catálogo de sistemas exemplo é consultado
- **THEN** ele contém os ids `login` e `saque`, cada um com um nome de exibição

### Requirement: Catálogo do sistema
Cada sistema exemplo MUST declarar um catálogo com estados (ids em PascalCase ASCII), eventos (em snake_case), variáveis opcionais e estado inicial, com uma descrição de cada item.

#### Scenario: Catálogo completo
- **WHEN** o catálogo de um sistema exemplo é lido
- **THEN** ele informa os estados, eventos e variáveis válidos, com descrições, e o estado inicial pertence à lista de estados

#### Scenario: Contador representado em estados
- **WHEN** um requisito depende de contagem e o catálogo não declara variáveis
- **THEN** o catálogo representa cada etapa da contagem como um estado próprio

### Requirement: Interface de execução uniforme
Cada variante de sistema exemplo MUST aceitar o disparo de um evento do catálogo e expor o estado atual usando um nome do catálogo.

#### Scenario: Evento aplicável
- **WHEN** um evento aplicável ao estado atual é disparado
- **THEN** o estado exposto muda de acordo com a regra de negócio do sistema

#### Scenario: Evento não aplicável
- **WHEN** um evento sem efeito no estado atual é disparado
- **THEN** o estado exposto permanece o mesmo e nenhum erro é lançado

#### Scenario: Evento fora do catálogo
- **WHEN** um evento que não pertence ao catálogo é disparado
- **THEN** o sistema lança um erro que identifica o evento

### Requirement: Comportamento implementado como regra de negócio
Os sistemas exemplo MUST implementar o comportamento com regras de negócio próprias, e não derivá-lo do modelo de referência.

#### Scenario: Independência do modelo
- **WHEN** o modelo de referência de um sistema é alterado
- **THEN** o comportamento do sistema permanece o mesmo

### Requirement: Variantes correta e com bug
Cada sistema exemplo MUST oferecer uma variante correta e uma variante com bug injetado que viola um critério de aceite do exemplo.

#### Scenario: Selecionar variante
- **WHEN** um sistema é criado informando a variante
- **THEN** é retornada uma instância nova da variante pedida, no estado inicial

#### Scenario: Variante inexistente
- **WHEN** um sistema é criado com id ou variante desconhecidos
- **THEN** é lançado um erro que identifica o valor inválido

### Requirement: Modelo de referência
Cada sistema exemplo MUST incluir um modelo de referência no formato do modelo de estados que passa na validação, descreve corretamente a variante correta e usa somente nomes do catálogo.

#### Scenario: Referência válida e fiel
- **WHEN** testes são gerados a partir do modelo de referência
- **THEN** todos passam na variante correta e ao menos um falha na variante com bug

#### Scenario: Referência passa na validação
- **WHEN** o modelo de referência é validado com os critérios do exemplo e o catálogo
- **THEN** a validação não devolve erros

### Requirement: Requisitos de exemplo
Cada sistema exemplo MUST incluir uma user story e critérios de aceite numerados, coerentes com seu modelo de referência.

#### Scenario: Critérios cobertos
- **WHEN** os critérios de um exemplo são comparados ao modelo de referência
- **THEN** todo critério aparece em ao menos uma transição do modelo
