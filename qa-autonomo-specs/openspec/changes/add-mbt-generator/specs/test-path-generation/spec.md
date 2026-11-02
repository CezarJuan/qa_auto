# Spec Delta

## Purpose

Calcular, de forma determinística, os caminhos de teste viáveis sobre o modelo de estados e medir a cobertura obtida, sem participação do LLM.

## ADDED Requirements

### Requirement: Caminhos viáveis do inicial ao final
Cada caminho SHALL começar no estado inicial, terminar em um estado final e ser viável: simulado com os valores de contexto e de entrada escolhidos, cada guarda do caminho é verdadeira no momento em que a transição ocorre.

#### Scenario: Caminho feliz do Saque
- **WHEN** os caminhos do gabarito do Saque são gerados
- **THEN** existe um caminho de `Inicio` até `SaqueRealizado` com valor menor ou igual ao saldo e múltiplo de 20

#### Scenario: Caminho com contador
- **WHEN** a transição para `CartaoRetido` exige `tentativas >= 2`
- **THEN** o caminho que a cobre tem três eventos `pin_invalido`

### Requirement: Estratégia de cobertura de todas as transições
Na estratégia padrão, o sistema SHALL gerar o menor conjunto de caminhos que encontrar no qual cada transição viável aparece em ao menos um caminho, preferindo caminhos mais curtos.

#### Scenario: Cobertura total
- **WHEN** a estratégia padrão é aplicada ao gabarito do Cupom
- **THEN** toda transição do modelo aparece em ao menos um caminho

### Requirement: Estratégia de caminhos elementares
Na estratégia de caminhos elementares, o sistema SHALL listar por busca em profundidade todos os caminhos sem repetir a mesma combinação de estado e variáveis, até o limite configurado de caminhos.

#### Scenario: Limite atingido
- **WHEN** existem mais caminhos que o limite de 200
- **THEN** são devolvidos 200 caminhos e o relatório avisa que o limite foi atingido

### Requirement: Cenários de borda
Para cada guarda que compara uma variável com um valor ou outra variável, o sistema SHALL gerar um cenário com o valor na fronteira e outro com o valor imediatamente fora dela. O cenário de fora MAY terminar com o evento recusado.

#### Scenario: Borda do saldo
- **WHEN** a guarda é `valor <= saldo` com saldo 100
- **THEN** há um cenário com valor 100 e outro com valor 120, o próximo múltiplo de 20 acima de 100

### Requirement: Relatório de cobertura
O sistema SHALL informar a porcentagem de estados, transições e critérios de aceite cobertos e listar cada elemento não coberto com o motivo.

#### Scenario: Transição inviável no limite de profundidade
- **WHEN** uma transição não é alcançada em até 30 passos
- **THEN** ela aparece como não coberta com o motivo "profundidade máxima atingida"

### Requirement: Determinismo
Para o mesmo modelo e a mesma configuração, o sistema SHALL produzir os mesmos caminhos, com os mesmos valores, na mesma ordem.

#### Scenario: Duas execuções
- **WHEN** os caminhos são gerados duas vezes para o mesmo modelo
- **THEN** as duas saídas são idênticas byte a byte

### Requirement: Rastreabilidade do caminho
Cada caminho SHALL informar a sequência de transições, os valores de contexto e de entrada usados e os critérios de aceite das transições percorridas.

#### Scenario: Critérios do caminho
- **WHEN** um caminho passa por transições dos critérios 1 e 3
- **THEN** o caminho informa os critérios 1 e 3
