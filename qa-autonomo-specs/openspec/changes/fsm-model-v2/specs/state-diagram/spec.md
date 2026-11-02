# Spec Delta

## MODIFIED Requirements

### Requirement: Rótulos das transições
Cada transição SHALL aparecer no diagrama com o nome do evento, a guarda entre colchetes quando houver, e os critérios de aceite relacionados.

#### Scenario: Transição com critério
- **WHEN** a transição "pin_invalido" atende ao critério 3
- **THEN** o rótulo da seta mostra "pin_invalido" e "CA3"

#### Scenario: Transição com guarda
- **WHEN** a transição "pin_invalido" tem a guarda `tentativas >= 2`
- **THEN** o rótulo da seta mostra "pin_invalido [tentativas >= 2]"

## ADDED Requirements

### Requirement: Estados inicial e finais no diagrama
O diagrama SHALL ligar o marcador de início ao estado inicial e cada estado final ao marcador de fim.

#### Scenario: Estado final
- **WHEN** `CartaoRetido` é um estado final
- **THEN** o diagrama contém a seta de `CartaoRetido` para o marcador de fim
