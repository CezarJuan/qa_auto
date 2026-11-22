# Spec Delta

## Purpose

Permitir apresentar a ferramenta sem provedor de LLM, deixando claro para quem assiste que o modelo exibido é o de referência do exemplo, e não um resultado extraído.

## ADDED Requirements

### Requirement: Modo demonstração identificado
Quando o modo demonstração estiver ativo, a interface SHALL mostrar em todas as abas de resultado um aviso visível de que o modelo é o de referência do exemplo, sem LLM.

#### Scenario: Demo ativa
- **WHEN** o usuário ativa o modo demonstração e gera um exemplo
- **THEN** cada aba de resultado mostra o aviso "Demonstração: modelo de referência, sem LLM"

### Requirement: Demo restrita aos exemplos com modelo de referência
No modo demonstração, o sistema SHALL exibir resultado apenas para exemplos com modelo de referência cujo texto não foi editado. Para texto digitado, editado ou exemplo sem modelo de referência, SHALL NOT exibir modelo e SHALL informar o motivo.

#### Scenario: Texto livre em modo demo
- **WHEN** o modo demo está ativo e o usuário digita um requisito de boleto
- **THEN** nenhum modelo é exibido
- **AND** a interface informa que é preciso desativar a demonstração para processar texto livre

#### Scenario: Exemplo editado em modo demo
- **WHEN** o usuário carrega o exemplo de Login, altera um critério e gera no modo demo
- **THEN** nenhum modelo é exibido e a interface informa que o exemplo foi editado

#### Scenario: Exemplo sem modelo de referência
- **WHEN** o usuário carrega o exemplo do Cupom e gera no modo demo
- **THEN** nenhum modelo é exibido e a interface informa que esse exemplo não tem modelo de referência

#### Scenario: Exemplo com referência não editado
- **WHEN** o modo demo está ativo e o usuário carrega o exemplo de Login sem editar
- **THEN** o modelo de referência do Login é exibido com o aviso
