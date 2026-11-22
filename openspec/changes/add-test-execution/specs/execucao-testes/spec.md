# Spec Delta

## MODIFIED Requirements

### Requirement: Seleção do sistema na interface
A interface MUST permitir escolher um sistema exemplo ou a opção sem sistema. Sem sistema, MUST informar que o resultado é um esqueleto e explicar como implementar o adaptador.

#### Scenario: Exemplo carregado
- **WHEN** a pessoa carrega um exemplo
- **THEN** o sistema correspondente fica selecionado

#### Scenario: Sem sistema
- **WHEN** a pessoa gera testes para um requisito de boleto, sem sistema selecionado
- **THEN** a aba de execução não oferece a execução, explica que não há sistema exemplo e aponta para o adaptador no pacote

### Requirement: Execução nas duas variantes
A execução MUST rodar a suíte contra a variante correta e contra cada mutante do sistema, cada uma em processo separado da interface, com tempo limite configurável.

#### Scenario: Executar testes
- **WHEN** a pessoa aciona a execução
- **THEN** os resultados da variante correta e de cada mutante são exibidos por cenário, com aprovados, falhas e motivo

#### Scenario: Execução sem resíduos
- **WHEN** a execução termina
- **THEN** nenhum arquivo gerado permanece no repositório

#### Scenario: Limite de tempo
- **WHEN** a execução de uma variante ultrapassa o tempo limite
- **THEN** ela é interrompida e o veredito é de erro de execução, indicando o tempo limite atingido

### Requirement: Veredito da execução
A interface MUST apresentar um veredito que usa a variante correta como referência da verdade e informa quantos mutantes a suíte detectou.

#### Scenario: Bug detectado
- **WHEN** todos os testes passam na variante correta e cada mutante tem ao menos um teste falhando
- **THEN** o veredito é "Bugs detectados (N de N)"

#### Scenario: Mutante sobrevivente
- **WHEN** todos os testes passam na variante correta e nenhum cenário falha contra o mutante "cupom expirado aceito"
- **THEN** o veredito é "Bugs detectados parcialmente (k de N)" e lista o mutante como sobrevivente, com o defeito e o critério de validade

#### Scenario: Bug não detectado
- **WHEN** todos os testes passam na variante correta e em todos os mutantes
- **THEN** o veredito é "Bug não detectado (0 de N)", indicando que os testes são insuficientes

#### Scenario: Modelo diverge do sistema
- **WHEN** algum teste falha na variante correta
- **THEN** o veredito é "Modelo diverge do sistema", com cada cenário que falhou listado como falso alarme e ligado aos critérios das suas tags, independentemente dos mutantes

#### Scenario: Erro de execução
- **WHEN** os testes não podem ser coletados ou executados em alguma variante
- **THEN** o veredito é "Erro de execução", com o motivo, e nenhuma taxa de detecção é exibida

## ADDED Requirements

### Requirement: Resultado por critério de aceite
O relatório MUST agregar os resultados por critério de aceite, usando as tags `@CA-<n>` dos cenários.

#### Scenario: Falha no critério 3
- **WHEN** dois cenários com `@CA-3` falham contra um mutante
- **THEN** o critério 3 aparece como violado nesse mutante, com os dois cenários listados

### Requirement: Execução por linha de comando
A execução e a análise de mutantes MUST estar disponíveis por linha de comando, a partir de um pacote gerado e de um id de sistema, produzindo o mesmo veredito da interface.

#### Scenario: Análise pela linha de comando
- **WHEN** o usuário executa a análise de mutantes do Saque ATM pela linha de comando
- **THEN** a saída mostra o veredito, a taxa de mutantes detectados e os sobreviventes

### Requirement: Comparação com suíte manual
Para Saque ATM, Cupom e MFA, o sistema MUST executar uma suíte escrita à mão contra os mesmos mutantes e mostrar, ao lado da gerada, o número de cenários, os cenários de borda, os mutantes detectados e o tempo de elaboração registrado.

#### Scenario: Relatório comparativo do MFA
- **WHEN** a comparação do MFA é executada
- **THEN** o relatório mostra as duas suítes com cenários, bordas, mutantes detectados e tempo de elaboração
