# Spec Delta

## MODIFIED Requirements

### Requirement: Catálogo do sistema
Cada sistema exemplo MUST declarar um catálogo com estados (ids em PascalCase ASCII), eventos (em snake_case), variáveis opcionais e estado inicial, com uma descrição de cada item.

#### Scenario: Catálogo completo
- **WHEN** o catálogo de um sistema exemplo é lido
- **THEN** ele informa os estados, eventos e variáveis válidos, com descrições, e o estado inicial pertence à lista de estados

#### Scenario: Contador representado em estados
- **WHEN** um requisito depende de contagem e o catálogo não declara variáveis
- **THEN** o catálogo representa cada etapa da contagem como um estado próprio

### Requirement: Modelo de referência
Cada sistema exemplo MUST incluir um modelo de referência no formato do modelo de estados que passa na validação, descreve corretamente a variante correta e usa somente nomes do catálogo.

#### Scenario: Referência válida e fiel
- **WHEN** testes são gerados a partir do modelo de referência
- **THEN** todos passam na variante correta e ao menos um falha na variante com bug

#### Scenario: Referência passa na validação
- **WHEN** o modelo de referência é validado com os critérios do exemplo e o catálogo
- **THEN** a validação não devolve erros
