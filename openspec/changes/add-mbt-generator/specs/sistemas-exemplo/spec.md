# Spec Delta

## MODIFIED Requirements

### Requirement: Interface de execução uniforme
Cada variante de sistema exemplo MUST aceitar a definição de valores de contexto, o disparo de um evento do catálogo com dados de entrada opcionais, informando se o evento foi aceito, e expor o estado atual usando um id do catálogo.

#### Scenario: Evento aplicável
- **WHEN** um evento aplicável ao estado atual é disparado
- **THEN** o disparo informa que o evento foi aceito e o estado exposto muda de acordo com a regra de negócio do sistema

#### Scenario: Evento não aplicável
- **WHEN** um evento sem efeito no estado atual é disparado
- **THEN** o disparo informa que o evento foi recusado, o estado permanece o mesmo e nenhum erro é lançado

#### Scenario: Evento fora do catálogo
- **WHEN** um evento que não pertence ao catálogo é disparado
- **THEN** o sistema lança um erro que identifica o evento

#### Scenario: Contexto desconhecido
- **WHEN** é definido um valor de contexto para uma variável que não está no catálogo
- **THEN** o sistema lança um erro que identifica a variável
