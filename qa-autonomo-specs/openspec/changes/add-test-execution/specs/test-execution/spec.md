# Spec Delta

## Purpose

Executar as suítes geradas contra um sistema sob teste e transformar o resultado em evidência: falhas por critério, defeitos detectados e comparação com testes escritos à mão.

## ADDED Requirements

### Requirement: Execução isolada com tempo limite
O sistema SHALL executar a suíte em processo separado, contra o sistema escolhido, com tempo limite configurável, e SHALL relatar o estouro de tempo como resultado da execução, sem travar a interface.

#### Scenario: Suíte que não termina
- **WHEN** a execução passa de 60 s
- **THEN** ela é encerrada e o relatório indica tempo limite atingido

### Requirement: Resultado por cenário e por critério
O relatório SHALL listar cada cenário com resultado (passou, falhou, erro) e mensagem de falha, e SHALL agregar por critério de aceite usando as tags `@CA-<n>`.

#### Scenario: Falha no critério 3
- **WHEN** dois cenários com `@CA-3` falham
- **THEN** o critério 3 aparece como falhando, com os dois cenários listados

### Requirement: Análise de mutantes
O sistema SHALL executar a suíte contra todos os mutantes de um sistema de referência e informar a taxa de mutantes detectados e, para cada sobrevivente, o defeito e o critério que ele viola.

#### Scenario: Mutante sobrevivente
- **WHEN** nenhum cenário falha contra o mutante "cupom expirado aceito"
- **THEN** o relatório mostra o mutante como sobrevivente e cita o critério de validade

### Requirement: Falsos alarmes contra o sistema correto
Quando a suíte vier de um modelo extraído pelo LLM, o sistema SHALL executá-la também contra a implementação correta e reportar como falso alarme cada cenário que falhar ali.

#### Scenario: Modelo extraído errado
- **WHEN** o modelo extraído retém o cartão no primeiro PIN errado e a suíte roda no Saque correto
- **THEN** o cenário correspondente falha e é reportado como falso alarme ligado ao critério 3

### Requirement: Execução pela interface e por linha de comando
A interface SHALL ter uma aba de execução para os exemplos com sistema de referência, e a mesma execução SHALL estar disponível por linha de comando. Para histórias sem sistema de referência, a aba SHALL explicar como implementar o adaptador.

#### Scenario: História sem sistema de referência
- **WHEN** o usuário gera testes para um requisito de boleto
- **THEN** a aba de execução explica que não há sistema de referência e aponta para o adaptador no pacote

### Requirement: Comparação com suíte manual
Para cada exemplo canônico, o sistema SHALL executar uma suíte escrita à mão contra os mesmos mutantes e mostrar, lado a lado com a gerada, número de cenários, cenários de borda, mutantes detectados e tempo de elaboração registrado.

#### Scenario: Relatório comparativo do MFA
- **WHEN** a comparação do MFA é executada
- **THEN** o relatório mostra as duas suítes com cenários, bordas, mutantes detectados e tempo de elaboração
