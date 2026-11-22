# Spec Delta

## Purpose

Representar o modelo de estados como diagrama Mermaid stateDiagram-v2 válido, para inspeção visual imediata do autômato na interface.

## ADDED Requirements

### Requirement: Diagrama válido para qualquer nome de estado
O diagrama SHALL ser sintaticamente válido para qualquer nome de estado, inclusive com espaços, acentos e pontuação, mantendo o nome original como rótulo visível.

#### Scenario: Estado com espaço
- **WHEN** o modelo contém o estado "Com itens"
- **THEN** o diagrama tem um único nó com rótulo "Com itens"
- **AND** não existem nós "Com" e "itens"

#### Scenario: Estado com acento
- **WHEN** o modelo contém o estado "Cartão Retido"
- **THEN** o diagrama é aceito pelo parser do Mermaid

### Requirement: Colisão de identificadores
Se dois nomes de estado diferentes resultarem no mesmo identificador no diagrama, o sistema SHALL rejeitar o modelo com mensagem que cite os dois nomes.

#### Scenario: Nomes que colidem
- **WHEN** o modelo contém "Com itens" e "ComItens"
- **THEN** o modelo é rejeitado com mensagem citando os dois nomes

### Requirement: Rótulos das transições
Cada transição SHALL aparecer no diagrama com o nome do evento e, quando houver, os critérios de aceite relacionados.

#### Scenario: Transição com critério
- **WHEN** a transição "pin_invalido" atende ao critério 3
- **THEN** o rótulo da seta mostra "pin_invalido" e "CA3"

### Requirement: Código do diagrama disponível
A interface SHALL exibir o diagrama renderizado e SHALL permitir ver e copiar o código Mermaid.

#### Scenario: Copiar código
- **WHEN** o usuário abre a aba do diagrama
- **THEN** ele vê o grafo e pode copiar o código stateDiagram-v2
