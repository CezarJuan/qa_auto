# Spec Delta

## Purpose

Permitir apresentar a ferramenta sem provedor de LLM, deixando claro para quem assiste que os resultados exibidos são pré-gravados e não gerados.

## ADDED Requirements

### Requirement: Modo demonstração identificado
Quando o modo demonstração estiver ativo, a interface SHALL mostrar em todas as abas de resultado um aviso visível de que o conteúdo é pré-gravado.

#### Scenario: Demo ativa
- **WHEN** o usuário ativa o modo demonstração e gera um exemplo
- **THEN** cada aba de resultado mostra o aviso "Resultado pré-gravado (demonstração)"

### Requirement: Demo restrita aos exemplos canônicos
No modo demonstração, o sistema SHALL exibir resultados pré-gravados apenas para exemplos canônicos não editados. Para texto digitado ou editado, SHALL informar que a demonstração não processa texto livre.

#### Scenario: Texto livre em modo demo
- **WHEN** o modo demo está ativo e o usuário digita um requisito de boleto
- **THEN** nenhum modelo é exibido
- **AND** a interface informa que é preciso desativar a demo para processar texto livre

#### Scenario: Exemplo canônico em modo demo
- **WHEN** o modo demo está ativo e o usuário carrega o exemplo de Login sem editar
- **THEN** o resultado pré-gravado do Login é exibido com o aviso

### Requirement: Artefatos de teste fora da demo
Enquanto a geração real de testes não existir, as abas de Gherkin e Pytest SHALL mostrar que a funcionalidade não está disponível e SHALL NOT oferecer download de arquivos que não executam.

#### Scenario: Aba Pytest no modo real
- **WHEN** o usuário abre a aba Pytest após uma geração real
- **THEN** a aba informa que a geração de testes ainda não está disponível
- **AND** não há botão de download
