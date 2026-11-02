# state-diagram Specification

## Purpose

Representar o modelo de estados como diagrama Mermaid stateDiagram-v2 válido, para inspeção visual imediata do autômato na interface.

## Requirements

### Requirement: Diagrama sintaticamente válido
O diagrama SHALL ser aceito pelo parser do Mermaid para qualquer modelo que passou na validação, usando o id de cada estado como nó e o rótulo como texto visível, inclusive quando rótulos, eventos ou guardas contêm dois-pontos, aspas ou acentos.

#### Scenario: Estado com acento
- **WHEN** o modelo contém o estado de id `CartaoRetido` e rótulo "Cartão retido"
- **THEN** o diagrama tem um único nó `CartaoRetido` exibido como "Cartão retido"
- **AND** é aceito pelo parser do Mermaid

#### Scenario: Evento com dois-pontos e aspas
- **WHEN** um evento do modelo é `pin: "inválido"`
- **THEN** o diagrama é aceito pelo parser do Mermaid e a seta continua ligando os mesmos estados

### Requirement: Rótulos das transições
Cada transição SHALL aparecer no diagrama com o nome do evento, a guarda entre colchetes quando houver e os critérios de aceite relacionados no formato `CA<n>`.

#### Scenario: Transição com critério
- **WHEN** a transição `pin_invalido` atende ao critério 3
- **THEN** o rótulo da seta mostra "pin_invalido" e "CA3"

#### Scenario: Transição com guarda
- **WHEN** a transição `pin_invalido` tem a guarda `tentativas >= 2`
- **THEN** o rótulo da seta mostra "pin_invalido [tentativas >= 2]"

#### Scenario: Transição sem critério
- **WHEN** a transição não cita critério
- **THEN** o rótulo da seta não mostra nenhum `CA<n>`

### Requirement: Código do diagrama disponível
A interface SHALL exibir o diagrama renderizado e SHALL permitir ver e copiar o código Mermaid.

#### Scenario: Copiar código
- **WHEN** o usuário abre a aba do diagrama
- **THEN** ele vê o grafo e pode copiar o código stateDiagram-v2

### Requirement: Estados inicial e finais no diagrama
O diagrama SHALL ligar o marcador de início ao estado inicial e cada estado final ao marcador de fim.

#### Scenario: Estado final
- **WHEN** `CartaoRetido` é um estado final
- **THEN** o diagrama contém a seta de `CartaoRetido` para o marcador de fim
