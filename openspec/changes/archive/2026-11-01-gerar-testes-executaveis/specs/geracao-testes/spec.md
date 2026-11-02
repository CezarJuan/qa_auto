# Spec Delta

## Purpose

Deriva caminhos de teste de um modelo de estados válido e os transforma em artefatos Gherkin e Pytest executáveis, de forma determinística e sem uso do LLM.

## ADDED Requirements

### Requirement: Cobertura de todas as transições
A geração MUST produzir caminhos que partem do estado inicial e que, em conjunto, percorrem todas as transições do modelo.

#### Scenario: Todas cobertas
- **WHEN** caminhos são gerados de um modelo válido
- **THEN** cada transição aparece em ao menos um caminho

#### Scenario: Início do caminho
- **WHEN** um caminho é gerado
- **THEN** ele começa no estado inicial e cada passo parte do estado em que o passo anterior terminou

### Requirement: Geração determinística
A mesma entrada MUST produzir artefatos idênticos, sem chamadas ao LLM.

#### Scenario: Gerar duas vezes
- **WHEN** artefatos são gerados duas vezes para o mesmo modelo e sistema
- **THEN** os conteúdos são idênticos

#### Scenario: LLM indisponível
- **WHEN** os artefatos são gerados de um modelo existente sem LLM disponível
- **THEN** a geração conclui normalmente

### Requirement: Cenários Gherkin verificam cada passo
Cada caminho MUST virar um cenário que define o estado inicial, dispara os eventos em ordem e confere o estado esperado após cada evento.

#### Scenario: Conteúdo do cenário
- **WHEN** um caminho com dois eventos vira cenário
- **THEN** o cenário contém o estado inicial, dois disparos e duas conferências de estado

### Requirement: Rastreabilidade nos cenários
O nome de cada cenário MUST ser único e informar os números dos critérios de aceite percorridos pelo caminho.

#### Scenario: Caminho com critérios
- **WHEN** um caminho percorre transições dos critérios 2 e 3
- **THEN** o nome do cenário cita os critérios 2 e 3

#### Scenario: Caminho sem critérios
- **WHEN** um caminho percorre apenas transições sem critério
- **THEN** o nome do cenário indica que é um caminho auxiliar

### Requirement: Artefatos executáveis com sistema alvo
Com sistema alvo, a geração MUST produzir um `.feature` e um script `pytest-bdd` com nomes coerentes, cujos cenários têm todos os passos definidos e rodam contra o sistema.

#### Scenario: Par baixado executa
- **WHEN** os dois arquivos são salvos juntos com os nomes sugeridos e o comando indicado no script é executado
- **THEN** todos os cenários são coletados e executados, sem erro de arquivo ou de passo ausente

#### Scenario: Variante selecionável
- **WHEN** o script roda com a variante correta ou com bug selecionada por configuração de ambiente
- **THEN** os cenários executam contra a variante selecionada

#### Scenario: Divergência explicada
- **WHEN** o estado do sistema difere do esperado em um passo
- **THEN** o teste falha informando o estado esperado e o obtido

### Requirement: Esqueleto sem sistema alvo
Sem sistema alvo, a geração MUST produzir os mesmos artefatos em forma de esqueleto, cujos testes falham até que um sistema real seja conectado.

#### Scenario: Esqueleto não passa sozinho
- **WHEN** o esqueleto é executado sem adaptação
- **THEN** os cenários são coletados e falham com mensagem indicando que falta conectar o sistema

### Requirement: Texto do modelo tratado como dado
Texto vindo do modelo ou dos requisitos MUST NOT virar código no script gerado nem alterar a estrutura do arquivo Gherkin.

#### Scenario: Evento malicioso
- **WHEN** um evento sem catálogo contém aspas, quebras de linha ou trechos de código
- **THEN** o `.feature` continua com a mesma estrutura de cenários e o script não contém esse texto
