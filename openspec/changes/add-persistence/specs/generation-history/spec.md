# Spec Delta

## Purpose

Guardar projetos, requisitos, modelos de estados, suítes de teste e execuções em um banco relacional local, e permitir consultar e reabrir o histórico pela interface.

## ADDED Requirements

### Requirement: Criação e atualização idempotente do esquema
Um script de inicialização SHALL criar o banco e todas as tabelas quando não existirem, aplicar migrações pendentes quando o esquema estiver desatualizado e não alterar nada quando estiver atualizado, sem perda de dados.

#### Scenario: Banco novo
- **WHEN** o script roda sem arquivo de banco
- **THEN** o banco é criado com TB_PROJETO, TB_USER_STORY, TB_CRITERIO_ACEITE, TB_MODELO_ESTADOS, TB_SUITE_TESTE e TB_EXECUCAO

#### Scenario: Segunda execução
- **WHEN** o script roda duas vezes seguidas com dados no banco
- **THEN** a segunda execução termina sem erro e os dados continuam lá

### Requirement: Registro de cada geração
Cada geração SHALL ser gravada com projeto, história, critérios numerados, modelo de estados, diagrama, provedor, modelo do LLM, versão do prompt, tentativas, duração e situação (sucesso ou falha, com os erros).

#### Scenario: Geração com sucesso
- **WHEN** uma geração do Cupom termina com sucesso no projeto "Loja"
- **THEN** existem registros da história, dos critérios e do modelo ligados ao projeto "Loja"

#### Scenario: Geração com falha
- **WHEN** uma geração esgota as tentativas
- **THEN** ela é gravada com situação falha e os erros da última tentativa

### Requirement: Registro de suítes e execuções
Cada suíte gerada SHALL ser gravada com estratégia, cobertura, `.feature` e teste, ligada ao modelo de origem. Cada execução SHALL ser gravada com o sistema, o veredito, o resultado por variante e por cenário e a análise de mutantes.

#### Scenario: Execução gravada
- **WHEN** a suíte do Saque ATM é executada contra a variante correta e os mutantes
- **THEN** existe uma execução ligada à suíte com o veredito e o resultado de cada variante e de cada cenário

### Requirement: Projeto padrão e seleção de projeto
A interface SHALL permitir criar e selecionar projetos. Gerações sem projeto escolhido SHALL ser gravadas no projeto "Geral".

#### Scenario: Sem projeto escolhido
- **WHEN** o usuário gera sem escolher projeto
- **THEN** a geração fica no projeto "Geral"

### Requirement: Consulta e reabertura do histórico
A interface SHALL listar as gerações do projeto selecionado, da mais recente para a mais antiga, e SHALL reabrir uma geração mostrando os mesmos artefatos sem chamar o LLM.

#### Scenario: Reabrir geração antiga
- **WHEN** o usuário abre uma geração de ontem com o provedor desligado
- **THEN** o diagrama, o Gherkin e o teste gravados são exibidos

### Requirement: Exclusão de projeto em cascata
Excluir um projeto SHALL exigir confirmação e SHALL remover todas as histórias, critérios, modelos, suítes e execuções ligados a ele.

#### Scenario: Excluir projeto
- **WHEN** o usuário confirma a exclusão do projeto "Loja"
- **THEN** não resta nenhum registro ligado ao projeto "Loja"
