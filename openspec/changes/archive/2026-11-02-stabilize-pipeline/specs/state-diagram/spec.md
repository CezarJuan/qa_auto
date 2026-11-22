# Spec Delta

## Purpose

Representar o modelo de estados como diagrama Mermaid stateDiagram-v2 válido, para inspeção visual imediata do autômato na interface.

## ADDED Requirements

### Requirement: Diagrama sintaticamente válido
O diagrama SHALL ser aceito pelo parser do Mermaid para qualquer modelo que passou na validação, inclusive quando nomes de evento contêm dois-pontos, aspas ou acentos.

#### Scenario: Estado com acento
- **WHEN** o modelo contém o estado `CartãoRetido`
- **THEN** o diagrama é aceito pelo parser do Mermaid

#### Scenario: Evento com dois-pontos e aspas
- **WHEN** um evento do modelo é `pin: "inválido"`
- **THEN** o diagrama é aceito pelo parser do Mermaid e a seta continua ligando os mesmos estados

### Requirement: Rótulos das transições
Cada transição SHALL aparecer no diagrama com o nome do evento e, quando houver, os critérios de aceite relacionados no formato `CA<n>`.

#### Scenario: Transição com critério
- **WHEN** a transição `PinIncorreto` atende ao critério 3
- **THEN** o rótulo da seta mostra "PinIncorreto" e "CA3"

#### Scenario: Transição sem critério
- **WHEN** a transição não cita critério
- **THEN** o rótulo da seta mostra apenas o evento

### Requirement: Código do diagrama disponível
A interface SHALL exibir o diagrama renderizado e SHALL permitir ver e copiar o código Mermaid.

#### Scenario: Copiar código
- **WHEN** o usuário abre a aba do diagrama
- **THEN** ele vê o grafo e pode copiar o código stateDiagram-v2
