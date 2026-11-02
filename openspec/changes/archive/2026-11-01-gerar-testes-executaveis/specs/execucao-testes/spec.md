# Spec Delta

## Purpose

Permite executar os testes gerados pela interface e apresenta um veredito que separa erro do modelo, bug do sistema e testes insuficientes.

## ADDED Requirements

### Requirement: Seleção do sistema na interface
A interface MUST permitir escolher um sistema exemplo ou a opção sem sistema, e informar quando o resultado será apenas um esqueleto.

#### Scenario: Exemplo carregado
- **WHEN** a pessoa carrega um exemplo
- **THEN** o sistema correspondente fica selecionado

#### Scenario: Sem sistema
- **WHEN** a pessoa gera artefatos sem sistema selecionado
- **THEN** a interface avisa que são esqueletos e não oferece a execução

### Requirement: Artefatos gerados no modo real e na demonstração
A interface MUST exibir e permitir baixar o Gherkin e o script gerados, nos dois modos, e nenhum artefato MUST vir de texto fixo.

#### Scenario: Modo real
- **WHEN** o backend devolve um modelo válido
- **THEN** as abas de Gherkin e Pytest mostram os artefatos gerados desse modelo

#### Scenario: Modo demonstração
- **WHEN** a pessoa gera um exemplo no modo demonstração
- **THEN** os artefatos são gerados do modelo de referência, sem backend e sem LLM

### Requirement: Demonstração não mascara requisito editado
O modo demonstração MUST avisar quando os requisitos na tela diferem dos requisitos do exemplo.

#### Scenario: Requisito editado
- **WHEN** a pessoa altera a user story ou os critérios e gera no modo demonstração
- **THEN** a interface avisa que o resultado corresponde ao exemplo, e não ao texto editado

### Requirement: Execução nas duas variantes
A execução MUST rodar os testes contra a variante correta e contra a variante com bug, em um processo separado da interface.

#### Scenario: Executar testes
- **WHEN** a pessoa aciona a execução
- **THEN** os resultados das duas variantes são exibidos por cenário, com aprovados, falhas e motivo

#### Scenario: Execução sem resíduos
- **WHEN** a execução termina
- **THEN** nenhum arquivo gerado permanece no repositório

#### Scenario: Limite de tempo
- **WHEN** a execução ultrapassa o tempo limite
- **THEN** ela é interrompida e o veredito é de erro de execução

### Requirement: Veredito da execução
A interface MUST apresentar um veredito derivado dos resultados das duas variantes, usando a variante correta como referência da verdade.

#### Scenario: Bug detectado
- **WHEN** todos os testes passam na variante correta e algum falha na variante com bug
- **THEN** o veredito é "Bug detectado"

#### Scenario: Modelo diverge do sistema
- **WHEN** algum teste falha na variante correta
- **THEN** o veredito é "Modelo diverge do sistema", com os cenários que falharam, independentemente da variante com bug

#### Scenario: Bug não detectado
- **WHEN** todos os testes passam nas duas variantes
- **THEN** o veredito é "Bug não detectado", indicando que os testes são insuficientes

#### Scenario: Erro de execução
- **WHEN** os testes não podem ser coletados ou executados em alguma variante
- **THEN** o veredito é "Erro de execução", com o motivo, e nenhum resultado de aprovação é exibido

### Requirement: Resultado vinculado aos artefatos
A interface MUST descartar o resultado da execução anterior quando novos artefatos forem gerados.

#### Scenario: Nova geração
- **WHEN** a pessoa gera novos artefatos após uma execução
- **THEN** o veredito anterior deixa de ser exibido
